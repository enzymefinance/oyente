#!/usr/bin/env python

import shlex
import subprocess
import os
import re
import argparse
import logging
import requests
import json
import global_params
import six
from source_map import SourceMap
from utils import run_command
from symExec import analyze

def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0


def has_dependencies_installed():
    try:
        import z3
        import z3.z3util
        if z3.get_version_string() != '4.5.0':
            logging.warning("You are using an untested version of z3. 4.5.0 is the officially tested version")
    except:
        logging.critical("Z3 is not available. Please install z3 from https://github.com/Z3Prover/z3.")
        return False

    if not cmd_exists("evm"):
        logging.critical("Please install evm from go-ethereum and make sure it is in the path.")
        return False
    else:
        cmd = "evm --version"
        out = run_command(cmd).strip()
        version = re.findall(r"evm version (\d*.\d*.\d*)", out)[0]
        if version != '1.6.6':
            logging.warning("You are using evm version %s. The supported version is 1.6.6" % version)

    if not cmd_exists("solc"):
        logging.critical("solc is missing. Please install the solidity compiler and make sure solc is in the path.")
        return False
    else:
        cmd = "solc --version"
        out = run_command(cmd).strip()
        version = re.findall(r"Version: (\d*.\d*.\d*)", out)[0]
        if version != '0.4.17':
            logging.warning("You are using solc version %s, The latest supported version is 0.4.17" % version)

    return True


def removeSwarmHash(evm):
    evm_without_hash = re.sub(r"a165627a7a72305820\S{64}0029$", "", evm)
    return evm_without_hash

def extract_bin_str(s):
    binary_regex = r"\n======= (.*?) =======\nBinary of the runtime part: \n(.*?)\n"
    contracts = re.findall(binary_regex, s)
    contracts = [contract for contract in contracts if contract[1]]
    if not contracts:
        logging.critical("Solidity compilation failed")
        if global_params.WEB:
            six.print_({"error": "Solidity compilation failed"})
        exit()
    return contracts

def link_libraries(filename, libs):
    option = ""
    for idx, lib in enumerate(libs):
        lib_address = "0x" + hex(idx+1)[2:].zfill(40)
        option += " --libraries %s:%s" % (lib, lib_address)
    FNULL = open(os.devnull, 'w')
    cmd = "solc --bin-runtime %s" % filename
    p1 = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=FNULL)
    cmd = "solc --link%s" %option
    p2 = subprocess.Popen(shlex.split(cmd), stdin=p1.stdout, stdout=subprocess.PIPE, stderr=FNULL)
    p1.stdout.close()
    out = p2.communicate()[0].decode()
    return extract_bin_str(out)

def compile_contracts():
    cmd = "solc --bin-runtime %s" % args.source
    out = run_command(cmd)

    libs = re.findall(r"_+(.*?)_+", out)
    libs = set(libs)
    if libs:
        return link_libraries(args.source, libs)
    else:
        return extract_bin_str(out)

def compile_standard_json():
    global args

    FNULL = open(os.devnull, 'w')
    cmd = "cat %s" % args.source
    p1 = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=FNULL)
    cmd = "solc --allow-paths %s --standard-json" % args.allow_paths
    p2 = subprocess.Popen(shlex.split(cmd), stdin=p1.stdout, stdout=subprocess.PIPE, stderr=FNULL)
    p1.stdout.close()
    out = p2.communicate()[0]
    with open('standard_json_output', 'w') as of:
        of.write(out)
    # should handle the case without allow-paths option
    j = json.loads(out)
    contracts = []
    for source in j["sources"]:
        for contract in j["contracts"][source]:
            cname = source + ":" + contract
            evm = j["contracts"][source][contract]["evm"]["deployedBytecode"]["object"]
            contracts.append((cname, evm))
    return contracts

def prepare_disasm_files_for_analysis(contracts):
    for contract, bin_str in contracts:
        write_evm_file(contract, bin_str)
        write_disasm_file(contract)

def get_temporary_files(contract):
    return {
        "evm": contract + ".evm",
        "disasm": contract + ".evm.disasm",
        "log": contract + ".evm.disasm.log"
    }

def write_evm_file(contract, bin_str):
    evm_file = get_temporary_files(contract)["evm"]
    with open(evm_file, 'w') as of:
        of.write(removeSwarmHash(bin_str))

