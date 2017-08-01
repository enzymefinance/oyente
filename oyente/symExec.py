import tokenize
import zlib, base64
from tokenize import NUMBER, NAME, NEWLINE
import re
import math
import sys
import atexit
import pickle
import json
import traceback
import signal
import time
import logging
from collections import namedtuple
from z3 import *

from vargenerator import *
from ethereum_data import *
from basicblock import BasicBlock
from assertion import Assertion
from analysis import *
import global_params

from test_evm.global_test_params import (TIME_OUT, UNKOWN_INSTRUCTION,
                                         EXCEPTION, PICKLE_PATH)


log = logging.getLogger(__name__)

UNSIGNED_BOUND_NUMBER = 2**256 - 1
CONSTANT_ONES_159 = BitVecVal((1 << 160) - 1, 256)


def initGlobalVars():
    global solver
    # Z3 solver
    solver = Solver()
    solver.set("timeout", global_params.TIMEOUT)

    global results
    results = {}

    # capturing the last statement of each basic block
    global end_ins_dict
    end_ins_dict = {}

    # capturing all the instructions, keys are corresponding addresses
    global instructions
    instructions = {}

    global source
    source = ""

    global sourceLocations
    sourceLocations = {}

    # capturing the "jump type" of each basic block
    global jump_type
    jump_type = {}

    global vertices
    vertices = {}

    global edges
    edges = {}

    global assertions
    assertions = []

    global visited_edges
    visited_edges = {}

    global money_flow_all_paths
    money_flow_all_paths = []

    global reentrancy_all_paths
    reentrancy_all_paths = []

    global data_flow_all_paths
    data_flow_all_paths = [[], []] # store all storage addresses

    # store the path condition corresponding to each path in money_flow_all_paths
    global path_conditions
    path_conditions = []

    # store global variables, e.g. storage, balance of all paths
    global all_gs
    all_gs = []

    global total_no_of_paths
    total_no_of_paths = 0

    # to generate names for symbolic variables
    global gen
    gen = Generator()

    global data_source
    if global_params.USE_GLOBAL_BLOCKCHAIN:
        data_source = EthereumData()

    global log_file
    log_file = open(c_name + '.log', "w")

    global rfile
    if global_params.REPORT_MODE:
        rfile = open(c_name + '.report', 'w')

def check_unit_test_file():
    if global_params.UNIT_TEST == 1:
        try:
            open('unit_test.json', 'r')
        except:
            log.critical("Could not open result file for unit test")
            exit()

def isTesting():
    return global_params.UNIT_TEST != 0

# A simple function to compare the end stack with the expected stack
# configurations specified in a test file
def compare_stack_unit_test(stack):
    try:
        size = int(result_file.readline())
        content = result_file.readline().strip('\n')
        if size == len(stack) and str(stack) == content:
            log.debug("PASSED UNIT-TEST")
        else:
            log.warning("FAILED UNIT-TEST")
            log.warning("Expected size %d, Resulted size %d", size, len(stack))
            log.warning("Expected content %s \nResulted content %s", content, str(stack))
    except Exception as e:
        log.warning("FAILED UNIT-TEST")
        log.warning(e.message)

def compare_storage_and_gas_unit_test(global_state, analysis):
    unit_test = pickle.load(open(PICKLE_PATH, 'rb'))
    test_status = unit_test.compare_with_symExec_result(global_state, analysis)
    exit(test_status)

def handler(signum, frame):
    if global_params.UNIT_TEST == 2 or global_params.UNIT_TEST == 3:
        exit(TIME_OUT)
    detect_bugs()
    raise Exception("timeout")

def detect_bugs():
    global assertions
    global results

    if global_params.REPORT_MODE:
        rfile.write(str(total_no_of_paths) + "\n")
    detect_money_concurrency()
    detect_time_dependency()
    stop = time.time()
    if global_params.REPORT_MODE:
        rfile.write(str(stop-start))
        rfile.close()
    if global_params.DATA_FLOW:
        detect_data_concurrency()
        detect_data_money_concurrency()
    log.debug("Results for Reentrancy Bug: " + str(reentrancy_all_paths))
    reentrancy_bug_found = any([v for sublist in reentrancy_all_paths for v in sublist])
    if not isTesting():
        log.info("\t  Reentrancy bug exists: %s", str(reentrancy_bug_found))
    results['reentrancy'] = reentrancy_bug_found

    if global_params.CHECK_ASSERTIONS:
        check_assertions()
        assertion_fails = [assertion for assertion in assertions if assertion.is_violated()]
        is_fail = len(assertion_fails) > 0
        results['assertion_failure'] = is_fail
        if not isTesting():
            log.info("\t  Assertion fails: \t %s", str(is_fail))
        if not global_params.WEB:
            for asrt in assertion_fails:
                asrt.display()

