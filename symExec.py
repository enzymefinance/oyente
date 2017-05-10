from z3 import *
from vargenerator import *
from ethereum_data import *
import tokenize
import signal
from tokenize import NUMBER, NAME, NEWLINE
from basicblock import BasicBlock
from analysis import *
from utils import *
import math
from arithmetic_utils import *
import time
from global_params import *
from test_evm.global_test_params import *
import sys
import atexit
import logging
import pickle
import json
from collections import namedtuple

results = {}

UNSIGNED_BOUND_NUMBER = 2**256 - 1

if len(sys.argv) >= 16:
    IGNORE_EXCEPTIONS = int(sys.argv[2])
    REPORT_MODE = int(sys.argv[3])
    PRINT_MODE = int(sys.argv[4])
    DATA_FLOW = int(sys.argv[5])
    DEBUG_MODE = int(sys.argv[6])
    CHECK_CONCURRENCY_FP = int(sys.argv[7])
    TIMEOUT = int(sys.argv[8])
    UNIT_TEST = int(sys.argv[9])
    GLOBAL_TIMEOUT = int(sys.argv[10])
    PRINT_PATHS = int(sys.argv[11])
    USE_GLOBAL_BLOCKCHAIN = int(sys.argv[12])
    DEPTH_LIMIT = int(sys.argv[13])
    GAS_LIMIT = int(sys.argv[14])
    USE_INPUT_STATE = int(sys.argv[15])
    LOOP_LIMIT = int(sys.argv[16])

if REPORT_MODE:
    report_file = sys.argv[1] + '.report'
    rfile = open(report_file, 'w')

count_unresolved_jumps = 0
gen = Generator()  # to generate names for symbolic variables
if USE_GLOBAL_BLOCKCHAIN:
    data_source = EthereumData()

end_ins_dict = {}  # capturing the last statement of each basic block
instructions = {}  # capturing all the instructions, keys are corresponding addresses
jump_type = {}  # capturing the "jump type" of each basic block
vertices = {}
Edge = namedtuple("Edge", ["v1", "v2"]) # Factory Function for tuples is used as dictionary key
edges = {}
visited_edges = {}
money_flow_all_paths = []
reentrancy_all_paths =[]
data_flow_all_paths = [[], []] # store all storage addresses
path_conditions = [] # store the path condition corresponding to each path in money_flow_all_paths
all_gs = [] # store global variables, e.g. storage, balance of all paths
total_no_of_paths = 0

c_name = sys.argv[1]
if(len(c_name) > 5):
    c_name = c_name[4:]
set_cur_file(c_name)

# Z3 solver
solver = Solver()
solver.set("timeout", TIMEOUT)

CONSTANT_ONES_159 = BitVecVal((1 << 160) - 1, 256)

if UNIT_TEST == 1:
    try:
        result_file = open(sys.argv[16], 'r')
    except:
        if PRINT_MODE: print "Could not open result file for unit test"
        exit()


log_file = open(sys.argv[1] + '.log', "w")

def isSymbolic(value):
    return not isinstance(value, (int, long))

def isReal(value):
    return isinstance(value, (int, long))

def isTesting():
    return UNIT_TEST != 0

# A simple function to compare the end stack with the expected stack
# configurations specified in a test file
def compare_stack_unit_test(stack):
    try:
        size = int(result_file.readline())
        content = result_file.readline().strip('\n')
        if size == len(stack) and str(stack) == content:
            if PRINT_MODE: print "PASSED UNIT-TEST"
        else:
            if PRINT_MODE: print "FAILED UNIT-TEST"
            if PRINT_MODE: print "Expected size %d, Resulted size %d" % (size, len(stack))
            if PRINT_MODE: print "Expected content %s \nResulted content %s" % (content, str(stack))
    except Exception as e:
        if PRINT_MODE: print "FAILED UNIT-TEST"
        if PRINT_MODE: print e.message

def compare_storage_and_memory_unit_test(global_state, mem, analysis):
    unit_test = pickle.load(open("current_test.pickle", "rb"))
    test_status = unit_test.compare_with_symExec_result(global_state, mem, analysis)
    exit(test_status)

def handler(signum, frame):
    if UNIT_TEST == 2 or UNIT_TEST == 3: exit(TIME_OUT)
    raise Exception("timeout")

def main():
    start = time.time()
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(GLOBAL_TIMEOUT)

    print "Running, please wait..."


    if not isTesting(): print "\t============ Results ==========="

    if PRINT_MODE:
        print "Checking for Callstack attack..."
    run_callstack_attack()

    try:
        build_cfg_and_analyze()
        if PRINT_MODE:
            print "Done Symbolic execution"
    except Exception as e:
        if UNIT_TEST == 2 or UNIT_TEST == 3:
            logging.exception(e)
            exit(EXCEPTION)
        print "Exception - "+str(e)
        raise e
    signal.alarm(0)

    if REPORT_MODE:
        rfile.write(str(total_no_of_paths) + "\n")
    detect_money_concurrency()
    detect_time_dependency()
    stop = time.time()
    if REPORT_MODE:
        rfile.write(str(stop-start))
        rfile.close()
    if DATA_FLOW:
        detect_data_concurrency()
        detect_data_money_concurrency()
    if PRINT_MODE:
        print "Results for Reentrancy Bug: " + str(reentrancy_all_paths)
    reentrancy_bug_found = any([v for sublist in reentrancy_all_paths for v in sublist])
    if not isTesting(): print "\t  Reentrancy bug exists: %s" % str(reentrancy_bug_found)
    results['reentrancy'] = reentrancy_bug_found

def closing_message():
    if UNIT_TEST ==1: print "\t====== Analysis Completed ======"
    if len(sys.argv) > 17:
        with open(sys.argv[17], 'w') as of:
            of.write(json.dumps(results,indent=1))
        print "Wrote results to %s." % sys.argv[17]

atexit.register(closing_message)

def change_format():
    with open(sys.argv[1]) as disasm_file:
        file_contents = disasm_file.readlines()
        i = 0
        firstLine = file_contents[0].strip('\n')
        for line in file_contents:
            line = line.replace('SELFDESTRUCT', 'SUICIDE')
            line = line.replace('Missing opcode', 'INVALID')
            line = line.replace(':','')
            lineParts = line.split(' ')
            try: # removing initial zeroes
                lineParts[0] = str(int(lineParts[0]))

            except:
                lineParts[0] = lineParts[0]
            lineParts[-1] = lineParts[-1].strip('\n')
            try: # adding arrow if last is a number
                lastInt = lineParts[-1]
                if(int(lastInt,16) or int(lastInt,16) == 0) and len(lineParts) > 2:
                    lineParts[-1] = "=>"
                    lineParts.append(lastInt)
            except Exception as e:
                pass
            file_contents[i] = ' '.join(lineParts)
            i = i + 1
        file_contents[0] = firstLine
        file_contents[-1] += '\n'

    with open(sys.argv[1], 'w') as disasm_file:
       disasm_file.write("\n".join(file_contents))


