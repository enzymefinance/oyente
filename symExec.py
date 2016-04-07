from z3 import *
from vargenerator import *
import tokenize
from tokenize import NUMBER, NAME, NEWLINE
from basicblock import BasicBlock
from analysis import *
from utils import *
from math import *

REPORT_MODE = 1
DEBUG_MODE = 1
CHECK_CONCURRENCY_FLAG = 0
count_unresolved_jumps = 0
gen = Generator()  # to generate names for symbolic variables

end_ins_dict = {}  # capturing the last statement of each basic block
instructions = {}  # capturing all the instructions, keys are corresponding addresses
jump_type = {}  # capturing the "jump type" of each basic block
vertices = {}
edges = {}
money_flow_all_paths = []
data_flow_all_paths = [[], []] # store all storage addresses
path_conditions = [] # store the path condition corresponding to each path in money_flow_all_paths
all_gs = [] # store global variables, e.g. storage, balance of all paths

# Z3 solver
solver = Solver()
solver.set("timeout", 6000)

CONSTANT_ONES_159 = BitVecVal((1 << 160) - 1, 256)

# Set this flag to 1 if we want to do unit test
UNIT_TEST = 0

if UNIT_TEST == 1:
    try:
        result_file = open(sys.argv[2], 'r')
    except:
        print "Could not open result file for unit test"
        exit()

if DEBUG_MODE:
    log_file = open(sys.argv[1] + '.log', "w")

# A simple function to compare the end stack with the expected stack
# configurations specified in a test file
def compare_stack_unit_test(stack):
    if UNIT_TEST != 1:
        return
    try:
        size = int(result_file.readline())
        content = result_file.readline().strip('\n')
        if size == len(stack) and str(stack) == content:
            print "PASSED UNIT-TEST"
        else:
            print "FAILED UNIT-TEST"
            print "Expected size %d, Resulted size %d" % (size, len(stack))
            print "Expected content %s \nResulted content %s" % (content, str(stack))
    except Exception as e:
        print "FAILED UNIT-TEST"
        print e.message


def main():
    build_cfg_and_analyze()
    detect_money_concurrency()
    # detect_data_concurrency()
    # detect_data_money_concurrency()
    # print_cfg()


def build_cfg_and_analyze():
    with open(sys.argv[1], 'r') as disasm_file:
        disasm_file.readline()  # Remove first line
        tokens = tokenize.generate_tokens(disasm_file.readline)
        collect_vertices(tokens)
        construct_bb()
        construct_static_edges()
        full_sym_exec()  # jump targets are constructed on the fly


# detect if two paths send money to different people
def detect_money_concurrency():
    n = len(money_flow_all_paths)
    for i in range(n):
        print "Path " + str(i) + ": " + str(money_flow_all_paths[i])
        print all_gs[i]
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
                if CHECK_CONCURRENCY_FLAG and \
                        is_false_positive(i-1, j, all_gs, path_conditions) and \
                        is_false_positive(j, i-1, all_gs, path_conditions):
                    false_positive.append([i-1, j])

    print "All false positive cases: ", false_positive
    print "Concurrency in paths: ", concurrency_paths
    if REPORT_MODE:
        report_file = sys.argv[1] + '.report'
        with open(report_file, 'w') as rfile:
            rfile.write(str(n) + "\n")
            rfile.write(str(len(false_positive)) + "\n")
            rfile.write(str(false_positive) + "\n")
            rfile.write(str(len(concurrency_paths)) + "\n")
            rfile.write(str(concurrency_paths) + "\n")
            rfile.close()


# Detect if there is data concurrency in two different flows.
# e.g. if a flow modifies a value stored in the storage address and
# the other one reads that value in its execution
def detect_data_concurrency():
    sload_flows = data_flow_all_paths[0]
    sstore_flows = data_flow_all_paths[1]
    # print sload_flows
    # print sstore_flows
    concurrency_addr = []
    for sflow in sstore_flows:
        for addr in sflow:
            for lflow in sload_flows:
                if addr in lflow:
                    if not addr in concurrency_addr:
                        concurrency_addr.append(addr)
                    break
    print "data conccureny in storage " + str(concurrency_addr)