def check_assertions():
    global assertions
    global c_name_sol

    assertions_fail = [assertion for assertion in assertions if assertion.is_violated()]
    if len(assertions_fail) == 0:
        return

    fun_names = retrieveFunctionNames(c_name_sol)
    fun_sigs = retrieveFunctionSignatures(c_name_sol)

    interpret_assertion_bug(fun_sigs, fun_names)


def interpret_assertion_bug(fun_sigs, fun_names):
    global assertions
    global edges
    global vertices
    global instructions
    global results

    state = 0
    fsig = None
    functions = {}
    for instr in instructions:
        if state == 0:
            for sig in fun_sigs:
                if instructions[instr].startswith("PUSH4 " + sig):
                    # There will be a test on the function signature,
                    # we have to look for the next EQ
                    state = 1
                    fsig = sig
                    break
        elif state == 1 and instructions[instr].startswith("EQ"):
            # We found the EQ, so next should be PUSH
            state = 2
        elif state == 2 and instructions[instr].startswith("PUSH"):
            # We have the address of the beginning of the function
            hexaddr = instructions[instr].split("0x")[1].replace(' ', '')
            faddr = int(hexaddr, 16)
            functions[faddr] = fun_sigs[fsig]
            state = 0

    assertion_fails = [assertion for assertion in assertions if assertion.is_violated()]
    for asrt in assertion_fails:
        interpret_assertion(asrt, functions, fun_names)


def interpret_assertion(asrt, functions, fun_names):
    global vertices

    for i in range(len(asrt.path) - 1, 0, -1):
        block = asrt.path[i]
        if block in functions:
            block_fun = functions[block]
            if block_fun.split('(')[0] in fun_names:
                asrt.set_function(block_fun)
            else:
                asrt.set_violated(False)
            break


def main(contract, contract_sol):
    global c_name
    global c_name_sol
    c_name = contract
    c_name_sol = contract_sol

    check_unit_test_file()
    initGlobalVars()
    set_cur_file(c_name[4:] if len(c_name) > 5 else c_name)
    start = time.time()
    signal.signal(signal.SIGALRM, handler)
    if global_params.UNIT_TEST == 2 or global_params.UNIT_TEST == 3:
        global_params.GLOBAL_TIMEOUT = global_params.GLOBAL_TIMEOUT_TEST
    signal.alarm(global_params.GLOBAL_TIMEOUT)
    atexit.register(closing_message)
    if global_params.WEB:
        atexit.register(results_for_web)

    log.info("Running, please wait...")

    global results

    if not isTesting():
        log.info("\t============ Results ===========")

    log.debug("Checking for Callstack attack...")
    run_callstack_attack()

    try:
        build_cfg_and_analyze()
        log.debug("Done Symbolic execution")
    except Exception as e:
        if global_params.UNIT_TEST == 2 or global_params.UNIT_TEST == 3:
            log.exception(e)
            exit(EXCEPTION)
        traceback.print_exc()
        raise e
    signal.alarm(0)

    detect_bugs()


def results_for_web():
    global results
    if not results.has_key("callstack"):
        results["callstack"] = False
    if not results.has_key("time_dependency"):
        results["time_dependency"] = False
    if not results.has_key("reentrancy"):
        results["reentrancy"] = False
    if not results.has_key("concurrency"):
        results["concurrency"] = False

    print "Callstack Attack:", results['callstack']
    print "Time Dependency:", results['time_dependency']
    print "Reentrancy bug:", results['reentrancy']
    print "Concurrency:", results['concurrency']

    if global_params.CHECK_ASSERTIONS:
        if not results.has_key("assertion_failure"):
            results["assertion_failure"] = False
        print "Assertion failure:", results['assertion_failure']
        assertion_fails = [assertion for assertion in assertions if assertion.is_violated()]
        for asrt in assertion_fails:
            print asrt.display_on_web()


def closing_message():
    log.info("\t====== Analysis Completed ======")
    if global_params.STORE_RESULT:
        result_file = c_name + '.json'
        with open(result_file, 'w') as of:
            of.write(json.dumps(results, indent=1))
        log.info("Wrote results to %s.", result_file)

def change_format():
    with open(c_name) as disasm_file:
        file_contents = disasm_file.readlines()
        i = 0
        firstLine = file_contents[0].strip('\n')
        for line in file_contents:
            line = line.replace('SELFDESTRUCT', 'SUICIDE')
            line = line.replace('Missing opcode 0xfd', 'REVERT')
            line = line.replace('Missing opcode 0xfe', 'ASSERTFAIL')
            line = line.replace('Missing opcode', 'INVALID')
            line = line.replace(':', '')
            lineParts = line.split(' ')
            try: # removing initial zeroes
                lineParts[0] = str(int(lineParts[0]))

            except:
                lineParts[0] = lineParts[0]
            lineParts[-1] = lineParts[-1].strip('\n')
            try: # adding arrow if last is a number
                lastInt = lineParts[-1]
                if(int(lastInt, 16) or int(lastInt, 16) == 0) and len(lineParts) > 2:
                    lineParts[-1] = "=>"
                    lineParts.append(lastInt)
            except Exception:
                pass
            file_contents[i] = ' '.join(lineParts)
            i = i + 1
        file_contents[0] = firstLine
        file_contents[-1] += '\n'

    with open(c_name, 'w') as disasm_file:
        disasm_file.write("\n".join(file_contents))