def build_cfg_and_analyze():
    change_format()
    with open(sys.argv[1], 'r') as disasm_file:
        disasm_file.readline()  # Remove first line
        tokens = tokenize.generate_tokens(disasm_file.readline)
        collect_vertices(tokens)
        construct_bb()
        construct_static_edges()
        full_sym_exec()  # jump targets are constructed on the fly


# Detect if a money flow depends on the timestamp
def detect_time_dependency():
    TIMESTAMP_VAR = "IH_s"
    is_dependant = False
    index = 0
    if PRINT_PATHS:
        print "ALL PATH CONDITIONS"
    for cond in path_conditions:
        index += 1
        if PRINT_PATHS:
            print "PATH " + str(index) + ": " + str(cond)
        list_vars = []
        for expr in cond:
            if is_expr(expr):
                list_vars += get_vars(expr)
        set_vars = set(i.decl().name() for i in list_vars)
        if TIMESTAMP_VAR in set_vars:
            is_dependant = True
            break

    if not isTesting(): print "\t  Time Dependency: \t %s" % is_dependant
    results['time_dependency'] = is_dependant

    if REPORT_MODE:
        file_name = sys.argv[1].split("/")[len(sys.argv[1].split("/"))-1].split(".")[0]
        report_file = file_name + '.report'
        with open(report_file, 'w') as rfile:
            if is_dependant:
                rfile.write("yes\n")
            else:
                rfile.write("no\n")


# detect if two paths send money to different people
def detect_money_concurrency():
    n = len(money_flow_all_paths)
    for i in range(n):
        if PRINT_MODE: print "Path " + str(i) + ": " + str(money_flow_all_paths[i])
        if PRINT_MODE: print all_gs[i]
    i = 0
    false_positive = []
    concurrency_paths = []
    for flow in money_flow_all_paths:
        i += 1
        if len(flow) == 1:
            continue  # pass all flows which do not do anything with money
        for j in range(i, n):
            jflow = money_flow_all_paths[j]
            if len(jflow) == 1:
                continue
            if is_diff(flow, jflow):
                concurrency_paths.append([i-1, j])
                if CHECK_CONCURRENCY_FP and \
                        is_false_positive(i-1, j, all_gs, path_conditions) and \
                        is_false_positive(j, i-1, all_gs, path_conditions):
                    false_positive.append([i-1, j])

    # if PRINT_MODE: print "All false positive cases: ", false_positive
    if PRINT_MODE: print "Concurrency in paths: ", concurrency_paths
    if len(concurrency_paths) > 0:
        if not isTesting(): print "\t  Concurrency found in paths: %s" + str(concurrency_paths)
        results['concurrency'] = True
    else:
        if not isTesting(): print "\t  Concurrency Bug: \t False"
        results['concurrency'] = False
    if REPORT_MODE:
        rfile.write("number of path: " + str(n) + "\n")
        # number of FP detected
        rfile.write(str(len(false_positive)) + "\n")
        rfile.write(str(false_positive) + "\n")
        # number of total races
        rfile.write(str(len(concurrency_paths)) + "\n")
        # all the races
        rfile.write(str(concurrency_paths) + "\n")


# Detect if there is data concurrency in two different flows.
# e.g. if a flow modifies a value stored in the storage address and
# the other one reads that value in its execution
def detect_data_concurrency():
    sload_flows = data_flow_all_paths[0]
    sstore_flows = data_flow_all_paths[1]
    concurrency_addr = []
    for sflow in sstore_flows:
        for addr in sflow:
            for lflow in sload_flows:
                if addr in lflow:
                    if not addr in concurrency_addr:
                        concurrency_addr.append(addr)
                    break
    if PRINT_MODE: print "data conccureny in storage " + str(concurrency_addr)

# Detect if any change in a storage address will result in a different
# flow of money. Currently I implement this detection by
# considering if a path condition contains
# a variable which is a storage address.
def detect_data_money_concurrency():
    n = len(money_flow_all_paths)
    sstore_flows = data_flow_all_paths[1]
    concurrency_addr = []
    for i in range(n):
        cond = path_conditions[i]
        list_vars = []
        for expr in cond:
            list_vars += get_vars(expr)
        set_vars = set(i.decl().name() for i in list_vars)
        for sflow in sstore_flows:
            for addr in sflow:
                var_name = gen.gen_owner_store_var(addr)
                if var_name in set_vars:
                    concurrency_addr.append(var_name)
    if PRINT_MODE: print "Concurrency in data that affects money flow: " + str(set(concurrency_addr))


def print_cfg():
    for block in vertices.values():
        block.display()
    if PRINT_MODE: print str(edges)


# 1. Parse the disassembled file
# 2. Then identify each basic block (i.e. one-in, one-out)
# 3. Store them in vertices
def collect_vertices(tokens):
    current_ins_address = 0
    last_ins_address = 0
    is_new_line = True
    current_block = 0
    current_line_content = ""
    wait_for_push = False
    is_new_block = False

    for tok_type, tok_string, (srow, scol), _, line_number in tokens:
        if wait_for_push is True:
            push_val = ""
            for ptok_type, ptok_string, _, _, _ in tokens:
                if ptok_type == NEWLINE:
                    is_new_line = True
                    current_line_content += push_val + ' '
                    instructions[current_ins_address] = current_line_content
                    if PRINT_MODE: print current_line_content
                    current_line_content = ""
                    wait_for_push = False
                    break
                try:
                    int(ptok_string, 16)
                    push_val += ptok_string
                except ValueError:
                    pass

            continue
        elif is_new_line is True and tok_type == NUMBER:  # looking for a line number
            last_ins_address = current_ins_address
            try:
                current_ins_address = int(tok_string)
            except ValueError:
                if PRINT_MODE: print "ERROR when parsing row %d col %d" % (srow, scol)
                quit()
            is_new_line = False
            if is_new_block:
                current_block = current_ins_address
                is_new_block = False
            continue
        elif tok_type == NEWLINE:
            is_new_line = True
            if PRINT_MODE: print current_line_content
            instructions[current_ins_address] = current_line_content
            current_line_content = ""
            continue
        elif tok_type == NAME:
            if tok_string == "JUMPDEST":
                if not (last_ins_address in end_ins_dict):
                    end_ins_dict[current_block] = last_ins_address
                current_block = current_ins_address
                is_new_block = False
            elif tok_string == "STOP" or tok_string == "RETURN" or tok_string == "SUICIDE":
                jump_type[current_block] = "terminal"
                end_ins_dict[current_block] = current_ins_address
            elif tok_string == "JUMP":
                jump_type[current_block] = "unconditional"
                end_ins_dict[current_block] = current_ins_address
                is_new_block = True
            elif tok_string == "JUMPI":
                jump_type[current_block] = "conditional"
                end_ins_dict[current_block] = current_ins_address
                is_new_block = True
            elif tok_string.startswith('PUSH', 0):
                wait_for_push = True
            is_new_line = False
        if tok_string != "=" and tok_string != ">":
            current_line_content += tok_string + " "

    if current_block not in end_ins_dict:
        if PRINT_MODE: print "current block: %d" % current_block
        if PRINT_MODE: print "last line: %d" % current_ins_address
        end_ins_dict[current_block] = current_ins_address

    if current_block not in jump_type:
        jump_type[current_block] = "terminal"

    for key in end_ins_dict:
        if key not in jump_type:
            jump_type[key] = "falls_to"


