import os
from global_test_params import *
from global_params import *
from arithmetic_utils import *

def decode_hex(code):
    try:
        return long(code, 0)
    except ValueError as e:
        return None

def execute_vm(bytecode_content):
    with open('code', 'w') as code_file:
        code_file.write(bytecode_content)
        code_file.write('\n')
        code_file.close()
    cmd = os.system('python oyente.py -b code')
    exit_code = os.WEXITSTATUS(cmd)
    return exit_code

def compare_storage(params, exit_code):
    if exit_code == EXCEPTION and 'post' not in params: return PASS

    if exit_code != 0: return exit_code

    try:
        post = params['post']
        address = post.keys()[0]
    except:
        return JSON_STRUCTURE_NOT_MATCH

    if os.stat('storage').st_size <= 0:
        if post[address]['storage']: return EMPTY_RESULT
        else: return PASS

    for address in post:
        storage = post[address]['storage']
        storage_data = {}
        for storage_key in storage:
            storage_value = storage[storage_key]
            storage_key = storage_key.encode('utf-8')
            storage_value = storage_value.encode('utf-8')
            storage_key = decode_hex(storage_key)
            storage_value = decode_hex(storage_value)
            storage_data[storage_key] = storage_value

    result = FAIL
    with open('storage', 'r') as f:
        for line in f:
            key, value = line.split(' ')
            key, value = to_unsigned(long(key)), to_unsigned(long(value))

            if value == 0 and key not in storage_data: result = PASS
            else:
                try:
                    if value == storage_data[key]: result = PASS
                    else:
                        result = FAIL
                        print "Storage is: ", key, value
                        print "Storage should be: ", key, storage_data[key]
                except:
                    print "Caculated storage has key, value: ", key, value
                    print "Storage should be: ", storage_data
                    result = FAIL
    return result

def compare_memory(params, exit_code):
    if exit_code == EXCEPTION and 'out' not in params: return PASS

    try:
        out = params['out']
    except:
        return JSON_STRUCTURE_NOT_MATCH

    if os.stat('memory').st_size <= 0:
        if str(out) == '0x': return PASS
        else: return EMPTY_RESULT

    result = FAIL
    with open('memory', 'r') as f:
        for line in f:
            key, value = line.split(' ')
            key, value = to_unsigned(long(key)), to_unsigned(long(value))

            mem_value = out.encode('utf-8')
            mem_value = decode_hex(mem_value)
            if mem_value == value: result = PASS
            else:
                result = FAIL
                print "Memory is: ", key, value
                print "Memory should be: ", mem_value
    return result

def run_test(params):
    exek = params['exec']
    exit_code = execute_vm(exek['code'][2:])

    storage_status = compare_storage(params, exit_code)
    mem_status = compare_memory(params, exit_code)
    if storage_status != PASS: return storage_status
    if mem_status != PASS: return mem_status
    return PASS