def build_cfg_and_analyze():
    change_format()
    with open(c_name, 'r') as disasm_file:
        disasm_file.readline()  # Remove first line
        tokens = tokenize.generate_tokens(disasm_file.readline)
        collect_vertices(tokens)
        construct_bb()
        construct_static_edges()
        full_sym_exec()  # jump targets are constructed on the fly


# Detect if a money flow depends on the timestamp
def detect_time_dependency():
    global results
    TIMESTAMP_VAR = "IH_s"
    is_dependant = False
    index = 0
    if global_params.PRINT_PATHS:
        log.info("ALL PATH CONDITIONS")
    for cond in path_conditions:
        index += 1
        if global_params.PRINT_PATHS:
            log.info("PATH " + str(index) + ": " + str(cond))
        list_vars = []
        for expr in cond:
            if is_expr(expr):
                list_vars += get_vars(expr)
        set_vars = set(i.decl().name() for i in list_vars)
        if TIMESTAMP_VAR in set_vars:
            is_dependant = True
            break

    if not isTesting():
        log.info("\t  Time Dependency: \t %s", is_dependant)
    results['time_dependency'] = is_dependant

    if global_params.REPORT_MODE:
        file_name = c_name.split("/")[len(c_name.split("/"))-1].split(".")[0]
        report_file = file_name + '.report'
        with open(report_file, 'w') as rfile:
            if is_dependant:
                rfile.write("yes\n")
            else:
                rfile.write("no\n")


# detect if two paths send money to different people
def detect_money_concurrency():
    global results
    n = len(money_flow_all_paths)
    for i in range(n):
        log.debug("Path " + str(i) + ": " + str(money_flow_all_paths[i]))
        log.debug(all_gs[i])
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
                if global_params.CHECK_CONCURRENCY_FP and \
                        is_false_positive(i-1, j, all_gs, path_conditions) and \
                        is_false_positive(j, i-1, all_gs, path_conditions):
                    false_positive.append([i-1, j])

    # if PRINT_MODE: print "All false positive cases: ", false_positive
    log.debug("Concurrency in paths: ")
    if len(concurrency_paths) > 0:
        if not isTesting():
            log.info("\t  Concurrency found in paths: %s", str(concurrency_paths))
        results['concurrency'] = True
    else:
        if not isTesting():
            log.info("\t  Concurrency Bug: \t False")
        results['concurrency'] = False
    if global_params.REPORT_MODE:
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
    log.debug("data concurrency in storage " + str(concurrency_addr))

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
    log.debug("Concurrency in data that affects money flow: " + str(set(concurrency_addr)))


def print_cfg():
    for block in vertices.values():
        block.display()
    log.debug(str(edges))


# 1. Parse the disassembled file
# 2. Then identify each basic block (i.e. one-in, one-out)
# 3. Store them in vertices
def collect_vertices(tokens):
    global end_ins_dict
    global instructions
    global sourceLocations
    global jump_type
    global c_name_sol

    current_ins_address = 0
    last_ins_address = 0
    is_new_line = True
    current_block = 0
    current_line_content = ""
    wait_for_push = False
    is_new_block = False
    locations = retrieveSourceLocations(c_name_sol)

    count = 0
    for tok_type, tok_string, (srow, scol), _, line_number in tokens:
        if wait_for_push is True:
            push_val = ""
            for ptok_type, ptok_string, _, _, _ in tokens:
                if ptok_type == NEWLINE:
                    is_new_line = True
                    current_line_content += push_val + ' '
                    instructions[current_ins_address] = current_line_content
                    sourceLocations[current_ins_address] = locations[count]
                    count += 1
                    log.debug(current_line_content)
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
                log.critical("ERROR when parsing row %d col %d", srow, scol)
                quit()
            is_new_line = False
            if is_new_block:
                current_block = current_ins_address
                is_new_block = False
            continue
        elif tok_type == NEWLINE:
            is_new_line = True
            log.debug(current_line_content)
            instructions[current_ins_address] = current_line_content
            try:
                sourceLocations[current_ins_address] = locations[count]
                count += 1
            except:
                pass
            current_line_content = ""
            continue
        elif tok_type == NAME:
            if tok_string == "JUMPDEST":
                if last_ins_address not in end_ins_dict:
                    end_ins_dict[current_block] = last_ins_address
                current_block = current_ins_address
                is_new_block = False
            elif tok_string == "STOP" or tok_string == "RETURN" or tok_string == "SUICIDE" or tok_string == "REVERT" or tok_string == "ASSERTFAIL":
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
        log.debug("current block: %d", current_block)
        log.debug("last line: %d", current_ins_address)
        end_ins_dict[current_block] = current_ins_address

    if current_block not in jump_type:
        jump_type[current_block] = "terminal"

    for key in end_ins_dict:
        if key not in jump_type:
            jump_type[key] = "falls_to"