def write_disasm_file(contract):
    tmp_files = get_temporary_files(contract)
    evm_file = tmp_files["evm"]
    disasm_file = tmp_files["disasm"]
    disasm_out = ""
    try:
        disasm_p = subprocess.Popen(
            ["evm", "disasm", evm_file], stdout=subprocess.PIPE)
        disasm_out = disasm_p.communicate()[0].decode()
    except:
        logging.critical("Disassembly failed.")
        exit()

    with open(disasm_file, 'w') as of:
        of.write(disasm_out)

def remove_temporary_files_of_contracts(contracts):
    global args

    if args.standard_json:
        remove_temporary_file('standard_json_output')
    for contract, _ in contracts:
        remove_temporary_files(contract)

def remove_temporary_files(contract):
    global args

    tmp_files = get_temporary_files(contract)
    if not args.evm:
        remove_temporary_file(tmp_files["evm"])
    remove_temporary_file(tmp_files["disasm"])
    remove_temporary_file(tmp_files["log"])

def remove_temporary_file(path):
    if os.path.isfile(path):
        os.unlink(path)


def run_standard_json_analysis(contracts):
    global args
    results = {}
    exit_code = 0

    for contract, _ in contracts:
        source, cname = contract.split(":")
        source = re.sub(args.root_path, "", source)
        logging.info("Contract %s:", contract)
        source_map = SourceMap(contract, args.source, "standard json")
        disasm_file = get_temporary_files(contract)["disasm"]

        result, return_code = analyze(disasm_file=disasm_file, source_map=source_map, source_file=args.source)

        try:
            results[source][cname] = result
        except:
            results[source] = {cname: result}

        if return_code == 1:
            exit_code = 1
    return results, exit_code

def run_source_codes_analysis(contracts):
    global args
    results = {}
    exit_code = 0

    for contract, _ in contracts:
        source, cname = contract.split(":")
        source = re.sub(args.root_path, "", source)
        logging.info("Contract %s:", contract)
        source_map = SourceMap(contract, args.source, "solidity", args.root_path)
        disasm_file = get_temporary_files(contract)["disasm"]

        result, return_code = analyze(disasm_file=disasm_file, source_map=source_map, source_file=args.source)

        try:
            results[source][cname] = result
        except:
            results[source] = {cname: result}

        if return_code == 1:
            exit_code = 1
    return results, exit_code

def analyze_bytecode():
    global args
    contract = args.source
    with open(contract, "r") as f:
        bin_str = f.read()
    write_evm_file(contract, bin_str)
    write_disasm_file(contract)
    disasm_file = get_temporary_files(contract)["disasm"]

    result, exit_code = analyze(disasm_file=disasm_file, source_file=None, source_map=None)

    if global_params.WEB:
        six.print_(json.dumps(result))

    remove_temporary_files(contract)

    if global_params.UNIT_TEST == 2 or global_params.UNIT_TEST == 3:
        exit_code = os.WEXITSTATUS(cmd)
        if exit_code != 0:
            exit(exit_code)
    return exit_code

def analyze_standard_json():
    contracts = compile_standard_json()

    prepare_disasm_files_for_analysis(contracts)
    results, exit_code = run_standard_json_analysis(contracts)
    remove_temporary_files_of_contracts(contracts)
    return exit_code

def analyze_source_codes():
    contracts = compile_contracts()

    prepare_disasm_files_for_analysis(contracts)
    results, exit_code = run_source_codes_analysis(contracts)
    remove_temporary_files_of_contracts(contracts)

    if global_params.WEB:
        six.print_(json.dumps(results))
    return exit_code