def construct_bb():
    sorted_addresses = sorted(instructions.keys())
    size = len(sorted_addresses)
    for key in end_ins_dict:
        end_address = end_ins_dict[key]
        block = BasicBlock(key, end_address)
        if key not in instructions: continue
        block.add_instruction(instructions[key])
        i = sorted_addresses.index(key) + 1
        while i < size and sorted_addresses[i] <= end_address:
            block.add_instruction(instructions[sorted_addresses[i]])
            i += 1
        block.set_block_type(jump_type[key])
        vertices[key] = block
        edges[key] = []


def construct_static_edges():
    add_falls_to()  # these edges are static


def add_falls_to():
    key_list = sorted(jump_type.keys())
    length = len(key_list)
    for i, key in enumerate(key_list):
        if jump_type[key] != "terminal" and jump_type[key] != "unconditional" and i+1 < length:
            target = key_list[i+1]
            edges[key].append(target)
            vertices[key].set_falls_to(target)


def get_init_global_state(path_conditions_and_vars):
    global_state = { "balance" : {} , "pc": 0 }
    init_is = init_ia = deposited_value = sender_address = receiver_address = gas_price = origin = currentCoinbase = currentTimestamp = currentNumber = currentDifficulty = currentGasLimit = callData = None

    if USE_INPUT_STATE:
        with open('state.json') as f:
            state = json.loads(f.read())
            if state["Is"]["balance"]:
                init_is = int(state["Is"]["balance"], 16)
            if state["Ia"]["balance"]:
                init_ia = int(state["Ia"]["balance"], 16)
            if state["exec"]["value"]:
                deposited_value = int(state["exec"]["value"], 16)
            if state["Is"]["address"]:
                sender_address = int(state["Is"]["address"], 16)
            if state["Ia"]["address"]:
                receiver_address = int(state["Ia"]["address"], 16)
            if state["exec"]["gasPrice"]:
                gas_price = int(state["exec"]["gasPrice"], 16)
            if state["exec"]["origin"]:
                origin = int(state["exec"]["origin"], 16)
            if state["env"]["currentCoinbase"]:
                currentCoinbase = int(state["env"]["currentCoinbase"], 16)
            if state["env"]["currentTimestamp"]:
                currentTimestamp = int(state["env"]["currentTimestamp"], 16)
            if state["env"]["currentNumber"]:
                currentNumber = int(state["env"]["currentNumber"], 16)
            if state["env"]["currentDifficulty"]:
                currentDifficulty = int(state["env"]["currentDifficulty"], 16)
            if state["env"]["currentGasLimit"]:
                currentGasLimit = int(state["env"]["currentGasLimit"], 16)
            if state["exec"]["data"]:
                callData = state["exec"]["data"]
                if callData[:2] == "0x":
                    callData = callData[2:]

    # for some weird reason these 3 vars are stored in path_conditions insteaad of global_state
    if not sender_address:
        sender_address = BitVec("Is", 256)
    path_conditions_and_vars["Is"] = sender_address

    if not receiver_address:
        receiver_address = BitVec("Ia", 256)
    path_conditions_and_vars["Ia"] = receiver_address

    if not deposited_value:
        deposited_value = BitVec("Iv", 256)
    path_conditions_and_vars["Iv"] = deposited_value

    if not init_is:
        init_is = BitVec("init_Is", 256)
    if not init_ia:
        init_ia = BitVec("init_Ia", 256)

    constraint = (deposited_value >= BitVecVal(0, 256))
    path_conditions_and_vars["path_condition"].append(constraint)
    constraint = (init_is >= deposited_value)
    path_conditions_and_vars["path_condition"].append(constraint)
    constraint = (init_ia >= BitVecVal(0, 256))
    path_conditions_and_vars["path_condition"].append(constraint)

    # update the balances of the "caller" and "callee"

    global_state["balance"]["Is"] = (init_is - deposited_value)
    global_state["balance"]["Ia"] = (init_ia + deposited_value)

    if not gas_price:
        new_var_name = gen.gen_gas_price_var()
        gas_price = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = gas_price

    if not origin:
        new_var_name = gen.gen_origin_var()
        origin = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = origin

    if not currentCoinbase:
        new_var_name = "IH_c"
        currentCoinbase = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentCoinbase

    if not currentTimestamp:
        new_var_name = "IH_s"
        currentTimestamp = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentTimestamp

    if not currentNumber:
        new_var_name = "IH_i"
        currentNumber = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentNumber

    if not currentDifficulty:
        new_var_name = "IH_d"
        currentDifficulty = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentDifficulty

    if not currentGasLimit:
        new_var_name = "IH_l"
        currentGasLimit = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = currentGasLimit

    if not callData:
        new_var_name = gen.gen_data_size()
        callData = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = callData  

    # the state of the current current contract
    global_state["Ia"] = {}
    global_state["miu_i"] = 0
    global_state["value"] = deposited_value
    global_state["sender_address"] = sender_address
    global_state["receiver_address"] = receiver_address
    global_state["gas_price"] = gas_price
    global_state["origin"] = origin
    global_state["currentCoinbase"] = currentCoinbase
    global_state["currentTimestamp"] = currentTimestamp
    global_state["currentNumber"] = currentNumber
    global_state["currentDifficulty"] = currentDifficulty
    global_state["currentGasLimit"] = currentGasLimit
    global_state["callData"] = callData

    return global_state


def full_sym_exec():
    # executing, starting from beginning
    stack = []
    path_conditions_and_vars = {"path_condition" : []}
    visited, depth = [], 0
    mem = {}
    global_state = get_init_global_state(path_conditions_and_vars)  # this is init global state for this particular execution
    analysis = init_analysis()
    return sym_exec_block(0, 0, visited, depth, stack, mem, global_state, path_conditions_and_vars, analysis)


