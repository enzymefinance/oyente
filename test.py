import json
import glob
import testutils as testutils
from global_test_params import *

def status(exit_code):
    if exit_code == 100: return "pass"
    if exit_code == 101: return "fail"
    if exit_code == 102: return "storage empty"
    if exit_code == 103: return "not yet handled opcode"
    if exit_code == 104: return "json test file structure not match"
    if exit_code == 105: return "not a number"
    if exit_code == 106: return "time out"
    if exit_code == 107: return "unkown instruction"
    if exit_code == 108: return "exception"

def print_exit_code_footer(exit_code):
    print "===============%s!====================" % status(exit_code).upper()

def main():
    test_dir = 'tests'
    files = glob.glob(test_dir+'vmBitwiseLogicOperationTest.json')
    fixtures = {}
    num_tests = num_passes =  num_fails = num_storage_empts = num_nyh_ops = \
    num_not_matches = num_not_a_numbers = num_time_outs = num_unkown_instrs = \
    num_exceptions = 0

    fails, storage_empts, nyh_ops, not_matchs, not_a_numbers, time_outs, \
    unkown_instrs, exceptions = [], [], [], [], [], [], [], []

    for f in files:
        fixtures.update(json.loads(open(f).read()))

    print "*****************************************************"
    print "                  *************                      "
    print "                      Start                          "
    for testname, testdata in list(fixtures.items()):
        print
        print
        print "===============Loading: %s====================" % testname
        num_tests += 1
        testname = testname.encode('utf-8')
        exit_code = testutils.run_test(testname, testdata)
        print_exit_code_footer(exit_code)
        if exit_code == PASS:
            num_passes += 1
        elif exit_code == FAIL:
            fails.append(testname)
            num_fails += 1
        elif exit_code == STORAGE_EMPTY:
            storage_empts.append(testname)
            num_storage_empts += 1
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

    print "Done!"
    print "Total: ", num_tests
    print
    print "Pass: ", num_passes
    print
    print "Fail: ", num_fails, fails
    print
    print "Storage empty: ", num_storage_empts, storage_empts
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

if __name__ == '__main__':
    main()
