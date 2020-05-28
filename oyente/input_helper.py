import shlex
import subprocess
import os
import re
import logging
import json
import global_params
import six
from source_map import SourceMap
from utils import run_command, run_command_with_err

class InputHelper:
    BYTECODE = 0
    SOLIDITY = 1
    STANDARD_JSON = 2
    STANDARD_JSON_OUTPUT = 3

    def __init__(self, input_type, **kwargs):
        self.input_type = input_type

        if input_type == InputHelper.BYTECODE:
            attr_defaults = {
                'source': None,
                'evm': False,
            }
        elif input_type == InputHelper.SOLIDITY:
            attr_defaults = {
                'source': None,
                'evm': False,
                'root_path': "",
                'compiled_contracts': [],
                'compilation_err': False,
                'remap': "",
                'allow_paths': ""
            }
        elif input_type == InputHelper.STANDARD_JSON:
            attr_defaults = {
                'source': None,
                'evm': False,
                'root_path': "",
                'allow_paths': None,
                'compiled_contracts': []
            }
        elif input_type == InputHelper.STANDARD_JSON_OUTPUT:
            attr_defaults = {
                'source': None,
                'evm': False,
                'root_path': "",
                'compiled_contracts': [],
            }

        for (attr, default) in six.iteritems(attr_defaults):
            val = kwargs.get(attr, default)
            if val == None:
                raise Exception("'%s' attribute can't be None" % attr)
            else:
                setattr(self, attr, val)

    def get_inputs(self, targetContracts=None):
        inputs = []
        if self.input_type == InputHelper.BYTECODE:
            with open(self.source, 'r') as f:
                bytecode = f.read()
            self._prepare_disasm_file(self.source, bytecode)

            disasm_file = self._get_temporary_files(self.source)['disasm']
            inputs.append({'disasm_file': disasm_file})
        else:
            contracts = self._get_compiled_contracts()
            self._prepare_disasm_files_for_analysis(contracts)
            for contract, _ in contracts:
                c_source, cname = contract.split(':')
                if targetContracts is not None and cname not in targetContracts:
                    continue
                c_source = re.sub(self.root_path, "", c_source)
                if self.input_type == InputHelper.SOLIDITY:
                    source_map = SourceMap(contract, self.source, 'solidity', self.root_path, self.remap, self.allow_paths)
                else:
                    source_map = SourceMap(contract, self.source, 'standard json', self.root_path)
                disasm_file = self._get_temporary_files(contract)['disasm']
                inputs.append({
                    'contract': contract,
                    'source_map': source_map,
                    'source': self.source,
                    'c_source': c_source,
                    'c_name': cname,
                    'disasm_file': disasm_file
                })
        if targetContracts is not None and not inputs:
            raise ValueError("Targeted contract wasn't found in the input! No contract was processed!")
        return inputs

    def rm_tmp_files(self):
        if self.input_type == InputHelper.BYTECODE:
            self._rm_tmp_files(self.source)
        else:
            self._rm_tmp_files_of_multiple_contracts(self.compiled_contracts)

    def _get_compiled_contracts(self):
        if not self.compiled_contracts:
            if self.input_type == InputHelper.SOLIDITY:
                self.compiled_contracts = self._compile_solidity()
            elif self.input_type == InputHelper.STANDARD_JSON:
                self.compiled_contracts = self._compile_standard_json()
            elif self.input_type == InputHelper.STANDARD_JSON_OUTPUT:
                self.compiled_contracts = self._compile_standard_json_output(self.source)

        return self.compiled_contracts

    def _compile_solidity(self):
        if not self.allow_paths:
            cmd = "solc --bin-runtime %s %s" % (self.remap, self.source)
        else:
            cmd = "solc --bin-runtime %s %s --allow-paths %s" % (self.remap, self.source, self.allow_paths)
        err = ''
        if self.compilation_err:
            out, err = run_command_with_err(cmd)
            err = re.sub(self.root_path, "", err)
        else:
            out = run_command(cmd)

        libs = re.findall(r"_+(.*?)_+", out)
        libs = set(libs)
        if libs:
            return self._link_libraries(self.source, libs)
        else:
            return self._extract_bin_str(out, err)

    def _compile_standard_json(self):
        FNULL = open(os.devnull, 'w')
        cmd = "cat %s" % self.source
        p1 = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=FNULL)
        cmd = "solc --allow-paths %s --standard-json" % self.allow_paths
        p2 = subprocess.Popen(shlex.split(cmd), stdin=p1.stdout, stdout=subprocess.PIPE, stderr=FNULL)
        p1.stdout.close()
        out = p2.communicate()[0]
        with open('standard_json_output', 'w') as of:
            of.write(out)

        return self._compile_standard_json_output('standard_json_output')

    def _compile_standard_json_output(self, json_output_file):
        with open(json_output_file, 'r') as f:
            out = f.read()
        j = json.loads(out)
        contracts = []
        for source in j['sources']:
            for contract in j['contracts'][source]:
                cname = source + ":" + contract
                evm = j['contracts'][source][contract]['evm']['deployedBytecode']['object']
                contracts.append((cname, evm))
        return contracts

    def _removeSwarmHash(self, evm):
        evm_without_hash = re.sub(r"a165627a7a72305820\S{64}0029$", "", evm)
        return evm_without_hash

    def _extract_bin_str(self, s, err=''):
        binary_regex = r"\n======= (.*?) =======\nBinary of the runtime part: \n(.*?)\n"
        contracts = re.findall(binary_regex, s)
        contracts = [contract for contract in contracts if contract[1]]
        if not contracts:
            if not self.compilation_err:
                logging.critical("Solidity compilation failed. Please use -ce flag to see the detail.")
                if global_params.WEB:
                    six.print_({"error": "Solidity compilation failed."})
            else:
                logging.critical("solc output:\n" + s)
                logging.critical(err)
                logging.critical("Solidity compilation failed.")
                if global_params.WEB:
                    six.print_({"error": err})

            exit(1)
        return contracts

    def _link_libraries(self, filename, libs):
        option = ""
        for idx, lib in enumerate(libs):
            lib_address = "0x" + hex(idx+1)[2:].zfill(40)
            option += " --libraries %s:%s" % (lib, lib_address)
        FNULL = open(os.devnull, 'w')
        if not self.allow_paths:
            cmd = "solc --bin-runtime %s %s" % (self.remap, self.source)
        else:
            cmd = "solc --bin-runtime %s %s --allow-paths %s" % (self.remap, self.source, self.allow_paths)
        p1 = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=FNULL)
        cmd = "solc --link%s" %option
        p2 = subprocess.Popen(shlex.split(cmd), stdin=p1.stdout, stdout=subprocess.PIPE, stderr=FNULL)
        p1.stdout.close()
        out = p2.communicate()[0].decode('utf-8', 'strict')
        return self._extract_bin_str(out)

    def _prepare_disasm_files_for_analysis(self, contracts):
        for contract, bytecode in contracts:
            self._prepare_disasm_file(contract, bytecode)

    def _prepare_disasm_file(self, target, bytecode):
        self._write_evm_file(target, bytecode)
        self._write_disasm_file(target)

    def _get_temporary_files(self, target):
        return {
            "evm": target + ".evm",
            "disasm": target + ".evm.disasm",
            "log": target + ".evm.disasm.log"
        }

    def _write_evm_file(self, target, bytecode):
        evm_file = self._get_temporary_files(target)["evm"]
        with open(evm_file, 'w') as of:
            of.write(self._removeSwarmHash(bytecode))

    def _write_disasm_file(self, target):
        tmp_files = self._get_temporary_files(target)
        evm_file = tmp_files["evm"]
        disasm_file = tmp_files["disasm"]
        disasm_out = ""
        try:
            disasm_p = subprocess.Popen(
                ["evm", "disasm", evm_file], stdout=subprocess.PIPE)
            disasm_out = disasm_p.communicate()[0].decode('utf-8', 'strict')
        except:
            logging.critical("Disassembly failed.")
            exit()

        with open(disasm_file, 'w') as of:
            of.write(disasm_out)

    def _rm_tmp_files_of_multiple_contracts(self, contracts):
        if self.input_type in ['standard_json', 'standard_json_output']:
            self._rm_file('standard_json_output')
        for contract, _ in contracts:
            self._rm_tmp_files(contract)

    def _rm_tmp_files(self, target):
        tmp_files = self._get_temporary_files(target)
        if not self.evm:
            self._rm_file(tmp_files["evm"])
            self._rm_file(tmp_files["disasm"])
        self._rm_file(tmp_files["log"])

    def _rm_file(self, path):
        if os.path.isfile(path):
            os.unlink(path)