def construct_bb():
    global vertices
    global edges
    sorted_addresses = sorted(instructions.keys())
    size = len(sorted_addresses)
    for key in end_ins_dict:
        end_address = end_ins_dict[key]
        block = BasicBlock(key, end_address)
        if key not in instructions:
            continue
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
    global vertices
    global edges
    key_list = sorted(jump_type.keys())
    length = len(key_list)
    for i, key in enumerate(key_list):
        if jump_type[key] != "terminal" and jump_type[key] != "unconditional" and i+1 < length:
            target = key_list[i+1]
            edges[key].append(target)
            vertices[key].set_falls_to(target)


def get_init_global_state(path_conditions_and_vars):
    global_state = {"balance" : {}, "pc": 0}
    init_is = init_ia = deposited_value = sender_address = receiver_address = gas_price = origin = currentCoinbase = currentNumber = currentDifficulty = currentGasLimit = callData = None

    if global_params.INPUT_STATE:
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
            if state["Ia"]["storage"]:
                storage_dict = state["Ia"]["storage"]
                global_state["Ia"] = {}
                for key in storage_dict:
                    global_state["Ia"][int(key, 16)] = int(storage_dict[key], 16)

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

    new_var_name = "IH_s"
    currentTimestamp = BitVec(new_var_name, 256)
    path_conditions_and_vars[new_var_name] = currentTimestamp

    # the state of the current current contract
    if "Ia" not in global_state:
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
    memory = [] # This memory is used only for the process of finding the position of a mapping variable in storage. In this process, memory is used for hashing methods
    sha3_list = {} # mapping a lengthy position string in SHA3 opcode to an arbitrary BitVec variable for easier debug

    # this is init global state for this particular execution
    global_state = get_init_global_state(path_conditions_and_vars)
    analysis = init_analysis()
    return sym_exec_block(0, 0, visited, depth, stack, mem, memory, global_state, sha3_list, path_conditions_and_vars, analysis, [], [])


