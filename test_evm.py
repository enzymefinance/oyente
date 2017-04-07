import json
import glob
import os
import pickle
from global_test_params import *
from test_evm.evm_unit_test import EvmUnitTest

def status(exit_code):
    if exit_code == 0: return "Successful execution but cant evaluate result"
    if exit_code == 1: return "Error on execution"
    if exit_code == 100: return "Pass"
    if exit_code == 101: return "Fail"
    if exit_code == 102: return "Not yet handled opcode"
    if exit_code == 103: return "Json test file structure not match"
    if exit_code == 104: return "Not a number"
    if exit_code == 105: return "Time out"
    if exit_code == 106: return "Unkown instruction"
    if exit_code == 107: return "Exception"
    if exit_code == 108: return "Empty result"


def main():
    test_dir = 'test_evm/test_data'
    files = glob.glob(test_dir+'/vmArithmeticTest.json')
    test_cases = {}

    num_tests = num_passes =  num_fails = num_nyh_ops = \
        num_not_matches = num_not_a_numbers = num_time_outs = num_unkown_instrs = \
        num_exceptions = num_empty_res = num_err_exec = num_cant_eval = 0

    fails, nyh_ops, not_matchs, not_a_numbers, time_outs, \
        unkown_instrs, exceptions, empty_res, err_exec, \
        cant_eval = [], [], [], [], [], [], [], [], [], []

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
        pickle.dump(current_test, open("current_test.pickle", "wb"))

        exit_code = current_test.run_test()
        # Special case when symExec run into exception but it is correct result
        if exit_code == EXCEPTION and current_test.is_exception_case():
            exit_code = PASS

        print "===============%s!====================" % status(exit_code).upper()

        testname = testname.encode('utf8')
        num_tests += 1
        if exit_code == PASS:
            num_passes += 1
        elif exit_code == FAIL:
            fails.append(testname)
            num_fails += 1
        elif exit_code == NOT_YET_HANDLED_OPCODE:
            nyh_ops.append(testname)
            num_nyh_ops += 1
        elif exit_code == JSON_STRUCTURE_NOT_MATCH:
            not_matchs.append(testname)
            num_not_matches += 1
        elif exit_code == NOT_A_NUMBER:
            not_a_numbers.append(testname)
            num_not_a_numbers += 1
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
        elif exit_code == ERR_EXECUTION:
            err_exec.append(testname)
            num_err_exec += 1
        elif exit_code == CANT_EVALUATE:
            cant_eval.append(testname)
            num_cant_eval += 1

    print "Done!"
    print "Total: ", num_tests
    print
    print "Pass: ", num_passes
    print
    print "Fail: ", num_fails, fails
    print
    print "Not yet handled opcode: ", num_nyh_ops, nyh_ops
    print
    print "Json structure not match: ", num_not_matches, not_matchs
    print
    print "Not a number: ", num_not_a_numbers, not_a_numbers
    print
    print "Time out: ", num_time_outs, time_outs
    print
    print "Unkown instruction: ", num_unkown_instrs, unkown_instrs
    print
    print "Exception: ", num_exceptions, exceptions
    print
    print "Empty result: ", num_empty_res, empty_res
    print
    print "Error execution:", num_err_exec, err_exec
    print
    print "Cant evaluate", num_cant_eval, cant_eval

    remove_temporary_files()


def remove_temporary_files():
    if os.path.isfile("./bytecode"): os.system("rm bytecode")
    if os.path.isfile("./current_test.pickle"): os.system("rm current_test.pickle")

if __name__ == '__main__':
    main()