# Symbolically executing a block from the start address
def sym_exec_block(block, pre_block, visited, depth, stack, mem, global_state, path_conditions_and_vars, analysis):
    if block < 0:
        if PRINT_MODE: print "ERROR: UNKNOWN JUMP ADDRESS. TERMINATING THIS PATH"
        return ["ERROR"]

    if PRINT_MODE: print "\nDEBUG: Reach block address %d \n" % block
    if PRINT_MODE: print "STACK: " + str(stack)

    current_edge = Edge(pre_block, block)
    if visited_edges.has_key(current_edge):
        updated_count_number = visited_edges[current_edge] + 1
        visited_edges.update({current_edge: updated_count_number})
    else:
        visited_edges.update({current_edge: 1})

    if visited_edges[current_edge] > LOOP_LIMIT:
        if PRINT_MODE: print "Overcome a number of loop limit. Terminating this path ..."
        return stack

    current_gas_used = analysis["gas"]
    if  current_gas_used > GAS_LIMIT :
        if PRINT_MODE: print "Run out of gas. Terminating this path ... "
        return stack

    # Execute every instruction, one at a time
    try:
        block_ins = vertices[block].get_instructions()
    except KeyError:
        if PRINT_MODE: print "This path results in an exception, possibly an invalid jump address"
        return ["ERROR"]

    for instr in block_ins:
        sym_exec_ins(block, instr, stack, mem, global_state, path_conditions_and_vars, analysis)

    # Mark that this basic block in the visited blocks
    visited.append(block)
    depth += 1

    # Go to next Basic Block(s)
    if jump_type[block] == "terminal" or depth > DEPTH_LIMIT:
        if PRINT_MODE: print "TERMINATING A PATH ..."
        display_analysis(analysis)
        global total_no_of_paths
        total_no_of_paths += 1
        reentrancy_all_paths.append(analysis["reentrancy_bug"])
        if analysis["money_flow"] not in money_flow_all_paths:
            money_flow_all_paths.append(analysis["money_flow"])
            path_conditions.append(path_conditions_and_vars["path_condition"])
            all_gs.append(copy_global_values(global_state))
        if DATA_FLOW:
            if analysis["sload"] not in data_flow_all_paths[0]:
                data_flow_all_paths[0].append(analysis["sload"])
            if analysis["sstore"] not in data_flow_all_paths[1]:
                data_flow_all_paths[1].append(analysis["sstore"])
        if UNIT_TEST == 1: compare_stack_unit_test(stack)
        if UNIT_TEST == 2 or UNIT_TEST == 3: compare_storage_and_memory_unit_test(global_state, mem, analysis)

    elif jump_type[block] == "unconditional":  # executing "JUMP"
        successor = vertices[block].get_jump_target()
        stack1 = list(stack)
        mem1 = dict(mem)
        global_state1 = my_copy_dict(global_state)
        global_state1["pc"] = successor
        visited1 = list(visited)
        path_conditions_and_vars1 = my_copy_dict(path_conditions_and_vars)
        analysis1 = my_copy_dict(analysis)
        sym_exec_block(successor, block, visited1, depth, stack1, mem1, global_state1, path_conditions_and_vars1, analysis1)
    elif jump_type[block] == "falls_to":  # just follow to the next basic block
        successor = vertices[block].get_falls_to()
        stack1 = list(stack)
        mem1 = dict(mem)
        global_state1 = my_copy_dict(global_state)
        global_state1["pc"] = successor
        visited1 = list(visited)
        path_conditions_and_vars1 = my_copy_dict(path_conditions_and_vars)
        analysis1 = my_copy_dict(analysis)
        sym_exec_block(successor, block, visited1, depth, stack1, mem1, global_state1, path_conditions_and_vars1, analysis1)
    elif jump_type[block] == "conditional":  # executing "JUMPI"

        # A choice point, we proceed with depth first search

        branch_expression = vertices[block].get_branch_expression()

        if PRINT_MODE: print "Branch expression: " + str(branch_expression)

        solver.push()  # SET A BOUNDARY FOR SOLVER
        solver.add(branch_expression)

        try:
            if solver.check() == unsat:
                if PRINT_MODE: print "INFEASIBLE PATH DETECTED"
            else:
                left_branch = vertices[block].get_jump_target()
                stack1 = list(stack)
                mem1 = dict(mem)
                global_state1 = my_copy_dict(global_state)
                global_state1["pc"] = left_branch
                visited1 = list(visited)
                path_conditions_and_vars1 = my_copy_dict(path_conditions_and_vars)
                path_conditions_and_vars1["path_condition"].append(branch_expression)
                analysis1 = my_copy_dict(analysis)
                sym_exec_block(left_branch, block, visited1, depth, stack1, mem1, global_state1, path_conditions_and_vars1, analysis1)
        except Exception as e:
            log_file.write(str(e))
            print "Exception - "+str(e)
            if not IGNORE_EXCEPTIONS:
                if str(e) == "timeout":
                    raise e

        solver.pop()  # POP SOLVER CONTEXT

        solver.push()  # SET A BOUNDARY FOR SOLVER
        negated_branch_expression = Not(branch_expression)
        solver.add(negated_branch_expression)

        if PRINT_MODE: print "Negated branch expression: " + str(negated_branch_expression)

        try:
            if solver.check() == unsat:
                # Note that this check can be optimized. I.e. if the previous check succeeds,
                # no need to check for the negated condition, but we can immediately go into
                # the else branch
                if PRINT_MODE: print "INFEASIBLE PATH DETECTED"
            else:
                right_branch = vertices[block].get_falls_to()
                stack1 = list(stack)
                mem1 = dict(mem)
                global_state1 = my_copy_dict(global_state)
                global_state1["pc"] = right_branch
                visited1 = list(visited)
                path_conditions_and_vars1 = my_copy_dict(path_conditions_and_vars)
                path_conditions_and_vars1["path_condition"].append(negated_branch_expression)
                analysis1 = my_copy_dict(analysis)
                sym_exec_block(right_branch, block, visited1, depth, stack1, mem1, global_state1, path_conditions_and_vars1, analysis1)
        except Exception as e:
            log_file.write(str(e))
            if str(e) == "timeout":
                raise e
        solver.pop()  # POP SOLVER CONTEXT
        updated_count_number = visited_edges[current_edge] - 1
        visited_edges.update({current_edge: updated_count_number})
    else:
        updated_count_number = visited_edges[current_edge] - 1
        visited_edges.update({current_edge: updated_count_number})
        raise Exception('Unknown Jump-Type')