def main():
    # TODO: Implement -o switch.

    global args

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-s",  "--source",    type=str, help="local source file name. Solidity by default. Use -b to process evm instead. Use stdin to read from stdin.")
    group.add_argument("-ru", "--remoteURL", type=str, help="Get contract from remote URL. Solidity by default. Use -b to process evm instead.", dest="remote_URL")

    parser.add_argument("--version", action="version", version="oyente version 0.2.7 - Commonwealth")

    parser.add_argument("-t",   "--timeout",        help="Timeout for Z3 in ms.", action="store", type=int)
    parser.add_argument("-gl",  "--gaslimit",       help="Limit Gas", action="store", dest="gas_limit", type=int)
    parser.add_argument("-rp",   "--root-path",      help="Root directory path used for the online version", action="store", dest="root_path", type=str)
    parser.add_argument("-ll",  "--looplimit",      help="Limit number of loops", action="store", dest="loop_limit", type=int)
    parser.add_argument("-dl",  "--depthlimit",     help="Limit DFS depth", action="store", dest="depth_limit", type=int)
    parser.add_argument("-ap",  "--allow-paths",    help="Allow a given path for imports", action="store", dest="allow_paths", type=str)
    parser.add_argument("-glt", "--global-timeout", help="Timeout for symbolic execution", action="store", dest="global_timeout", type=int)

    parser.add_argument( "-e",   "--evm",                 help="Do not remove the .evm file.", action="store_true")
    parser.add_argument( "-w",   "--web",                 help="Run Oyente for web service", action="store_true")
    parser.add_argument( "-j",   "--json",                help="Redirect results to a json file.", action="store_true")
    parser.add_argument( "-err", "--error",               help="Enable exceptions and print output. Monsters here.", action="store_true")
    parser.add_argument( "-p",   "--paths",               help="Print path condition information.", action="store_true")
    parser.add_argument( "-db",  "--debug",               help="Display debug information", action="store_true")
    parser.add_argument( "-st",  "--state",               help="Get input state from state.json", action="store_true")
    parser.add_argument( "-r",   "--report",              help="Create .report file.", action="store_true")
    parser.add_argument( "-v",   "--verbose",             help="Verbose output, print everything.", action="store_true")
    parser.add_argument( "-b",   "--bytecode",            help="read bytecode in source instead of solidity file.", action="store_true")
    parser.add_argument( "-a",   "--assertion",           help="Check assertion failures.", action="store_true")
    parser.add_argument( "-sj",  "--standard-json",       help="Support Standard JSON input", action="store_true")
    parser.add_argument( "-gb",  "--globalblockchain",    help="Integrate with the global ethereum blockchain", action="store_true")
    parser.add_argument( "-gtc", "--generate-test-cases", help="Generate test cases each branch of symbolic execution tree", action="store_true")

    args = parser.parse_args()

    if args.root_path:
        if args.root_path[-1] != '/':
            args.root_path += '/'
    else:
        args.root_path = ""

    if args.timeout:
        global_params.TIMEOUT = args.timeout

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    global_params.PRINT_PATHS = 1 if args.paths else 0
    global_params.REPORT_MODE = 1 if args.report else 0
    global_params.IGNORE_EXCEPTIONS = 1 if args.error else 0
    global_params.USE_GLOBAL_BLOCKCHAIN = 1 if args.globalblockchain else 0
    global_params.INPUT_STATE = 1 if args.state else 0
    global_params.WEB = 1 if args.web else 0
    global_params.STORE_RESULT = 1 if args.json else 0
    global_params.CHECK_ASSERTIONS = 1 if args.assertion else 0
    global_params.DEBUG_MODE = 1 if args.debug else 0
    global_params.GENERATE_TEST_CASES = 1 if args.generate_test_cases else 0

    if args.depth_limit:
        global_params.DEPTH_LIMIT = args.depth_limit
    if args.gas_limit:
        global_params.GAS_LIMIT = args.gas_limit
    if args.loop_limit:
        global_params.LOOP_LIMIT = args.loop_limit
    if global_params.WEB:
        if args.global_timeout and args.global_timeout < global_params.GLOBAL_TIMEOUT:
            global_params.GLOBAL_TIMEOUT = args.global_timeout
    else:
        if args.global_timeout:
            global_params.GLOBAL_TIMEOUT = args.global_timeout

    if not has_dependencies_installed():
        return

    if args.remote_URL:
        r = requests.get(args.remote_URL)
        code = r.text
        filename = "remote_contract.evm" if args.bytecode else "remote_contract.sol"
        args.source = filename
        with open(filename, 'w') as f:
            f.write(code)

    exit_code = 0
    if args.bytecode:
        exit_code = analyze_bytecode()
    elif args.standard_json:
        exit_code = analyze_standard_json()
    else:
        exit_code = analyze_source_codes()

    exit(exit_code)

if __name__ == '__main__':
    main()
