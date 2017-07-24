#!/usr/bin/env python

import glob
import json
import os
import pickle

os.chdir(os.path.dirname(__file__))

from test_evm.global_test_params import (
    PASS, FAIL, TIME_OUT, UNKOWN_INSTRUCTION, EXCEPTION, EMPTY_RESULT,
    INCORRECT_GAS, PICKLE_PATH)
from test_evm.evm_unit_test import EvmUnitTest


def status(exit_code):
    if exit_code == 100: return "Pass"
    if exit_code == 101: return "Fail"
    if exit_code == 102: return "Time out"
    if exit_code == 103: return "Unkown instruction"
    if exit_code == 104: return "Exception"
    if exit_code == 105: return "Empty result"
    if exit_code == 106: return "Incorrect gas tracked"

    return str(exit_code)


def main():
    test_dir = 'test_evm/test_data'
    files = glob.glob(test_dir + '/vmArithmeticTest.json')
    test_cases = {}

    num_tests = num_passes = num_fails = \
        num_time_outs = num_unkown_instrs = \
        num_exceptions = num_empty_res = num_incorrect_gas = 0

    fails, time_outs, \
        unkown_instrs, exceptions, empty_res, \
        incorrect_gas = [], [], [], [], [], []

    for f in files:
        test_cases.update(json.loads(open(f).read()))

    print "*****************************************************"
    print "                  *************                      "
    print "                      Start                          "
    for testname, testdata in list(test_cases.items()):
        print
        print
        print "===============Loading: %s====================" % testname

        current_test = EvmUnitTest(testname, testdata)

        pickle.dump(current_test, open(PICKLE_PATH, 'wb'), pickle.HIGHEST_PROTOCOL)

        exit_code = current_test.run_test()

        # Special case when symExec run into exception but it is correct result
        if exit_code == EXCEPTION and current_test.is_exception_case():
            exit_code = PASS

        if exit_code:
            print "===============%s!====================" % status(exit_code).upper()
        else:
            print "no exit code returned"

        testname = testname.encode('utf8')
        num_tests += 1
        if exit_code == PASS:
            num_passes += 1
        elif exit_code == FAIL:
            fails.append(testname)
            num_fails += 1
        elif exit_code == TIME_OUT:
            time_outs.append(testname)
            num_time_outs += 1
        elif exit_code == UNKOWN_INSTRUCTION:
            unkown_instrs.append(testname)
            num_unkown_instrs += 1
        elif exit_code == EXCEPTION:
            exceptions.append(testname)
            num_exceptions += 1
        elif exit_code == EMPTY_RESULT:
            empty_res.append(testname)
            num_empty_res += 1
        elif exit_code == INCORRECT_GAS:
            incorrect_gas.append(testname)
            num_incorrect_gas += 1

    print "Done!"
    print "Total: ", num_tests
    print
    print "Pass: ", num_passes
    print
    print "Fail: ", num_fails, fails
    print
    print "Time out: ", num_time_outs, time_outs
    print
    print "Unkown instruction: ", num_unkown_instrs, unkown_instrs
    print
    print "Exception: ", num_exceptions, exceptions
    print
    print "Empty result: ", num_empty_res, empty_res
    print
    print "Incorrect gas tracked", num_incorrect_gas, incorrect_gas

    remove_temporary_files()


def remove_temporary_files():
    if os.path.isfile('./bytecode'):
        os.unlink('./bytecode')

    if os.path.isfile(PICKLE_PATH):
        os.unlink(PICKLE_PATH)


if __name__ == '__main__':
    main()
