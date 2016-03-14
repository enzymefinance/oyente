from z3 import *
from vargenerator import *
import sys
import tokenize
from tokenize import NUMBER, NAME, NEWLINE
from basicblock import BasicBlock


gen = Generator()

end_ins_dict = {}  # capturing the last statement of each basic block
instructions = {}
jump_type = {}
vertices = {}
edges = {}

solver = Solver()

function_not = Function('not', IntSort(), IntSort())
function_and = Function('and', IntSort(), IntSort(), IntSort())
function_or = Function('or', IntSort(), IntSort(), IntSort())
function_xor = Function('xor', IntSort(), IntSort(), IntSort())


def main():
    if len(sys.argv) != 2:
        print "Usage: python core.py <disassembled file>"
        return
    build_cfg()
    print_cfg()


def build_cfg():
    with open(sys.argv[1], 'r') as disasm_file:
        disasm_file.readline()  # Remove first line
        tokens = tokenize.generate_tokens(disasm_file.readline)
        collect_vertices(tokens)
        construct_bb()
        construct_edges()


def print_cfg():
    for block in vertices.values():
        block.display()
    print str(edges)


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


def construct_edges():
    # for ease of debugging
    add_falls_to()
    full_sym_exec()


def add_falls_to():
    key_list = sorted(jump_type.keys())
    length = len(key_list)
    for i, key in enumerate(key_list):
        if jump_type[key] != "terminal" and jump_type[key] != "unconditional" and i+1 < length:
            target = key_list[i+1]
            edges[key].append(target)
            vertices[key].set_falls_to(target)


def full_sym_exec():
    # executing, starting from beginning
    stack = []
    svars = []
    visited = []
    mem = {}
    sym_exec_block(0, visited, stack, mem, svars)


# Symbolically executing a block from the start address
def sym_exec_block(start, visited, stack, mem, svars):
    if start < 0:
        print "WARNING: UNKNOWN JUMP ADDRESS. TERMINATING THIS PATH"
        return
    block_ins = vertices[start].get_instructions()
    for instr in block_ins:
        sym_exec_ins(start, instr, stack, mem, svars)
    visited.append(start)
    if jump_type[start] == "terminal":
        print "TERMINATING A PATH ..."
    elif jump_type[start] == "unconditional":
        successor = vertices[start].get_jump_target()
        stack1 = list(stack)
        mem1 = dict(mem)
        visited1 = list(visited)
        svars1 = list(svars)
        sym_exec_block(successor, visited1, stack1, mem1, svars1)
    elif jump_type[start] == "falls_to":
        successor = vertices[start].get_falls_to()
        stack1 = list(stack)
        mem1 = dict(mem)
        visited1 = list(visited)
        svars1 = list(svars)
        sym_exec_block(successor, visited1, stack1, mem1, svars1)
    elif jump_type[start] == "conditional":

        branch_expression = simplify(vertices[start].get_branch_expression())
        print "Branch expression: " + str(branch_expression)
        raw_input("Press Enter to continue...\n")

        solver.push()  # SET A BOUNDARY FOR SOLVER
        solver.add(branch_expression)

        if solver.check() == unsat:
            print "INFEASIBLE PATH DETECTED"
            raw_input("Press Enter to continue...\n")
        else:
            left_branch = vertices[start].get_jump_target()
            stack1 = list(stack)
            mem1 = dict(mem)
            visited1 = list(visited)
            svars1 = list(svars)
            sym_exec_block(left_branch, visited1, stack1, mem1, svars1)

        solver.pop()  # POP SOLVER CONTEXT

        solver.push()
        negated_branch_expression = simplify(Not(branch_expression))
        solver.add(negated_branch_expression)

        print "Branch expression: " + str(negated_branch_expression)
        raw_input("Press Enter to continue...\n")

        if solver.check() == unsat:   # CAN BE OPTIMIZED
            print "INFEASIBLE PATH DETECTED"
            raw_input("Press Enter to continue...\n")
        else:
            right_branch = vertices[start].get_falls_to()
            stack1 = list(stack)
            mem1 = dict(mem)
            visited1 = list(visited)
            svars1 = list(svars)
            sym_exec_block(right_branch, visited1, stack1, mem1, svars1)

        solver.pop()  # POP SOLVER CONTEXT
    else:
        raise Exception('Unknown Jump-Type')


