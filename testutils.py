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
    return exit_code

def run_test(testname, params):
    try:
        exek = params['exec']
        post = params['post']
    except:
        return JSON_STRUCTURE_NOT_MATCH

    exit_code = execute_vm(exek['code'][2:])
    if exit_code != 0: return exit_code

    for address in post:
        try:
            storage_data = {}
            storage = post[address]['storage']
            if not storage: raise
            for storage_key in storage:
                storage_value = storage[storage_key]
                storage_key = storage_key.encode('utf-8')
                storage_value = storage_value.encode('utf-8')
                storage_key = decode_hex(storage_key)
                storage_value = decode_hex(storage_value)
                storage_data[storage_key] = storage_value
        except:
            print "Storage is much likely to be empty in json test file"
            return STORAGE_EMPTY

    result = PASS
    with open('result', 'r') as result_file:
        for line in result_file:
            key, value = line.split(' ')
            key, value = long(key), long(value)

            try:
                if value != storage_data[key]:
                    result = FAIL
                    print "Storage is", key, value
                    print "Storage should be: ", storage_key, storage_value
            except:
                print key, value
                print storage_data
                result = FAIL
    return result