# detect if any change in a storage address will result in a different
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
    print "Concurrency in data that affects money flow: " + str(set(concurrency_addr))


def print_cfg():
    for block in vertices.values():
        block.display()
    print str(edges)


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
                    print current_line_content
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
                print "ERROR when parsing row %d col %d" % (srow, scol)
                quit()
            is_new_line = False
            if is_new_block:
                current_block = current_ins_address
                is_new_block = False
            continue
        elif tok_type == NEWLINE:
            is_new_line = True
            print current_line_content
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
        print "current block: %d" % current_block
        print "last line: %d" % current_ins_address
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
    global_state = { "balance" : {} }
    for new_var_name in ("Is", "Ia"):
        if new_var_name not in path_conditions_and_vars:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var

    deposited_value = BitVec("Iv", 256)
    path_conditions_and_vars["Iv"] = deposited_value

    init_is = BitVec("init_Is", 256)
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

    # the state of the current current contract
    global_state["Ia"] = {}
    global_state["miu_i"] = 0

    return global_state


def full_sym_exec():
    # executing, starting from beginning
    stack = []
    path_conditions_and_vars = {"path_condition" : []}
    visited = []
    mem = {}
    global_state = get_init_global_state(path_conditions_and_vars)  # this is init global state for this particular execution
    analysis = init_analysis()
    return sym_exec_block(0, visited, stack, mem, global_state, path_conditions_and_vars, analysis)