# Symbolically executing a block from the start address
def sym_exec_block(block, pre_block, visited, depth, stack, mem, memory, global_state, sha3_list, path_conditions_and_vars, analysis, path, models):
    global solver
    global visited_edges
    global money_flow_all_paths
    global data_flow_all_paths
    global path_conditions
    global all_gs
    global results
    Edge = namedtuple("Edge", ["v1", "v2"]) # Factory Function for tuples is used as dictionary key
    if block < 0:
        log.debug("UNKNOWN JUMP ADDRESS. TERMINATING THIS PATH")
        return ["ERROR"]

    log.debug("Reach block address %d \n", block)
    log.debug("STACK: " + str(stack))

    current_edge = Edge(pre_block, block)
    if visited_edges.has_key(current_edge):
        updated_count_number = visited_edges[current_edge] + 1
        visited_edges.update({current_edge: updated_count_number})
    else:
        visited_edges.update({current_edge: 1})

    if visited_edges[current_edge] > global_params.LOOP_LIMIT:
        log.debug("Overcome a number of loop limit. Terminating this path ...")
        return stack

    current_gas_used = analysis["gas"]
    if current_gas_used > global_params.GAS_LIMIT:
        log.debug("Run out of gas. Terminating this path ... ")
        return stack

    # Execute every instruction, one at a time
    try:
        block_ins = vertices[block].get_instructions()
    except KeyError:
        log.debug("This path results in an exception, possibly an invalid jump address")
        return ["ERROR"]

    for instr in block_ins:
        sym_exec_ins(block, instr, stack, mem, memory, global_state, sha3_list, path_conditions_and_vars, analysis, path, models)

    # Mark that this basic block in the visited blocks
    visited.append(block)
    depth += 1

    reentrancy_all_paths.append(analysis["reentrancy_bug"])
    if analysis["money_flow"] not in money_flow_all_paths:
        money_flow_all_paths.append(analysis["money_flow"])
        path_conditions.append(path_conditions_and_vars["path_condition"])
        all_gs.append(copy_global_values(global_state))
    if global_params.DATA_FLOW:
        if analysis["sload"] not in data_flow_all_paths[0]:
            data_flow_all_paths[0].append(analysis["sload"])
        if analysis["sstore"] not in data_flow_all_paths[1]:
            data_flow_all_paths[1].append(analysis["sstore"])

    # Go to next Basic Block(s)
    if jump_type[block] == "terminal" or depth > global_params.DEPTH_LIMIT:
        log.debug("TERMINATING A PATH ...")
        display_analysis(analysis)
        global total_no_of_paths
        total_no_of_paths += 1
        if global_params.UNIT_TEST == 1:
            compare_stack_unit_test(stack)
        if global_params.UNIT_TEST == 2 or global_params.UNIT_TEST == 3:
            compare_storage_and_gas_unit_test(global_state, analysis)

    elif jump_type[block] == "unconditional":  # executing "JUMP"
        successor = vertices[block].get_jump_target()
        visited1, stack1, mem1, memory1, global_state1, sha3_list1, path_conditions_and_vars1, analysis1 = copy_all(visited, stack, mem, memory, global_state, sha3_list, path_conditions_and_vars, analysis)
        global_state1["pc"] = successor
        sym_exec_block(successor, block, visited1, depth, stack1, mem1, memory1, global_state1, sha3_list1, path_conditions_and_vars1, analysis1, path + [block], models)
    elif jump_type[block] == "falls_to":  # just follow to the next basic block
        successor = vertices[block].get_falls_to()
        visited1, stack1, mem1, memory1, global_state1, sha3_list1, path_conditions_and_vars1, analysis1 = copy_all(visited, stack, mem, memory, global_state, sha3_list, path_conditions_and_vars, analysis)
        global_state1["pc"] = successor
        sym_exec_block(successor, block, visited1, depth, stack1, mem1, memory1, global_state1, sha3_list1, path_conditions_and_vars1, analysis1, path + [block], models)
    elif jump_type[block] == "conditional":  # executing "JUMPI"

        # A choice point, we proceed with depth first search

        branch_expression = vertices[block].get_branch_expression()

        log.debug("Branch expression: " + str(branch_expression))

        solver.push()  # SET A BOUNDARY FOR SOLVER
        solver.add(branch_expression)

        try:
            if solver.check() == unsat:
                log.debug("INFEASIBLE PATH DETECTED")
            else:
                left_branch = vertices[block].get_jump_target()
                visited1, stack1, mem1, memory1, global_state1, sha3_list1, path_conditions_and_vars1, analysis1 = copy_all(visited, stack, mem, memory, global_state, sha3_list, path_conditions_and_vars, analysis)
                global_state1["pc"] = left_branch
                path_conditions_and_vars1["path_condition"].append(branch_expression)
                try:
                    model = [solver.model()]
                except Exception as e:
                    model = []
                sym_exec_block(left_branch, block, visited1, depth, stack1, mem1, memory1, global_state1, sha3_list1, path_conditions_and_vars1, analysis1, path + [block], models + model)
        except Exception as e:
            log_file.write(str(e))
            traceback.print_exc()
            if not global_params.IGNORE_EXCEPTIONS:
                if str(e) == "timeout":
                    raise e

        solver.pop()  # POP SOLVER CONTEXT

        solver.push()  # SET A BOUNDARY FOR SOLVER
        negated_branch_expression = Not(branch_expression)
        solver.add(negated_branch_expression)

        log.debug("Negated branch expression: " + str(negated_branch_expression))

        try:
            if solver.check() == unsat:
                # Note that this check can be optimized. I.e. if the previous check succeeds,
                # no need to check for the negated condition, but we can immediately go into
                # the else branch
                log.debug("INFEASIBLE PATH DETECTED")
            else:
                right_branch = vertices[block].get_falls_to()
                visited1, stack1, mem1, memory1, global_state1, sha3_list1, path_conditions_and_vars1, analysis1 = copy_all(visited, stack, mem, memory, global_state, sha3_list, path_conditions_and_vars, analysis)
                global_state1["pc"] = right_branch
                path_conditions_and_vars1["path_condition"].append(negated_branch_expression)
                try:
                    model = [solver.model()]
                except Exception as e:
                    model = []
                sym_exec_block(right_branch, block, visited1, depth, stack1, mem1, memory1, global_state1, sha3_list1, path_conditions_and_vars1, analysis1, path + [block], models + model)
        except Exception as e:
            log_file.write(str(e))
            traceback.print_exc()
            if not global_params.IGNORE_EXCEPTIONS:
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
def sym_exec_ins(start, instr, stack, mem, memory, global_state, sha3_list, path_conditions_and_vars, analysis, path, models):
    global solver
    global vertices
    global edges
    global assertions
    global c_name_sol

    instr_parts = str.split(instr, ' ')

    if instr_parts[0] == "INVALID":
        return
    elif instr_parts[0] == "ASSERTFAIL":
        # We only consider assertions blocks that already start with ASSERTFAIL,
        # without any JUMPDEST
        if instr == vertices[start].get_instructions()[0]:
            from_block = path[-1]
            block_instrs = vertices[from_block].get_instructions()
            is_init_callvalue = True
            if len(block_instrs) < 5:
                is_init_callvalue = False
            else:
                instrs = ["JUMPDEST", "CALLVALUE", "ISZERO", "PUSH", "JUMPI"]
                for i in range(0, 5):
                    if not block_instrs[i].startswith(instrs[i]):
                        is_init_callvalue = False
                        break
            if from_block != 0 and not is_init_callvalue:
                assertion = Assertion(start)
                assertion.set_violated(True)
                assertion.set_model(models[-1])
                assertion.set_path(path + [start])
                assertion.set_sym(path_conditions_and_vars)
                position = get_position(c_name_sol, source, sourceLocations, global_state["pc"])
                assertion.set_position(position)
                assertions.append(assertion)
        return

    # collecting the analysis result by calling this skeletal function
    # this should be done before symbolically executing the instruction,
    # since SE will modify the stack and mem
    update_analysis(analysis, instr_parts[0], stack, mem, global_state, path_conditions_and_vars, solver)

    log.debug("==============================")
    log.debug("EXECUTING: " + instr)

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
            if isReal(first) and isSymbolic(second):
                first = BitVecVal(first, 256)
                computed = first + second
            elif isSymbolic(first) and isReal(second):
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
            if isReal(first) and isSymbolic(second):
                first = BitVecVal(first, 256)
            elif isSymbolic(first) and isReal(second):
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
            if isReal(first) and isSymbolic(second):
                first = BitVecVal(first, 256)
                computed = first - second
            elif isSymbolic(first) and isReal(second):
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
            if isAllReal(first, second):
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
            if isAllReal(first, second):
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
                solver.add(Not(second == 0))
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
            if isAllReal(first, second):
                if second == 0:
                    computed = 0
                else:
                    first = to_unsigned(first)
                    second = to_unsigned(second)
                    computed = first % second & UNSIGNED_BOUND_NUMBER

            else:
                first = to_symbolic(first)
                second = to_symbolic(second)

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
            if isAllReal(first, second):
                if second == 0:
                    computed = 0
                else:
                    first = to_signed(first)
                    second = to_signed(second)
                    sign = -1 if first < 0 else 1
                    computed = sign * (abs(first) % abs(second))
            else:
                first = to_symbolic(first)
                second = to_symbolic(second)

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

            if isAllReal(first, second, third):
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

            if isAllReal(first, second, third):
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
            if isAllReal(base, exponent):
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
            if isAllReal(first, second):
                if first >= 32 or first < 0:
                    computed = second
                else:
                    signbit_index_from_right = 8 * first + 7
                    if second & (1 << signbit_index_from_right):
                        computed = second | (2 ** 256 - (1 << signbit_index_from_right))
                    else:
                        computed = second & ((1 << signbit_index_from_right) - 1 )
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
                    solver.add(second & (1 << signbit_index_from_right) == 0)
                    if solver.check() == unsat:
                        computed = second | (2 ** 256 - (1 << signbit_index_from_right))
                    else:
                        computed = second & ((1 << signbit_index_from_right) - 1)
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
            if isAllReal(first, second):
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
            if isAllReal(first, second):
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
            if isAllReal(first, second):
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
            if isAllReal(first, second):
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
            if isAllReal(first, second):
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
            if isReal(first):
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

            if isAllReal(first, second):
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
            s0 = stack.pop(0)
            s1 = stack.pop(0)
            if isAllReal(s0, s1):
                # simulate the hashing of sha3
                data = [str(x) for x in memory[s0: s0 + s1]]
                position = ''.join(data)
                position = re.sub('[\s+]', '', position)
                position = zlib.compress(position, 9)
                position = base64.b64encode(position)
                if position in sha3_list:
                    stack.insert(0, sha3_list[position])
                else:
                    new_var_name = gen.gen_arbitrary_var()
                    new_var = BitVec(new_var_name, 256)
                    sha3_list[position] = new_var
                    stack.insert(0, new_var)
            else:
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
            if isReal(address) and global_params.USE_GLOBAL_BLOCKCHAIN:
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
            if global_params.INPUT_STATE and global_state["callData"]:
                callData = global_state["callData"]
                start = position * 2
                end = start + 64
                while end > len(callData):
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
    elif instr_parts[0] == "CALLDATASIZE":
        global_state["pc"] = global_state["pc"] + 1
        if global_params.INPUT_STATE and global_state["callData"]:
            stack.insert(0, len(global_state["callData"])/2)
        else:
            new_var_name = gen.gen_data_size()
            if new_var_name in path_conditions_and_vars:
                new_var = path_conditions_and_vars[new_var_name]
            else:
                new_var = BitVec(new_var_name, 256)
                path_conditions_and_vars[new_var_name] = new_var
            stack.insert(0, new_var)
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
        if c_name.endswith('.disasm'):
            evm_file_name = c_name[:-7]
        else:
            evm_file_name = c_name
        with open(evm_file_name, 'r') as evm_file:
            evm = evm_file.read()[:-1]
            code_size = len(evm)/2
            stack.insert(0, code_size)
    elif instr_parts[0] == "CODECOPY":
        if len(stack) > 2:
            global_state["pc"] = global_state["pc"] + 1
            mem_location = stack.pop(0)
            code_from = stack.pop(0)
            no_bytes = stack.pop(0)
            current_miu_i = global_state["miu_i"]

            if isAllReal(mem_location, current_miu_i, code_from, no_bytes):
                temp = long(math.ceil((mem_location + no_bytes) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp

                if c_name.endswith('.disasm'):
                    evm_file_name = c_name[:-7]
                else:
                    evm_file_name = c_name
                with open(evm_file_name, 'r') as evm_file:
                    evm = evm_file.read()[:-1]
                    start = code_from * 2
                    end = start + no_bytes * 2
                    code = evm[start: end]
                mem[mem_location] = int(code, 16)
            else:
                new_var_name = gen.gen_code_var("Ia", code_from, no_bytes)
                if new_var_name in path_conditions_and_vars:
                    new_var = path_conditions_and_vars[new_var_name]
                else:
                    new_var = BitVec(new_var_name, 256)
                    path_conditions_and_vars[new_var_name] = new_var

                temp = ((mem_location + no_bytes) / 32) + 1
                current_miu_i = to_symbolic(current_miu_i)
                expression = current_miu_i < temp
                solver.push()
                solver.add(expression)
                if solver.check() != unsat:
                    current_miu_i = If(expression, temp, current_miu_i)
                solver.pop()
                mem.clear() # very conservative
                mem[str(mem_location)] = new_var
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "GASPRICE":
        global_state["pc"] = global_state["pc"] + 1
        stack.insert(0, global_state["gas_price"])
    elif instr_parts[0] == "EXTCODESIZE":
        if len(stack) > 0:
            global_state["pc"] = global_state["pc"] + 1
            address = stack.pop(0)
            if isReal(address) and global_params.USE_GLOBAL_BLOCKCHAIN:
                code = data_source.getCode(address)
                stack.insert(0, len(code)/2)
            else:
                #not handled yet
                stack.insert(0, 0)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "EXTCODECOPY":
        if len(stack) > 3:
            global_state["pc"] = global_state["pc"] + 1
            address = stack.pop(0)
            mem_location = stack.pop(0)
            code_from = stack.pop(0)
            no_bytes = stack.pop(0)
            current_miu_i = global_state["miu_i"]

            if isAllReal(adress, mem_location, current_miu_i, code_from, no_bytes) and USE_GLOBAL_BLOCKCHAIN:
                temp = long(math.ceil((mem_location + no_bytes) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp

                evm = data_source.getCode(address)
                start = code_from * 2
                end = start + no_bytes * 2
                code = evm[start: end]
                mem[mem_location] = int(code, 16)
            else:
                new_var_name = gen.gen_code_var(address, code_from, no_bytes)
                if new_var_name in path_conditions_and_vars:
                    new_var = path_conditions_and_vars[new_var_name]
                else:
                    new_var = BitVec(new_var_name, 256)
                    path_conditions_and_vars[new_var_name] = new_var

                temp = ((mem_location + no_bytes) / 32) + 1
                current_miu_i = to_symbolic(current_miu_i)
                expression = current_miu_i < temp
                solver.push()
                solver.add(expression)
                if solver.check() != unsat:
                    current_miu_i = If(expression, temp, current_miu_i)
                solver.pop()
                mem.clear() # very conservative
                mem[str(mem_location)] = new_var
            global_state["miu_i"] = current_miu_i
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
            if isAllReal(address, current_miu_i) and address in mem:
                temp = long(math.ceil((address + 32) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp
                value = mem[address]
                stack.insert(0, value)
                log.debug("temp: " + str(temp))
                log.debug("current_miu_i: " + str(current_miu_i))
            else:
                temp = ((address + 31) / 32) + 1
                current_miu_i = to_symbolic(current_miu_i)
                expression = current_miu_i < temp
                solver.push()
                solver.add(expression)
                if solver.check() != unsat:
                    # this means that it is possibly that current_miu_i < temp
                    current_miu_i = If(expression,temp,current_miu_i)
                solver.pop()
                new_var_name = gen.gen_mem_var(address)
                if new_var_name in path_conditions_and_vars:
                    new_var = path_conditions_and_vars[new_var_name]
                else:
                    new_var = BitVec(new_var_name, 256)
                    path_conditions_and_vars[new_var_name] = new_var
                stack.insert(0, new_var)
                if isReal(address):
                    mem[address] = new_var
                else:
                    mem[str(address)] = new_var
                log.debug("temp: " + str(temp))
                log.debug("current_miu_i: " + str(current_miu_i))
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MSTORE":
        if len(stack) > 1:
            global_state["pc"] = global_state["pc"] + 1
            stored_address = stack.pop(0)
            stored_value = stack.pop(0)
            current_miu_i = global_state["miu_i"]
            if isReal(stored_address):
                # preparing data for hashing later
                old_size = len(memory) // 32
                new_size = ceil32(stored_address + 32) // 32
                mem_extend = (new_size - old_size) * 32
                memory.extend([0] * mem_extend)
                for i in range(31, -1, -1):
                    memory[stored_address + i] = stored_value % 256
                    stored_value /= 256
            if isAllReal(stored_address, current_miu_i):
                temp = long(math.ceil((stored_address + 32) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp
                mem[stored_address] = stored_value  # note that the stored_value could be symbolic
                log.debug("temp: " + str(temp))
                log.debug("current_miu_i: " + str(current_miu_i))
            else:
                log.debug("temp: " + str(stored_address))
                temp = ((stored_address + 31) / 32) + 1
                log.debug("current_miu_i: " + str(current_miu_i))
                expression = current_miu_i < temp
                log.debug("Expression: " + str(expression))
                solver.push()
                solver.add(expression)
                if solver.check() != unsat:
                    # this means that it is possibly that current_miu_i < temp
                    current_miu_i = If(expression,temp,current_miu_i)
                solver.pop()
                mem.clear()  # very conservative
                mem[str(stored_address)] = stored_value
                log.debug("temp: " + str(temp))
                log.debug("current_miu_i: " + str(current_miu_i))
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
            if isAllReal(stored_address, current_miu_i):
                temp = long(math.ceil((stored_address + 1) / float(32)))
                if temp > current_miu_i:
                    current_miu_i = temp
                mem[stored_address] = stored_value  # note that the stored_value could be symbolic
            else:
                temp = (stored_address / 32) + 1
                if isReal(current_miu_i):
                    current_miu_i = BitVecVal(current_miu_i, 256)
                expression = current_miu_i < temp
                solver.push()
                solver.add(expression)
                if solver.check() != unsat:
                    # this means that it is possibly that current_miu_i < temp
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
            if isReal(address) and address in global_state["Ia"]:
                value = global_state["Ia"][address]
                stack.insert(0, value)
            else:
                if str(address) in global_state["Ia"]:
                    value = global_state["Ia"][str(address)]
                    stack.insert(0, value)
                else:
                    if is_expr(address):
                        address = simplify(address)
                    new_var_name = gen.gen_owner_store_var(address)
                    if new_var_name in path_conditions_and_vars:
                        new_var = path_conditions_and_vars[new_var_name]
                    else:
                        new_var = BitVec(new_var_name, 256)
                        path_conditions_and_vars[new_var_name] = new_var
                    stack.insert(0, new_var)
                    if isReal(address):
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
            if isReal(stored_address):
                # note that the stored_value could be unknown
                global_state["Ia"][stored_address] = stored_value
            else:
                # note that the stored_value could be unknown
                global_state["Ia"][str(stored_address)] = stored_value
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "JUMP":
        if len(stack) > 0:
            target_address = stack.pop(0)
            if isSymbolic(target_address):
                try:
                    target_address = int(str(simplify(target_address)))
                except:
                    raise TypeError("Target address must be an integer")
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
                try:
                    target_address = int(str(simplify(target_address)))
                except:
                    raise TypeError("Target address must be an integer")
            vertices[start].set_jump_target(target_address)
            flag = stack.pop(0)
            branch_expression = (BitVecVal(0, 1) == BitVecVal(1, 1))
            if isReal(flag):
                if flag != 0:
                    branch_expression = True
            else:
                branch_expression = (flag != 0)
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
    #
    #  60s & 70s: Push Operations
    #
    elif instr_parts[0].startswith('PUSH', 0):  # this is a push instruction
        position = int(instr_parts[0][4:], 10)
        global_state["pc"] = global_state["pc"] + 1 + position
        pushed_value = int(instr_parts[1], 16)
        stack.insert(0, pushed_value)
        if global_params.UNIT_TEST == 3: # test evm symbolic
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
        # We do not simulate these log operations
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

            if isReal(transfer_amount):
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
                    if isReal(recipient):
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

            if isReal(transfer_amount):
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
    elif instr_parts[0] == "RETURN" or instr_parts[0] == "REVERT":
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
        if isReal(recipient):
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
        log.debug("UNKNOWN INSTRUCTION: " + instr_parts[0])
        if global_params.UNIT_TEST == 2 or global_params.UNIT_TEST == 3:
            log.critical("Unkown instruction: %s" % instr_parts[0])
            exit(UNKOWN_INSTRUCTION)
        raise Exception('UNKNOWN INSTRUCTION: ' + instr_parts[0])

    try:
        print_state(stack, mem, global_state)
    except:
        log.debug("Error: Debugging states")

# check for evm sequence SWAP4, POP, POP, POP, POP, ISZERO
def check_callstack_attack(disasm):
    problematic_instructions = ['CALL', 'CALLCODE']
    for i in xrange(0, len(disasm)):
        instruction = disasm[i]
        if instruction[1] in problematic_instructions:
            if not disasm[i+1][1] == 'SWAP':
                return True
            swap_num = int(disasm[i+1][2])
            for j in range(swap_num):
                if not disasm[i+j+2][1] == 'POP':
                    return True
            if not disasm[i + swap_num + 2][1] == 'ISZERO':
                return True
    return False

def run_callstack_attack():
    global results
    disasm_data = open(c_name).read()
    instr_pattern = r"([\d]+): ([A-Z]+)([\d]?)(?: 0x)?(\S+)?"
    instr = re.findall(instr_pattern, disasm_data)
    result = check_callstack_attack(instr)

    if not isTesting():
        log.info("\t  CallStack Attack: \t %s", result)
    results['callstack'] = result

if __name__ == '__main__':
    main(sys.argv[1])
