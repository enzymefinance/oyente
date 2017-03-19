import os
from global_test_params import *
from global_params import *

def decode_hex(code):
    return long(code, 0)

def execute_vm(bytecode_content):
    with open('code', 'w') as code_file:
        code_file.write(bytecode_content)
        code_file.write('\n')
        code_file.close()
    cmd = os.system('python oyente.py -b code')
    exit_code = os.WEXITSTATUS(cmd)
    if exit_code == 1: return False
    return True

def run_test(testname, params):
    try:
        exek = params['exec']
        post = params['post']
    except:
        return JSON_STRUCTURE_NOT_MATCH

    if execute_vm(exek['code'][2:]) == False: return NOT_YET_HANDLED_OPCODE

    for address in post:
        try:
            storage = post[address]['storage']
            storage_key = storage.keys()[0].encode('utf-8')
            storage_value = storage[storage_key].encode('utf-8')
            storage_key = decode_hex(storage_key)
            storage_value = decode_hex(storage_value)
        except:
            print "Storage is much likely to be empty in json test file"
            print "Storage", post
            return STORAGE_EMPTY

    with open('result', 'r') as result_file:
        key = result_file.readline()
        value = result_file.readline()

        key, value = long(key), long(value)

        if key == storage_key and value == storage_value: return PASS
        else:
            print "Storage is", key, value
            print "Storage should be: ", storage_key, storage_value
        result_file.close()
        return FAIL
