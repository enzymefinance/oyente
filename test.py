import json
import glob
import testutils as testutils
from global_test_params import *

def print_test_status_footer(status):
    print "===============%s!====================" % status.upper()

def main():
    test_dir = 'tests'
    files = glob.glob(test_dir+'/vmBitwiseLogicOperationTest.json')
    fixtures = {}
    num_tests = num_passes =  num_fails = num_storage_empts = num_nyh_ops \
    = num_not_matches = 0
    fails, storage_empts, nyh_ops, not_matchs = [], [], [], []

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
        test_status = testutils.run_test(testname, testdata)
        print_test_status_footer(test_status)
        if test_status == PASS:
            num_passes += 1
        elif test_status == FAIL:
            fails.append(testname)
            num_fails += 1
        elif test_status == STORAGE_EMPTY:
            storage_empts.append(testname)
            num_storage_empts += 1
        elif test_status == NOT_YET_HANDLED_OPCODE:
            nyh_ops.append(testname)
            num_nyh_ops += 1
        elif test_status == JSON_STRUCTURE_NOT_MATCH:
            not_matchs.append(testname)
            num_not_matches += 1

    print "Done!"
    print "Total: ", num_tests
    print "Pass: ", num_passes
    print "Fail: ", num_fails, fails
    print "Storage empty: ", num_storage_empts, storage_empts
    print "Not yet handled opcode: ", num_nyh_ops, nyh_ops
    print "Json structure not match: ", num_not_matches, not_matchs


if __name__ == '__main__':
    main()