# Symbolically executing a block from the start address
def sym_exec_block(start, visited, stack, mem, global_state, path_conditions_and_vars, analysis):
    if start < 0:
        print "ERROR: UNKNOWN JUMP ADDRESS. TERMINATING THIS PATH"
        return ["ERROR"]

    print "\nDEBUG: Reach block address %d \n" % start
    print "STACK: " + str(stack)

    if start in visited:
        print "Seeing a loop. Terminating this path ... "
        return stack

    # Execute every instruction, one at a time
    try:
        block_ins = vertices[start].get_instructions()
    except KeyError:
        print "This path results in an exception"
        return ["ERROR"]

    for instr in block_ins:
        sym_exec_ins(start, instr, stack, mem, global_state, path_conditions_and_vars, analysis)

    # Mark that this basic block in the visited blocks
    visited.append(start)

    # Go to next Basic Block(s)
    if jump_type[start] == "terminal":
        print "TERMINATING A PATH ..."
        display_analysis(analysis)
        if analysis["money_flow"] not in money_flow_all_paths:
            money_flow_all_paths.append(analysis["money_flow"])
            path_conditions.append(path_conditions_and_vars["path_condition"])
            all_gs.append(copy_global_values(global_state))
        if analysis["sload"] not in data_flow_all_paths[0]:
            data_flow_all_paths[0].append(analysis["sload"])
        if analysis["sstore"] not in data_flow_all_paths[1]:
            data_flow_all_paths[1].append(analysis["sstore"])
        compare_stack_unit_test(stack)
        # print "Path condition = " + str(path_conditions_and_vars["path_condition"])
        # raw_input("Press Enter to continue...\n")
    elif jump_type[start] == "unconditional":  # executing "JUMP"
        successor = vertices[start].get_jump_target()
        stack1 = list(stack)
        mem1 = dict(mem)
        global_state1 = my_copy_dict(global_state)
        visited1 = list(visited)
        path_conditions_and_vars1 = my_copy_dict(path_conditions_and_vars)
        analysis1 = my_copy_dict(analysis)
        sym_exec_block(successor, visited1, stack1, mem1, global_state1, path_conditions_and_vars1, analysis1)
    elif jump_type[start] == "falls_to":  # just follow to the next basic block
        successor = vertices[start].get_falls_to()
        stack1 = list(stack)
        mem1 = dict(mem)
        global_state1 = my_copy_dict(global_state)
        visited1 = list(visited)
        path_conditions_and_vars1 = my_copy_dict(path_conditions_and_vars)
        analysis1 = my_copy_dict(analysis)
        sym_exec_block(successor, visited1, stack1, mem1, global_state1, path_conditions_and_vars1, analysis1)
    elif jump_type[start] == "conditional":  # executing "JUMPI"

        # A choice point, we proceed with depth first search

        branch_expression = vertices[start].get_branch_expression()

        print "Branch expression: " + str(branch_expression)

        solver.push()  # SET A BOUNDARY FOR SOLVER
        solver.add(branch_expression)

        try:
            if solver.check() == unsat:
                print "INFEASIBLE PATH DETECTED"
            else:
                left_branch = vertices[start].get_jump_target()
                stack1 = list(stack)
                mem1 = dict(mem)
                global_state1 = my_copy_dict(global_state)
                visited1 = list(visited)
                path_conditions_and_vars1 = my_copy_dict(path_conditions_and_vars)
                path_conditions_and_vars1["path_condition"].append(branch_expression)
                analysis1 = my_copy_dict(analysis)
                sym_exec_block(left_branch, visited1, stack1, mem1, global_state1, path_conditions_and_vars1, analysis1)
        except Exception as e:
            log_file.write(str(e))

        solver.pop()  # POP SOLVER CONTEXT

        solver.push()  # SET A BOUNDARY FOR SOLVER
        negated_branch_expression = Not(branch_expression)
        solver.add(negated_branch_expression)

        print "Negated branch expression: " + str(negated_branch_expression)

        try:
            if solver.check() == unsat:
                # Note that this check can be optimized. I.e. if the previous check succeeds,
                # no need to check for the negated condition, but we can immediately go into
                # the else branch
                print "INFEASIBLE PATH DETECTED"
            else:
                right_branch = vertices[start].get_falls_to()
                stack1 = list(stack)
                mem1 = dict(mem)
                global_state1 = my_copy_dict(global_state)
                visited1 = list(visited)
                path_conditions_and_vars1 = my_copy_dict(path_conditions_and_vars)
                path_conditions_and_vars1["path_condition"].append(negated_branch_expression)
                analysis1 = my_copy_dict(analysis)
                sym_exec_block(right_branch, visited1, stack1, mem1, global_state1, path_conditions_and_vars1, analysis1)
        except Exception as e:
            log_file.write(str(e))
        solver.pop()  # POP SOLVER CONTEXT

    else:
        raise Exception('Unknown Jump-Type')