# evaluating an instruction
def sym_exec_ins(start, instr, stack, mem, svars):
    instr_parts = str.split(instr, ' ')
    if instr_parts[0].startswith('PUSH', 0):  # this is a push instruction
        pushed_value = int(instr_parts[1], 16)
        stack.insert(0, pushed_value)
    elif instr_parts[0] == "MSTORE":
        if len(stack) > 1:
            stored_address = stack.pop(0)
            stored_value = stack.pop(0)
            if isinstance(stored_address, (int, long)):
                mem[stored_address] = stored_value  # note that the stored_value could be unknown
            else:
                mem.clear()  # very conservative
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "EXP":
        if len(stack) > 1:
            base = stack.pop(0)
            exponent = stack.pop(0)
            computed = base ** exponent
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "ADD":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            computed = first + second
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MUL":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            computed = first * second
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SUB":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            computed = first - second
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "DIV":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            computed = first / second
            stack.insert(0, computed)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "MOD":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            computed = first % second
            stack.insert(0, computed)
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
                sym_expression = (first == second)
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "SGT":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
                if first > second:
                    stack.insert(0, 1)
                else:
                    stack.insert(0, 0)
            else:
                sym_expression = (first > second)
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "ISZERO":
        if len(stack) > 0:
            first = stack.pop(0)
            if isinstance(first, (int, long)):
                if first == 0:
                    stack.insert(0, 1)
                else:
                    stack.insert(0, 0)
            else:
                sym_expression = Not(first)
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "NOT":
        if len(stack) > 0:
            first = stack.pop(0)
            if isinstance(first, (int, long)):
                complement = -1 - first
                stack.insert(0, complement)
            else:
                sym_expression = function_not(first)
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "AND":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
                computed = first & second
                stack.insert(0, computed)
            else:
                sym_expression = function_and(first, second)
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "OR":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
                computed = first | second
                stack.insert(0, computed)
            else:
                sym_expression = function_or(first, second)
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "XOR":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if isinstance(first, (int, long)) and isinstance(second, (int, long)):
                computed = first ^ second
                stack.insert(0, computed)
            else:
                sym_expression = function_xor(first, second)
                stack.insert(0, sym_expression)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "JUMPDEST":
        pass
    elif instr_parts[0] == "CALLDATALOAD":  # from input data from environment
        if len(stack) > 0:
            position = stack.pop(0)
            new_var_name = gen.gen_data_var(position)
            svars.append(new_var_name)
            new_var = Int(new_var_name)
            stack.insert(0, new_var)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0].startswith("DUP", 0):
        position = int(instr_parts[0][3:], 10) - 1
        if len(stack) > position:
            duplicate = stack[position]
            stack.insert(0, duplicate)
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0].startswith("SWAP", 0):
        position = int(instr_parts[0][4:], 10)
        if len(stack) > position:
            temp = stack[position]
            stack[position] = stack[0]
            stack[0] = temp
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
            branch_expression = False
            if isinstance(flag, (int, long)):
                if flag != 0:
                    branch_expression = True
            else:
                branch_expression = (True == flag)
            vertices[start].set_branch_expression(branch_expression)
            if target_address not in edges[start]:
                edges[start].append(target_address)
        else:
            raise ValueError('STACK underflow')
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
                svars.append(new_var_name)
                new_var = Int(new_var_name)
                stack.insert(0, new_var)
                mem[address] = new_var
    elif instr_parts[0] == "RETURN":
        if len(stack) > 1:
            stack.pop(0)
            stack.pop(0)
            # TODO
            pass
        else:
            raise ValueError('STACK underflow')
    elif instr_parts[0] == "STOP":
        return
    elif instr_parts[0] == "SUICIDE":
        # TODO
        return
    else:
        print "UNKNOWN INSTRUCTION: " + instr_parts[0]
        raise Exception('UNKNOWN INSTRUCTION')

    print "DEBUG INFO: "
    print "EXECUTED: " + instr
    print_state(start, stack, mem)


def print_state(block_address, stack, mem):
    print "Address: %d" % block_address
    print str(stack)
    print str(mem)


main()