# Symbolically executing an instruction
def sym_exec_ins(start, instr, stack, mem, global_state, path_conditions_and_vars, analysis):
    instr_parts = str.split(instr, ' ')

    if instr_parts[0] == "INVALID":
        return

    # collecting the analysis result by calling this skeletal function
    # this should be done before symbolically executing the instruction,
    # since SE will modify the stack and mem
    update_analysis(analysis, instr_parts[0], stack, mem, global_state, path_conditions_and_vars, solver)

    if PRINT_MODE: print "=============================="
    if PRINT_MODE: print "EXECUTING: " + instr

    #
    #  0s: Stop and Arithmetic Operations
    #
    if instr_parts[0] == "STOP":
        global_state["pc"] = global_state["pc"] + 1
        return
    elif instr_parts[0] == "ADD":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            # Type conversion is needed when they are mismatched
            if isinstance(first, (int, long)) and not isinstance(second, (int, long)):
                first = BitVecVal(first, 256)
                computed = first + second
            elif not isinstance(first, (int, long)) and isinstance(second, (int, long)):
                second = BitVecVal(second, 256)
                computed = first + second
            else:
                # both are real and we need to manually modulus with 2 ** 256
                # if both are symbolic z3 takes care of modulus automatically
                computed = (first + second) % (2 ** 256)
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MUL":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and not isinstance(second, (int, long)):
                first = BitVecVal(first, 256)
            elif not isinstance(first, (int, long)) and isinstance(second, (int, long)):
                second = BitVecVal(second, 256)
            computed = first * second & UNSIGNED_BOUND_NUMBER
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SUB":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and not isinstance(second, (int, long)):
                first = BitVecVal(first, 256)
                computed = first - second
            elif not isinstance(first, (int, long)) and isinstance(second, (int, long)):
                second = BitVecVal(second, 256)
                computed = first - second
            else:
                computed = (first - second) % (2 ** 256)
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "DIV":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if contains_only_concrete_values([first, second]):
                if second == 0:
                    computed = 0
                else:
                    first = to_unsigned(first)
                    second = to_unsigned(second)
                    computed = first / second
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add( Not (second == 0) )
                if solver.check() == unsat:
                    computed = 0
                else:
                    computed = UDiv(first, second)
                solver.pop()
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SDIV":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if contains_only_concrete_values([first, second]):
                first = to_signed(first)
                second = to_signed(second)
                if second == 0:
                    computed = 0
                elif first == -2**255 and second == -1:
                    computed = -2**255
                else:
                    sign = -1 if (first / second) < 0 else 1
                    computed = sign * ( abs(first) / abs(second) )
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add( Not(second == 0) )
                if solver.check() == unsat:
                    computed = 0
                else:
                    solver.push()
                    solver.add( Not( And(first == -2**255, second == -1 ) ))
                    if solver.check() == unsat:
                        computed = -2**255
                    else:
                        solver.push()
                        solver.add(first / second < 0)
                        sign = -1 if solver.check() == sat else 1
                        z3_abs = lambda x: If(x >= 0, x, -x)
                        first = z3_abs(first)
                        second = z3_abs(second)
                        computed = sign * (first / second)
                        solver.pop()
                    solver.pop()
                solver.pop()
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MOD":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
                # handle for real value variables
                if second == 0:
                    computed = 0
                else:
                    first = to_unsigned(first)
                    second = to_unsigned(second)
                    computed = first % second & UNSIGNED_BOUND_NUMBER

            else:
                # handle for symbolic variables
                if isinstance(first, (int, long)):
                    first = BitVecVal(first, 256)  # Make first as a bitvector
                if isinstance(second, (int, long)):
                    second = BitVecVal(second, 256) # Make second as a bitvector

                solver.push()
                solver.add(Not(second == 0))
                if solver.check() == unsat:
                    # it is provable that second is indeed equal to zero
                    computed = 0
                else:
                    computed = URem(first, second)
                solver.pop()

            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SMOD":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
                # handle for real value variables
                if second == 0:
                    computed = 0
                else:
                    first = to_signed(first)
                    second = to_signed(second)
                    sign = -1 if first < 0 else 1
                    computed = sign * (abs(first) % abs(second))
            else:
                # handle for symbolic variables
                if isinstance(first, (int, long)):
                    first = BitVecVal(first, 256)  # Make first as a bitvector
                if isinstance(second, (int, long)):
                    second = BitVecVal(second, 256) # Make second as a bitvector

                solver.push()
                solver.add(Not(second == 0))
                if solver.check() == unsat:
                    # it is provable that second is indeed equal to zero
                    computed = 0
                else:

                    solver.push()
                    solver.add(first < 0) # check sign of first element
                    sign = BitVecVal(-1, 256) if solver.check() == sat \
                        else BitVecVal(1, 256)
                    solver.pop()

                    z3_abs = lambda x: If(x >= 0, x, -x)
                    first = z3_abs(first)
                    second = z3_abs(second)

                    computed = sign * (first % second)
                solver.pop()

            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "ADDMOD":
        if len(stack) > 2:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            third = stack.pop(0)

            if contains_only_concrete_values([first, second, third]):
                if third == 0:
                    computed = 0
                else:
                    computed = (first + second) % third
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add( Not(third == 0) )
                if solver.check() == unsat:
                    computed = 0
                else:
                    first = ZeroExt(256, first)
                    second = ZeroExt(256, second)
                    third = ZeroExt(256, third)
                    computed = (first + second) % third
                    computed = Extract(255, 0, computed)
                solver.pop()
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MULMOD":
        if len(stack) > 2:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            third = stack.pop(0)

            if contains_only_concrete_values([first, second, third]):
                if third == 0:
                    computed = 0
                else:
                    computed = (first * second) % third
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add( Not(third == 0) )
                if solver.check() == unsat:
                    computed = 0
                else:
                    first = ZeroExt(256, first)
                    second = ZeroExt(256, second)
                    third = ZeroExt(256, third)
                    computed = URem(first * second, third)
                    computed = Extract(255, 0, computed)
                solver.pop()
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "EXP":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            base = stack.pop(0)
            exponent = stack.pop(0)
            # Type conversion is needed when they are mismatched
            if isinstance(base, (int, long)) and isinstance(exponent, (int, long)):
                computed = pow(base, exponent, 2**256)
            else:
                # The computed value is unknown, this is because power is
                # not supported in bit-vector theory
                new_var_name = gen.gen_arbitrary_var()
                computed = BitVec(new_var_name, 256)
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SIGNEXTEND":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if contains_only_concrete_values([first, second]):
                if first >= 32 or first < 0:
                    computed = second
                else:
                   signbit_index_from_right = 8 * first + 7
                   if second & (1 << signbit_index_from_right):
                       computed = second | (2 ** 256 - (1 << signbit_index_from_right) )
                   else:
                       computed = second & ( (1 << signbit_index_from_right) - 1 )
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add( Not( Or(first >= 32, first < 0 ) ) )
                if solver.check() == unsat:
                    computed = second
                else:
                    signbit_index_from_right = 8 * first + 7
                    solver.push()
                    solver.add( second & (1 << signbit_index_from_right) == 0 )
                    if solver.check() == unsat:
                        computed = second | ( 2 ** 256 - (1 << signbit_index_from_right) )
                    else:
                        computed = second & ( (1 << signbit_index_from_right) - 1 )
                    solver.pop()
                solver.pop()
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    #
    #  10s: Comparison and Bitwise Logic Operations
    #
    elif instr_parts[0] == "LT":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
                first = to_unsigned(first)
                second = to_unsigned(second)
                if first < second:
                    stack.insert(0, 1)
                else:
                    stack.insert(0, 0)
            else:
                sym_expression = If(ULT(first, second), BitVecVal(1, 256), BitVecVal(0, 256))
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "GT":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
                first = to_unsigned(first)
                second = to_unsigned(second)
                if first > second:
                    stack.insert(0, 1)
                else:
                    stack.insert(0, 0)
            else:
                sym_expression = If(UGT(first, second), BitVecVal(1, 256), BitVecVal(0, 256))
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SLT":  # Not fully faithful to signed comparison
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
                first = to_signed(first)
                second = to_signed(second)
                if first < second:
                    stack.insert(0, 1)
                else:
                    stack.insert(0, 0)
            else:
                sym_expression = If(first < second, BitVecVal(1, 256), BitVecVal(0, 256))
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SGT":  # Not fully faithful to signed comparison
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
                first = to_signed(first)
                second = to_signed(second)
                if first > second:
                    stack.insert(0, 1)
                else:
                    stack.insert(0, 0)
            else:
                sym_expression = If(first > second, BitVecVal(1, 256), BitVecVal(0, 256))
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "EQ":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
                if first == second:
                    stack.insert(0, 1)
                else:
                    stack.insert(0, 0)
            else:
                sym_expression = If(first == second, BitVecVal(1, 256), BitVecVal(0, 256))
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "ISZERO":
        # Tricky: this instruction works on both boolean and integer,
        # when we have a symbolic expression, type error might occur
        # Currently handled by try and catch
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            if isinstance(first, (int, long)):
                if first == 0:
                    stack.insert(0, 1)
                else:
                    stack.insert(0, 0)
            else:
                sym_expression = If(first == 0, BitVecVal(1, 256), BitVecVal(0, 256))
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "AND":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)
            computed = first & second
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "OR":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)

            computed = first | second
            stack.insert(0, computed)

        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "XOR":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            second = stack.pop(0)

            computed = first ^ second
            stack.insert(0, computed)

        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "NOT":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            computed = (~first) & UNSIGNED_BOUND_NUMBER
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "BYTE":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            first = stack.pop(0)
            byte_index = 32 - first - 1
            second = stack.pop(0)

            if contains_only_concrete_values([first, second]):
                if first >= 32 or first < 0:
                    computed = 0
                else:
                    computed = second & (255 << (8 * byte_index))
                    computed = computed >> (8 * byte_index)
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)
                solver.push()
                solver.add( Not (Or( first >= 32, first < 0 ) ) )
                if solver.check() == unsat:
                    computed = 0
                else:
                    computed = second & (255 << (8 * byte_index))
                    computed = computed >> (8 * byte_index)
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    #
    # 20s: SHA3
    #
    elif instr_parts[0] == "SHA3":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            stack.pop(0)
            stack.pop(0)
            # push into the execution a fresh symbolic variable
            new_var_name = gen.gen_arbitrary_var()
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
            stack.insert(0, new_var)
        else:
            raise ValueError('STACK underflow')
    #
    # 30s: Environment Information
    #
    elif instr_parts[0] == "ADDRESS":  # get address of currently executing account
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, path_conditions_and_vars["Ia"])
    elif instr_parts[0] == "BALANCE":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            address = stack.pop(0)
            if isReal(address) and USE_GLOBAL_BLOCKCHAIN:
                new_var = data_source.getBalance(address)
            else:
                new_var_name = gen.gen_balance_var()
                if new_var_name in path_conditions_and_vars:
                    new_var = path_conditions_and_vars[new_var_name]
                else:
                    new_var = BitVec(new_var_name, 256)
                    path_conditions_and_vars[new_var_name] = new_var
            if isReal(address):
                hashed_address = "concrete_address_" + str(address)
            else:
                hashed_address = str(address)
            global_state["balance"][hashed_address] = new_var
            stack.insert(0, new_var)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "CALLER":  # get caller address
        # that is directly responsible for this execution
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["sender_address"])
    elif instr_parts[0] == "ORIGIN":  # get execution origination address
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["origin"])
    elif instr_parts[0] == "CALLVALUE":  # get value of this transaction
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["value"])
    elif instr_parts[0] == "CALLDATALOAD":  # from input data from environment
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            position = stack.pop(0)
            if USE_INPUT_STATE and global_state["callData"]:
                callData = global_state["callData"]
                start = position * 2
                end = start + 64
                while (end > len(callData)):
                    # append with zeros if insufficient length
                    callData = callData + "0"
                stack.insert(0, int(callData[start:end], 16))
            else:
                new_var_name = gen.gen_data_var(position)
                if new_var_name in path_conditions_and_vars:
                    new_var = path_conditions_and_vars[new_var_name]
                else:
                    new_var = BitVec(new_var_name, 256)
                    path_conditions_and_vars[new_var_name] = new_var
                stack.insert(0, new_var)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "CALLDATASIZE":  # from input data from environment
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, len(global_state["callData"])/2)
    elif instr_parts[0] == "CALLDATACOPY":  # Copy input data to memory
        #  TODO: Don't know how to simulate this yet
        if len(stack) > 2:
            global_state["pc"] = global_state["pc"] + 1
            stack.pop(0)
            stack.pop(0)
            stack.pop(0)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "CODESIZE":
        if sys.argv[1].endswith('.disasm'):
            evm_file_name = sys.argv[1][:-7]
        else:
            evm_file_name = sys.argv[1]
        with open(evm_file_name, 'r') as evm_file:
           evm = evm_file.read()[:-1]
           code_size = len(evm)/2
           stack.insert(0, code_size)
    elif instr_parts[0] == "CODECOPY":  # Copy code running in current env to memory
        #  TODO: Don't know how to simulate this yet
        # Need an example to test
        if len(stack) > 2:
            global_state["pc"] = global_state["pc"] + 1
            stack.pop(0)
            stack.pop(0)
            stack.pop(0)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "GASPRICE":
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["gas_price"])
    elif instr_parts[0] == "EXTCODESIZE":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            address = stack.pop(0)
            if isReal(address) and USE_GLOBAL_BLOCKCHAIN:
                code = data_source.getCode(address)
                stack.insert(0, len(code)/2)
            else:
                #not handled yet
                stack.insert(0, 0)
        else:
            raise ValueError('STACK underflow')
    #
    #  40s: Block Information
    #
    elif instr_parts[0] == "BLOCKHASH":  # information from block header
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            stack.pop(0)
            new_var_name = "IH_blockhash"
            if new_var_name in path_conditions_and_vars:
                new_var = path_conditions_and_vars[new_var_name]
            else:
                new_var = BitVec(new_var_name, 256)
                path_conditions_and_vars[new_var_name] = new_var
            stack.insert(0, new_var)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "COINBASE":  # information from block header
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentCoinbase"])
    elif instr_parts[0] == "TIMESTAMP":  # information from block header
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentTimestamp"])
    elif instr_parts[0] == "NUMBER":  # information from block header
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentNumber"])
    elif instr_parts[0] == "DIFFICULTY":  # information from block header
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentDifficulty"])
    elif instr_parts[0] == "GASLIMIT":  # information from block header
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["currentGasLimit"])
    #
    #  50s: Stack, Memory, Storage, and Flow Information
    #
    elif instr_parts[0] == "POP":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            stack.pop(0)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MLOAD":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            address = stack.pop(0)
            current_miu_i = global_state["miu_i"]
            if isinstance(address, (int, long)) and address in mem:
                temp = long(math.ceil((address + 32) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp
                value = mem[address]
                stack.insert(0, value)
                if PRINT_MODE: print "temp: " + str(temp)
                if PRINT_MODE: print "current_miu_i: " + str(current_miu_i)
            else:
                temp = ((address + 31) / 32) + 1
                if isinstance(current_miu_i, (int, long)):
                    current_miu_i = BitVecVal(current_miu_i, 256)
                expression = current_miu_i < temp
                solver.push()
                solver.add(expression)
                if solver.check() != unsat:
                    # this means that it is possibly that current_miu_i < temp
                    if expression == True:
                        current_miu_i = temp
                    else:
                        current_miu_i = If(expression,temp,current_miu_i)
                solver.pop()
                new_var_name = gen.gen_mem_var(address)
                if new_var_name in path_conditions_and_vars:
                    new_var = path_conditions_and_vars[new_var_name]
                else:
                    new_var = BitVec(new_var_name, 256)
                    path_conditions_and_vars[new_var_name] = new_var
                stack.insert(0, new_var)
                if isinstance(address, (int, long)):
                    mem[address] = new_var
                else:
                    mem[str(address)] = new_var
                if PRINT_MODE: print "temp: " + str(temp)
                if PRINT_MODE: print "current_miu_i: " + str(current_miu_i)
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MSTORE":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            stored_address = stack.pop(0)
            stored_value = stack.pop(0)
            current_miu_i = global_state["miu_i"]
            if isinstance(stored_address, (int, long)):
                temp = long(math.ceil((stored_address + 32) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp
                mem[stored_address] = stored_value  # note that the stored_value could be symbolic
                if PRINT_MODE: print "temp: " + str(temp)
                if PRINT_MODE: print "current_miu_i: " + str(current_miu_i)
            else:
                if PRINT_MODE: print "Debugging... temp " + str(stored_address)
                temp = ((stored_address + 31) / 32) + 1
                if isinstance(current_miu_i, (int, long)):
                    current_miu_i = BitVecVal(current_miu_i, 256)
                if PRINT_MODE: print "current_miu_i: " + str(current_miu_i)
                expression = current_miu_i < temp
                if PRINT_MODE: print "Expression: " + str(expression)
                solver.push()
                solver.add(expression)
                if solver.check() != unsat:
                    # this means that it is possibly that current_miu_i < temp
                    if expression == True:
                        current_miu_i = temp
                    else:
                        current_miu_i = If(expression,temp,current_miu_i)
                solver.pop()
                mem.clear()  # very conservative
                mem[str(stored_address)] = stored_value
                if PRINT_MODE: print "temp: " + str(temp)
                if PRINT_MODE: print "current_miu_i: " + str(current_miu_i)
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MSTORE8":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            stored_address = stack.pop(0)
            temp_value = stack.pop(0)
            stored_value = temp_value % 256  # get the least byte
            current_miu_i = global_state["miu_i"]
            if isinstance(stored_address, (int, long)):
                temp = long(math.ceil((stored_address + 1) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp
                mem[stored_address] = stored_value  # note that the stored_value could be symbolic
            else:
                temp = (stored_address / 32) + 1
                if isinstance(current_miu_i, (int, long)):
                    current_miu_i = BitVecVal(current_miu_i, 256)
                expression = current_miu_i < temp
                solver.push()
                solver.add(expression)
                if solver.check() != unsat:
                    # this means that it is possibly that current_miu_i < temp
                    if expression == True:
                        current_miu_i = temp
                    else:
                        current_miu_i = If(expression,temp,current_miu_i)
                solver.pop()
                mem.clear()  # very conservative
                mem[str(stored_address)] = stored_value
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SLOAD":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            address = stack.pop(0)
            if isinstance(address, (int, long)):
                if address in global_state["Ia"]:
                    value = global_state["Ia"][address]
                    stack.insert(0, value)
                else:
                    stack.insert(0, 0)
            else:
                new_var_name = gen.gen_owner_store_var(address)
                if new_var_name in path_conditions_and_vars:
                    new_var = path_conditions_and_vars[new_var_name]
                else:
                    new_var = BitVec(new_var_name, 256)
                    path_conditions_and_vars[new_var_name] = new_var
                stack.insert(0, new_var)
                if isinstance(address, (int, long)):
                    global_state["Ia"][address] = new_var
                else:
                    global_state["Ia"][str(address)] = new_var
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SSTORE":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            stored_address = stack.pop(0)
            stored_value = stack.pop(0)
            if isinstance(stored_address, (int, long)):
                global_state["Ia"][stored_address] = stored_value  # note that the stored_value could be unknown
            else:
                global_state["Ia"].clear()  # very conservative
                global_state["Ia"][str(stored_address)] = stored_value  # note that the stored_value could be unknown
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "JUMP":
        if len(stack) > 0:
            target_address = stack.pop(0)
            if isSymbolic(target_address):
                target_address = int( str( simplify(target_address) ) )
            vertices[start].set_jump_target(target_address)
            if target_address not in edges[start]:
                edges[start].append(target_address)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "JUMPI":
        # We need to prepare two branches
        if len(stack) > 1:
            target_address = stack.pop(0)
            if isSymbolic(target_address):
                target_address = int( str( simplify(target_address) ) )
            vertices[start].set_jump_target(target_address)
            flag = stack.pop(0)
            branch_expression = (BitVecVal(0, 1) == BitVecVal(1, 1))
            if isinstance(flag, (int, long)):
                if flag != 0:
                    branch_expression = True
            else:
                branch_expression = (0 != flag)
            vertices[start].set_branch_expression(branch_expression)
            if target_address not in edges[start]:
                edges[start].append(target_address)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "PC":
        stack.insert(0, global_state["pc"])
        global_state["pc"] = global_state["pc"] + 1
    elif instr_parts[0] == "MSIZE":
        global_state["pc"] = global_state["pc"] + 1
        msize = 32 * global_state["miu_i"]
        stack.insert(0, msize)
    elif instr_parts[0] == "GAS":
        # In general, we do not have this precisely. It depends on both
        # the initial gas and the amount has been depleted
        # we need o think about this in the future, in case precise gas
        # can be tracked
        global_state["pc"] = global_state["pc"] + 1
        new_var_name = gen.gen_gas_var()
        new_var = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "JUMPDEST":
        # Literally do nothing
        global_state["pc"] = global_state["pc"] + 1
        pass
    #
    #  60s & 70s: Push Operations
    #
    elif instr_parts[0].startswith('PUSH', 0):  # this is a push instruction
        position = int(instr_parts[0][4:], 10)
        global_state["pc"] = global_state["pc"] + 1 + position
        pushed_value = int(instr_parts[1], 16)
        stack.insert(0, pushed_value)
        if UNIT_TEST == 3: # test evm symbolic
            stack[0] = BitVecVal(stack[0], 256)
    #
    #  80s: Duplication Operations
    #
    elif instr_parts[0].startswith("DUP", 0):
        global_state["pc"] = global_state["pc"] + 1
        position = int(instr_parts[0][3:], 10) - 1
        if len(stack) > position:
            duplicate = stack[position]
            stack.insert(0, duplicate)
        else:
            raise ValueError('STACK underflow')

    #
    #  90s: Swap Operations
    #
    elif instr_parts[0].startswith("SWAP", 0):
        global_state["pc"] = global_state["pc"] + 1
        position = int(instr_parts[0][4:], 10)
        if len(stack) > position:
            temp = stack[position]
            stack[position] = stack[0]
            stack[0] = temp
        else:
            raise ValueError('STACK underflow')

    #
    #  a0s: Logging Operations
    #
    elif instr_parts[0] in ("LOG0", "LOG1", "LOG2", "LOG3", "LOG4"):
        global_state["pc"] = global_state["pc"] + 1
        # We do not simulate these logging operations
        num_of_pops = 2 + int(instr_parts[0][3:])
        while num_of_pops > 0:
            stack.pop(0)
            num_of_pops -= 1

    #
    #  f0s: System Operations
    #
    elif instr_parts[0] == "CALL":
        # TODO: Need to handle miu_i
        if len(stack) > 6:
            global_state["pc"] = global_state["pc"] + 1
            outgas = stack.pop(0)
            recipient = stack.pop(0)
            transfer_amount = stack.pop(0)
            start_data_input = stack.pop(0)
            size_data_input = stack.pop(0)
            start_data_output = stack.pop(0)
            size_data_ouput = stack.pop(0)
            # in the paper, it is shaky when the size of data output is
            # min of stack[6] and the | o |

            if isinstance(transfer_amount, (int, long)):
                if transfer_amount == 0:
                    stack.insert(0, 1)   # x = 0
                    return

            # Let us ignore the call depth
            balance_ia = global_state["balance"]["Ia"]
            is_enough_fund = (balance_ia < transfer_amount)
            solver.push()
            solver.add(is_enough_fund)

            if solver.check() == unsat:
                # this means not enough fund, thus the execution will result in exception
                solver.pop()
                stack.insert(0, 0)   # x = 0
            else:
                # the execution is possibly okay
                stack.insert(0, 1)   # x = 1
                solver.pop()
                solver.add(is_enough_fund)
                path_conditions_and_vars["path_condition"].append(is_enough_fund)
                new_balance_ia = (balance_ia - transfer_amount)
                global_state["balance"]["Ia"] = new_balance_ia
                address_is = path_conditions_and_vars["Is"]
                address_is = (address_is & CONSTANT_ONES_159)
                boolean_expression = (recipient != address_is)
                solver.push()
                solver.add(boolean_expression)
                if solver.check() == unsat:
                    solver.pop()
                    new_balance_is = (global_state["balance"]["Is"] + transfer_amount)
                    global_state["balance"]["Is"] = new_balance_is
                else:
                    solver.pop()
                    if isinstance(recipient, (int, long)):
                        new_address_name = "concrete_address_" + str(recipient)
                    else:
                        new_address_name = gen.gen_arbitrary_address_var()
                    old_balance_name = gen.gen_arbitrary_var()
                    old_balance = BitVec(old_balance_name, 256)
                    path_conditions_and_vars[old_balance_name] = old_balance
                    constraint = (old_balance >= 0)
                    solver.add(constraint)
                    path_conditions_and_vars["path_condition"].append(constraint)
                    new_balance = (old_balance + transfer_amount)
                    global_state["balance"][new_address_name] = new_balance
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "CALLCODE":
        # TODO: Need to handle miu_i
        if len(stack) > 6:
            global_state["pc"] = global_state["pc"] + 1
            outgas = stack.pop(0)
            stack.pop(0) # this is not used as recipient
            transfer_amount = stack.pop(0)
            start_data_input = stack.pop(0)
            size_data_input = stack.pop(0)
            start_data_output = stack.pop(0)
            size_data_ouput = stack.pop(0)
            # in the paper, it is shaky when the size of data output is
            # min of stack[6] and the | o |

            if isinstance(transfer_amount, (int, long)):
                if transfer_amount == 0:
                    stack.insert(0, 1)   # x = 0
                    return

            # Let us ignore the call depth
            balance_ia = global_state["balance"]["Ia"]
            is_enough_fund = (balance_ia < transfer_amount)
            solver.push()
            solver.add(is_enough_fund)

            if solver.check() == unsat:
                # this means not enough fund, thus the execution will result in exception
                solver.pop()
                stack.insert(0, 0)   # x = 0
            else:
                # the execution is possibly okay
                stack.insert(0, 1)   # x = 1
                solver.pop()
                solver.add(is_enough_fund)
                path_conditions_and_vars["path_condition"].append(is_enough_fund)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "RETURN":
        # TODO: Need to handle miu_i
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            stack.pop(0)
            stack.pop(0)
            # TODO
            pass
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SUICIDE":
        global_state["pc"] = global_state["pc"] + 1
        recipient = stack.pop(0)
        transfer_amount = global_state["balance"]["Ia"]
        global_state["balance"]["Ia"] = 0
        if isinstance(recipient, (int, long)):
            new_address_name = "concrete_address_" + str(recipient)
        else:
            new_address_name = gen.gen_arbitrary_address_var()
        old_balance_name = gen.gen_arbitrary_var()
        old_balance = BitVec(old_balance_name, 256)
        path_conditions_and_vars[old_balance_name] = old_balance
        constraint = (old_balance >= 0)
        solver.add(constraint)
        path_conditions_and_vars["path_condition"].append(constraint)
        new_balance = (old_balance + transfer_amount)
        global_state["balance"][new_address_name] = new_balance
        # TODO
        return

    else:
        if PRINT_MODE: print "UNKNOWN INSTRUCTION: " + instr_parts[0]
        if UNIT_TEST == 2 or UNIT_TEST == 3:
            logging.exception("Unkown instruction: %s" % instr_parts[0])
            exit(UNKOWN_INSTRUCTION)
        raise Exception('UNKNOWN INSTRUCTION: ' + instr_parts[0])

    print_state(start, stack, mem, global_state)

def check_callstack_attack(disasm):
    problematic_instructions = ['CALL', 'CALLCODE']
    for i in xrange(0, len(disasm)):
        instruction = disasm[i]
        if instruction[1] in problematic_instructions:
            error = True
            for j in xrange(i+1, len(disasm)):
                if disasm[j][1] in problematic_instructions:
                    break
                if disasm[j][1] == 'ISZERO':
                    error = False
                    break
            if error == True: return True
    return False

def run_callstack_attack():
    disasm_data = open(sys.argv[1]).read()
    instr_pattern = r"([\d]+): ([A-Z]+)([\d]?)(?: 0x)?(\S+)?"
    instructions = re.findall(instr_pattern, disasm_data)
    result = check_callstack_attack(instructions)

    if not isTesting(): print "\t  CallStack Attack: \t %s" % result
    results['callstack'] = result

def print_state(block_address, stack, mem, global_state):
    if PRINT_MODE: print "STACK: " + str(stack)
    if PRINT_MODE: print "MEM: " + str(mem)
    if PRINT_MODE: print "GLOBAL STATE: " + str(global_state)

def contains_only_concrete_values(stack):
    for element in stack:
        if isSymbolic(element):
            return False
    return True

def to_symbolic(number):
    if isReal(number):
        return BitVecVal(number, 256)
    return number

if __name__ == '__main__':
    main()
