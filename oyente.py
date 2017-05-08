import shlex
import subprocess
import os
import re
import sys
import global_params
import argparse

def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def has_dependencies_installed():
    try:
        import z3
        import z3util
    except:
        print "Error: Z3 is not available. Please install z3 from https://github.com/Z3Prover/z3."
        return False

    if not cmd_exists("disasm"):
        print "disasm is missing. Please install go-ethereum and make sure disasm is in the path."
        return False

    if not cmd_exists("solc"):
        print "solc is missing. Please install the solidity compiler and make sure solc is in the path."
        return False

    return True

def main():
    # TODO: Implement -o switch.

    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=str, help="Solidity file name by default, bytecode if -e is enabled. Use stdin to read from stdin.")
    parser.add_argument("-b", "--bytecode", help="read bytecode in source instead of solidity file.", action="store_true")
    parser.add_argument("-j", "--json", help="Redirect results to a json file.", action="store_true")
    parser.add_argument("-e", "--evm", help="Do not remove the .evm file.", action="store_true")
    parser.add_argument("-p", "--paths", help="Print path condition information.", action="store_true")
    parser.add_argument("--error", help="Enable exceptions and print output. Monsters here.", action="store_true")
    parser.add_argument("-t", "--timeout", type=int, help="Timeout for Z3.")
    parser.add_argument("-d", "--debug", help="Enable debug .log file.", action="store_true")
    parser.add_argument("-v", "--verbose", help="Verbose output, print everything.", action="store_true")
    parser.add_argument("-r", "--report", help="Create .report file.", action="store_true")
    parser.add_argument("-gb", "--globalblockchain", help="Integrate with the global ethereum blockchain", action="store_true")
    parser.add_argument("-dl", "--depthlimit", help="Limit DFS depth", action="store", dest="depth_limit", type=int)
    parser.add_argument("--erc20", help="ERC20 Contract", action="store_true")

    args = parser.parse_args()

    if args.timeout:
        global_params.TIMEOUT = args.timeout

    global_params.PRINT_PATHS = 1 if args.paths else 0
    global_params.PRINT_MODE = 1 if args.verbose else 0
    global_params.REPORT_MODE = 1 if args.report else 0
    global_params.DEBUG_MODE = 1 if args.debug else 0
    global_params.IGNORE_EXCEPTIONS = 1 if args.error else 0
    global_params.USE_GLOBAL_BLOCKCHAIN = 1 if args.globalblockchain else 0
    global_params.ERC20 = 1 if args.erc20 else 0

    if args.depth_limit:
        global_params.DEPTH_LIMIT = args.depth_limit

    if not has_dependencies_installed():
        return

    if args.bytecode:
        disasm_out = ""
        try:
            disasm_p = subprocess.Popen(shlex.split('disasm'), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            disasm_out = disasm_p.communicate(input=open(args.source).read())[0]
        except:
            print "Disassembly failed."

        # Run symExec

        with open(args.source+'.disasm', 'w') as of:
            of.write(disasm_out)


        # TODO: Do this as an import and run, instead of shell call and hacky fix
        
        cmd = os.system('python symExec.py %s.disasm %d %d %d %d %d %d %d %d %d %d %d %d %d %s' % (args.source, global_params.IGNORE_EXCEPTIONS, global_params.REPORT_MODE, global_params.PRINT_MODE, global_params.DATA_FLOW, global_params.DEBUG_MODE, global_params.CHECK_CONCURRENCY_FP, global_params.TIMEOUT, global_params.UNIT_TEST, global_params.GLOBAL_TIMEOUT, global_params.PRINT_PATHS, global_params.USE_GLOBAL_BLOCKCHAIN, global_params.DEPTH_LIMIT, global_params.ERC20, args.source+".json" if args.json else ""))

        os.system('rm %s.disasm' % (args.source))

        if global_params.UNIT_TEST == 2 or global_params.UNIT_TEST == 3:
            exit_code = os.WEXITSTATUS(cmd)
            if exit_code != 0: exit(exit_code)
        return

    # Compile first

    solc_cmd = "solc --optimize --bin-runtime %s"

    FNULL = open(os.devnull, 'w')

    solc_p = subprocess.Popen(shlex.split(solc_cmd % args.source), stdout = subprocess.PIPE, stderr=FNULL)
    solc_out = solc_p.communicate()

    binary_regex = r"\n======= (.*?) =======\nBinary of the runtime part: \n(.*?)\n"
    matches = re.findall(binary_regex, solc_out[0])

    if len(matches) == 0:
        print "Solidity compilation failed"
        exit()

    for (cname, bin_str) in matches:
        print "Contract %s:" % cname
        bin_str += "\0"

        disasm_out = ""
        try:
            disasm_p = subprocess.Popen(shlex.split('disasm'), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            disasm_out = disasm_p.communicate(input=bin_str)[0]

        except:
            print "Disassembly failed."

        # Run symExec

        with open(cname+'.evm.disasm', 'w') as of:
            of.write(disasm_out)

        with open(cname+'.evm', 'w') as of:
            of.write(bin_str)


        # TODO: Do this as an import and run, instead of shell call and hacky fix

        os.system('python symExec.py %s.evm.disasm %d %d %d %d %d %d %d %d %d %d %d %d %d %s' % (cname, global_params.IGNORE_EXCEPTIONS, global_params.REPORT_MODE, global_params.PRINT_MODE, global_params.DATA_FLOW, global_params.DEBUG_MODE, global_params.CHECK_CONCURRENCY_FP, global_params.TIMEOUT, global_params.UNIT_TEST, global_params.GLOBAL_TIMEOUT, global_params.PRINT_PATHS, global_params.USE_GLOBAL_BLOCKCHAIN, global_params.DEPTH_LIMIT, global_params.ERC20, cname+".json" if args.json else ""))

        if args.evm:
            with open(cname+'.evm','w') as of:
                of.write(bin_str)

        os.system('rm %s.evm.disasm' % (cname))

if __name__ == '__main__':
    main()
