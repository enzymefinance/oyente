# enable exceptions instead of ignoring them
IGNORE_EXCEPTIONS = 0

# enable reporting of the result
REPORT_MODE = 0

#print everything in the console
PRINT_MODE = 0

# enable data flow analysis (incomplete yet)
DATA_FLOW = 0

# enable log file to print all exception
DEBUG_MODE = 1

# check false positive in concurrency
CHECK_CONCURRENCY_FP = 0

# Timeout for z3
TIMEOUT = 1000

# Set this flag to 1 if we want to do unit test
# Set this flag to 2 if we want to do evm real value unit test
# Set this flag to 3 if we want to do evm symbolic unit test
UNIT_TEST = 0

# timeout to run symbolic execution (in secs)
GLOBAL_TIMEOUT = 2

# print path conditions
PRINT_PATHS = 0

# depth limit for DFS
DEPTH_LIMIT = 100000