# Symbolically executing an instruction
def sym_exec_ins(start, instr, stack, mem, global_state, path_conditions_and_vars, analysis):
    instr_parts = str.split(instr, ' ')

    # collecting the analysis result by calling this skeletal function
    # this should be done before symbolically executing the instruction,
    # since SE will modify the stack and mem
    update_analysis(analysis, instr_parts[0], stack, mem, global_state)

    print "=============================="
    print "EXECUTING: " + instr

    #
    #  0s: Stop and Arithmetic Operations
    #
    if instr_parts[0] == "STOP":
        return
    elif instr_parts[0] == "ADD":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            # Type conversion is needed when they are mismatched
            if isinstance(first, (int, long)) and not isinstance(second, (int, long)):
                first = BitVecVal(first, 256)
            elif not isinstance(first, (int, long)) and isinstance(second, (int, long)):
                second = BitVecVal(second, 256)
            computed = first + second
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MUL":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and not isinstance(second, (int, long)):
                first = BitVecVal(first, 256)
            elif not isinstance(first, (int, long)) and isinstance(second, (int, long)):
                second = BitVecVal(second, 256)
            computed = first * second
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SUB":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and not isinstance(second, (int, long)):
                first = BitVecVal(first, 256)
            elif not isinstance(first, (int, long)) and isinstance(second, (int, long)):
                second = BitVecVal(second, 256)
            computed = first - second
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "DIV":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and not isinstance(second, (int, long)):
                first = BitVecVal(first, 256)
            elif not isinstance(first, (int, long)) and isinstance(second, (int, long)):
                second = BitVecVal(second, 256)
            computed = first / second
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MOD":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(second, (int, long)):
                if second == 0:
                    computed = 0
                else:
                    if not isinstance(first, (int, long)):
                        second = BitVecVal(second, 256)  # Make second a bitvector
                    computed = first % second
            else:
                solver.push()
                solver.add(Not(second == 0))
                if solver.check() == unsat:
                    # it is provable that second is indeed equal to zero
                    computed = 0
                else:
                    if isinstance(first, (int, long)):
                        first = BitVecVal(first, 256)  # Make first a bitvector
                    computed = first % second
                solver.pop()
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SMOD":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(second, (int, long)):
                if second == 0:
                    computed = 0
                else:
                    if not isinstance(first, (int, long)):
                        second = BitVecVal(second, 256)  # Make second a bitvector
                    computed = first % second  # This is not yet faithful
            else:
                solver.push()
                solver.add(Not(second == 0))
                if solver.check() == unsat:
                    # it is provable that second is indeed equal to zero
                    computed = 0
                else:
                    if isinstance(first, (int, long)):
                        first = BitVecVal(first, 256)  # Make first a bitvector
                    computed = first % second  # This is not yet faithful
                solver.pop()
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "ADDMOD":
        if len(stack) > 2:
            first = stack.pop(0)
            second = stack.pop(0)
            third = stack.pop(0)
            if isinstance(third, (int, long)):
                if third == 0:
                    computed = 0
                else:
                    if not (isinstance(first, (int, long)) and isinstance(second, (int, long))):
                        # there is one guy that is a symbolic expression
                        third = BitVecVal(third, 256)
                        if isinstance(first, (int, long)):
                            first = BitVecVal(first, 256)
                        if isinstance(second, (int, long)):
                            second = BitVecVal(second, 256)
                    computed = (first + second) % third
            else:
                solver.push()
                solver.add(Not(third == 0))
                if solver.check() == unsat:
                    # it is provable that second is indeed equal to zero
                    computed = 0
                else:
                    if isinstance(first, (int, long)):
                        first = BitVecVal(first, 256)
                    if isinstance(second, (int, long)):
                        second = BitVecVal(second, 256)
                    computed = (first + second) % third
                solver.pop()
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MULMOD":
        if len(stack) > 2:
            first = stack.pop(0)
            second = stack.pop(0)
            third = stack.pop(0)
            if isinstance(third, (int, long)):
                if third == 0:
                    computed = 0
                else:
                    if not (isinstance(first, (int, long)) and isinstance(second, (int, long))):
                        # there is one guy that is a symbolic expression
                        third = BitVecVal(third, 256)
                        if isinstance(first, (int, long)):
                            first = BitVecVal(first, 256)
                        if isinstance(second, (int, long)):
                            second = BitVecVal(second, 256)
                    computed = (first * second) % third
            else:
                solver.push()
                solver.add(Not(third == 0))
                if solver.check() == unsat:
                    # it is provable that second is indeed equal to zero
                    computed = 0
                else:
                    if isinstance(first, (int, long)):
                        first = BitVecVal(first, 256)
                    if isinstance(second, (int, long)):
                        second = BitVecVal(second, 256)
                    computed = (first * second) % third
                solver.pop()
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "EXP":
        if len(stack) > 1:
            base = stack.pop(0)
            exponent = stack.pop(0)
            # Type conversion is needed when they are mismatched
            if isinstance(base, (int, long)) and isinstance(exponent, (int, long)):
                computed = base ** exponent
            else:
                # The computed value is unknown, this is because power is
                # not supported in bit-vector theory
                new_var_name = gen.gen_arbitrary_var()
                computed = BitVec(new_var_name, 256)
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SIGNEXTEND":
        index = stack.pop(0)
        content = stack.pop(0)
        new_var_name = gen.gen_arbitrary_var()
        new_var = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
        '''
        if isinstance(index, (int, long)):
            t = 256 - 8 * (index + 1)
            if isinstance(content, (int, long)):
                # TODO
            else:
                for i in range(0, 255):

        else:
            # DON'T KNOW WHAT could be the resulting value
            # we then create a new symbolic variable
        '''    
        raise ValueError('SIGNEXTEND is not yet handled')
    #
    #  10s: Comparison and Bitwise Logic Operations
    #
    elif instr_parts[0] == "LT":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
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
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
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
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
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
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
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
            first = stack.pop(0)
            second = stack.pop(0)
            computed = first & second
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "OR":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)

            computed = first | second
            stack.insert(0, computed)

        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "XOR":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)

            computed = first ^ second
            stack.insert(0, computed)

        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "NOT":
        if len(stack) > 0:
            first = stack.pop(0)
            if isinstance(first, (int, long)):
                complement = -1 - first
                stack.insert(0, complement)
            else:
                sym_expression = (~ first)
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "BYTE":
        raise ValueError('BYTE is not yet handled')
    #
    # 20s: SHA3
    #
    elif instr_parts[0] == "SHA3":
        if len(stack) > 1:
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
        new_var_name = gen.gen_address_var()
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "BALANCE":
        if len(stack) > 0:
            address = stack.pop(0)
            new_var_name = gen.gen_balance_var()
            if new_var_name in path_conditions_and_vars:
                new_var = path_conditions_and_vars[new_var_name]
            else:
                new_var = BitVec(new_var_name, 256)
                path_conditions_and_vars[new_var_name] = new_var
            if isinstance(address, (int, long)):
                hashed_address = "concrete_address_" + address
            else:
                hashed_address = str(address)
            global_state["balance"][hashed_address] = new_var
            stack.insert(0, new_var)
        else:
            raise ValueError('STACK underflow')      
    elif instr_parts[0] == "CALLER":  # get caller address
        # that is directly responsible for this execution
        new_var_name = gen.gen_caller_var()
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "ORIGIN":  # get execution origination address
        new_var_name = gen.gen_origin_var()
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "CALLVALUE":  # get value of this transaction
        new_var_name = "Iv"
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "CALLDATALOAD":  # from input data from environment
        if len(stack) > 0:
            position = stack.pop(0)
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
        new_var_name = gen.gen_data_size()
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "CALLDATACOPY":  # Copy input data to memory
        # Don't know how to simulate this yet
        if len(stack) > 2:
            stack.pop(0)
            stack.pop(0)
            stack.pop(0)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "CODECOPY":  # Copy code running in current env to memory
        # Don't know how to simulate this yet
        # Need an example to test
        if len(stack) > 2:
            stack.pop(0)
            stack.pop(0)
            stack.pop(0)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "GASPRICE":  # get address of currently executing account
        new_var_name = gen.gen_gas_price_var()
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    #
    #  40s: Block Information
    #
    elif instr_parts[0] == "BLOCKHASH":  # information from block header
        if len(stack) > 0:
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
        new_var_name = "IH_c"
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "TIMESTAMP":  # information from block header
        new_var_name = "IH_s"
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "NUMBER":  # information from block header
        new_var_name = "IH_i"
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "DIFFICULTY":  # information from block header
        new_var_name = "IH_d"
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "GASLIMIT":  # information from block header
        new_var_name = "IH_l"
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    #
    #  50s: Stack, Memory, Storage, and Flow Information
    #
    elif instr_parts[0] == "POP":
        if len(stack) > 0:
            stack.pop(0)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MLOAD":
        if len(stack) > 0:
            address = stack.pop(0)
            current_miu_i = global_state["miu_i"]
            if isinstance(address, (int, long)) and address in mem:
                temp = ceil((address + 32) / float(32))
                if temp > current_miu_i:
                    current_miu_i = temp
                value = mem[address]
                stack.insert(0, value)
            else:
                temp = ((address + 31) / 32) + 1
                if isinstance(current_miu_i, (int, long)):
                    current_miu_i = BitVecVal(current_miu_i, 256)
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
                if isinstance(address, (int, long)):
                    mem[address] = new_var
                else:
                    mem[str(address)] = new_var
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MSTORE":
        if len(stack) > 1:
            stored_address = stack.pop(0)
            stored_value = stack.pop(0)
            current_miu_i = global_state["miu_i"]
            if isinstance(stored_address, (int, long)):
                temp = ceil((stored_address + 32) / float(32))
                if temp > current_miu_i:
                    current_miu_i = temp
                mem[stored_address] = stored_value  # note that the stored_value could be symbolic
            else:
                temp = ((stored_address + 31) / 32) + 1
                if isinstance(current_miu_i, (int, long)):
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
    elif instr_parts[0] == "MSTORE8":
        if len(stack) > 1:
            stored_address = stack.pop(0)
            temp_value = stack.pop(0)
            stored_value = temp_value % 256  # get the least byte
            current_miu_i = global_state["miu_i"]
            if isinstance(stored_address, (int, long)):
                temp = ceil((stored_address + 1) / float(32))
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
                    current_miu_i = If(expression,temp,current_miu_i)
                solver.pop()
                mem.clear()  # very conservative
                mem[str(stored_address)] = stored_value
            global_state["miu_i"] = current_miu_i
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SLOAD":
        if len(stack) > 0:
            address = stack.pop(0)
            if isinstance(address, (int, long)) and address in global_state["Ia"]:
                value = global_state["Ia"][address]
                stack.insert(0, value)
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
            vertices[start].set_jump_target(target_address)
            if target_address not in edges[start]:
                edges[start].append(target_address)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "JUMPI":
        # WE need to prepare two branches
        if len(stack) > 1:
            target_address = stack.pop(0)
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
        # this is not hard, but tedious. Let's skip it for now
        raise Exception('Must implement PC now')
    elif instr_parts[0] == "MSIZE":
        msize = 32 * global_state["miu_i"]
        stack.insert(0, msize)
    elif instr_parts[0] == "GAS":
        # In general, we do not have this precisely. It depends on both
        # the initial gas and the amount has been depleted
        # we need o think about this in the future, in case precise gas
        # can be tracked
        new_var_name = gen.gen_gas_var()
        new_var = BitVec(new_var_name, 256)
        path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "JUMPDEST":
        # Literally do nothing
        pass
    #
    #  60s & 70s: Push Operations
    #
    elif instr_parts[0].startswith('PUSH', 0):  # this is a push instruction
        pushed_value = int(instr_parts[1], 16)
        stack.insert(0, pushed_value)
    #
    #  80s: Duplication Operations
    #
    elif instr_parts[0].startswith("DUP", 0):
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
        # We do not simulate these logging operations
        num_of_pops = 2 + int(instr_parts[0][3:])
        while num_of_pops > 0:
            stack.pop(0)
            num_of_pops -= 1

    #
    #  f0s: System Operations
    #
    elif instr_parts[0] == "CALL":
        # DOTO: Need to handle miu_i
        if len(stack) > 6:
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
        # DOTO: Need to handle miu_i
        if len(stack) > 6:
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
        # DOTO: Need to handle miu_i
        if len(stack) > 1:
            stack.pop(0)
            stack.pop(0)
            # TODO
            pass
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SUICIDE":
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
        print "UNKNOWN INSTRUCTION: " + instr_parts[0]
        raise Exception('UNKNOWN INSTRUCTION')

    print_state(start, stack, mem, global_state)


def print_state(block_address, stack, mem, global_state):
    print "STACK: " + str(stack)
    print "MEM: " + str(mem)
    print "GLOBAL STATE: " + str(global_state)


main()
