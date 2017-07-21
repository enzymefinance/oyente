import os
from z3 import *
from global_test_params import *
from global_params import *
from utils import to_unsigned

class EvmUnitTest(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data

    def bytecode(self):
        return self.data['exec']['code'][2:]

    def storage(self):
        storage = self.data['post'].values()[0]['storage']
        return storage if storage != None else {"0": "0"}

    def mem(self):
        memory = self.data['out']
        if memory == "0x":
            return memory + "00"
        else:
            return memory

    def gas_info(self):
        gas_limit = long(self.data['exec']['gas'], 0)
        gas_remaining = long(self.data['gas'], 0)
        return (gas_limit, gas_remaining)


    def run_test(self):
        return self._execute_vm(self.bytecode())

    def _execute_vm(self, bytecode):
        self._create_bytecode_file(bytecode)
        cmd = os.system('python oyente.py -b -s bytecode')
        exit_code = os.WEXITSTATUS(cmd)
        return exit_code

    def _create_bytecode_file(self, bytecode):
        with open('bytecode', 'w') as code_file:
            code_file.write(bytecode)
            code_file.write('\n')
            code_file.close()

    def compare_with_symExec_result(self, global_state, mem, analysis):
        if UNIT_TEST == 2: return self.compare_real_value(global_state, mem, analysis)
        if UNIT_TEST == 3: return self.compare_symbolic(global_state)

    def compare_real_value(self, global_state, mem, analysis):
        storage_status = self._compare_storage_value(global_state)
        mem_status = self._compare_memory_value(mem)
        gas_status = self._compare_gas_value(analysis)
        if storage_status != PASS: return storage_status
        if mem_status != PASS: return mem_status
        if gas_status != PASS: return gas_status
        return PASS

    def _compare_storage_value(self, global_state):
        for key, value in self.storage().items():
            key, value = long(key, 0), long(value, 0)

            try:
                storage = to_unsigned(long(global_state['Ia'][key]))
            except:
                return EMPTY_RESULT

            if storage != value:
                return FAIL
        return PASS

    def _compare_memory_value(self, mem):
        memory = 0 if not mem else mem.values()[0]
        memory = to_unsigned(long(memory))

        if memory != long(self.mem(), 0):
            return FAIL
        return PASS

    def _compare_gas_value(self, analysis):
        gas_used = analysis['gas']
        gas_limit, gas_remaining = self.gas_info()
        if gas_used == gas_limit - gas_remaining:
            return PASS
        else:
            return INCORRECT_GAS


    def compare_symbolic(self, global_state):
        for key, value in self.storage().items():
            key, value = long(key, 0), long(value, 0)
            try:
                symExec_result = global_state['Ia'][str(key)]
            except:
                return EMPTY_RESULT

            s = Solver()
            s.add(symExec_result == BitVecVal(value, 256))
            if s.check() == unsat: # Unsatisfy
                return FAIL
        return PASS

    def is_exception_case(self): # no post, gas field in data
        try:
            post = self.data['post']
            gas = self.data['gas']
            return False
        except:
            return True
