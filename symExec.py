from z3 import *
from vargenerator import *
import sys
import tokenize
from tokenize import NUMBER, NAME, NEWLINE
from basicblock import BasicBlock
from analysis import *
import copy

count_unresolved_jumps = 0

gen = Generator()  # to generate names for symbolic variables

end_ins_dict = {}  # capturing the last statement of each basic block
instructions = {}  # capturing all the instructions, keys are corresponding addresses
jump_type = {}  # capturing the "jump type" of each basic block
vertices = {}
edges = {}
money_flow_all_paths = []

# Z3 solver
solver = Solver()

CONSTANT_ONES_159 = BitVecVal((1 << 160) - 1, 256)

# Set this flag to 1 if we want to do unit test
UNIT_TEST = 0

if UNIT_TEST == 1:
    try:
        result_file = open(sys.argv[2], 'r')
    except:
        print "Could not open result file for unit test"
        exit()


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
    detect_concurrency()
    # print_cfg()


def build_cfg_and_analyze():
    with open(sys.argv[1], 'r') as disasm_file:
        disasm_file.readline()  # Remove first line
        tokens = tokenize.generate_tokens(disasm_file.readline)
        collect_vertices(tokens)
        construct_bb()
        construct_static_edges()
        full_sym_exec()  # jump targets are constructed on the fly


def detect_concurrency():

    n = len(money_flow_all_paths)
    for i in range(n):
        print "Path " + str(i) + ": " + str(money_flow_all_paths[i])
    i = 0
    for flow in money_flow_all_paths:
        i += 1
        if len(flow) == 1:
            continue  # pass all flows which do not do anything with money
        for j in range(i, n):
            jflow = money_flow_all_paths[j]
            if len(jflow) == 1:
                continue
            if is_diff(flow, jflow):
                print "Concurrency in path " + str(i-1) + " and path " + str(j)


# return true if the two paths have different flows of money
# later on we may want to return more meaningful output: e.g. if the concurrency changes
# the amount of money or the recipient.
def is_diff(flow1, flow2):
    if len(flow1) != len(flow2):
        return 1
    n = len(flow1)
    for i in range(n):
        if flow1[i] == flow2[i]:
            continue
        tx_cd = Or(Not(flow1[i][0] == flow2[i][0]),
                   Not(flow1[i][1] == flow2[i][1]),
                   Not(flow1[i][2] == flow2[i][2]))
        solver.push()
        solver.add(tx_cd)

        if solver.check() == sat:
            solver.pop()
            return 1
        solver.pop()
    return 0


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


def my_copy_dict(input):
    output = {}
    for key in input:
        if isinstance(input[key], list):
            output[key] = list(input[key])
        elif isinstance(input[key], dict):
            output[key] = dict(input[key])
        else:
            output[key] = input[key]

    return output


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

        solver.pop()  # POP SOLVER CONTEXT

        solver.push()  # SET A BOUNDARY FOR SOLVER
        negated_branch_expression = Not(branch_expression)
        solver.add(negated_branch_expression)

        print "Negated branch expression: " + str(negated_branch_expression)

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
        new_var_name = "Ia"
        if new_var_name in path_conditions_and_vars:
            new_var = path_conditions_and_vars[new_var_name]
        else:
            new_var = BitVec(new_var_name, 256)
            path_conditions_and_vars[new_var_name] = new_var
        stack.insert(0, new_var)
    elif instr_parts[0] == "CALLER":  # get address of the account
        # that is directly responsible for this execution
        new_var_name = "Is"
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
            if isinstance(address, (int, long)) and address in mem:
                value = mem[address]
                stack.insert(0, value)
            else:
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
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MSTORE":
        if len(stack) > 1:
            stored_address = stack.pop(0)
            stored_value = stack.pop(0)
            if isinstance(stored_address, (int, long)):
                mem[stored_address] = stored_value  # note that the stored_value could be unknown
            else:
                mem.clear()  # very conservative
                mem[str(stored_address)] = stored_value
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MSTORE8":
        if len(stack) > 1:
            stored_address = stack.pop(0)
            temp = stack.pop(0)
            stored_value = temp % 256  # get the least byte
            if isinstance(stored_address, (int, long)):
                mem[stored_address] = stored_value  # note that the stored_value could be unknown
            else:
                mem.clear()  # very conservative
                mem[str(stored_address)] = stored_value
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
        raise Exception('Must implement MSIZE now')
    elif instr_parts[0] == "GAS":
        # In general, we do not have this precisely. It depends on both
        # the initial gas and the amount has been depleted
        new_var_name = gen.get_gas_var()
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
    elif instr_parts[0] == "RETURN":
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
