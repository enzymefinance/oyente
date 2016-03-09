import sys
import tokenize
from tokenize import NUMBER, NAME, NEWLINE
from neo4jrestclient.client import GraphDatabase
from basicblock import BasicBlock


db = GraphDatabase("http://localhost:7474", username="neo4j", password="1.66Planck")

labels = db.labels.create("JumpDests")
label_dict = {}  # capturing the address of the first statement of each basic block
unknown = db.nodes.create(color="Black", name=("unknown address"))
label_dict[-1] = unknown
labels.add(unknown)


end_ins_dict = {}  # capturing the last statement of each basic block
call_dict = {}
instructions = {}
jump_type = {}
vertices = {}
edges = {}


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
            elif tok_string == "STOP" or tok_string == "RETURN":
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
            jump_type[key] = "falls to"


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
    add_easy_jumps()
    # TODO
    execute()
    visualize_with_ne4j()


def visualize_with_ne4j():
    for address in vertices:
        hex_address = format(address, 'x')
        new_node = db.nodes.create(name=("0x"+hex_address))
        label_dict[address] = new_node
        labels.add(new_node)

    for address in vertices:
        type_of_edge = vertices[address].get_block_type()
        for target in edges[address]:
            label_dict[address].relationships.create(type_of_edge, label_dict[target])


def add_falls_to():
    key_list = sorted(jump_type.keys())
    length = len(key_list)

    for i, key in enumerate(key_list):
        if jump_type[key] != "terminal" and jump_type[key] != "unconditional" and i+1 < length:
            edges[key].append(key_list[i+1])


def add_easy_jumps():
    reverse_instructions = sorted(instructions.keys(), reverse=True)
    for key in jump_type:
        if jump_type[key] == "conditional" or jump_type[key] == "unconditional":
            jump_instr = end_ins_dict[key]
            # print "JUMP ADDRESS: %d" % jump_instr
            previous_ins_address = reverse_instructions[reverse_instructions.index(jump_instr) + 1]
            # print "PREVIOUS INS: %d" % previous_ins_address
            instruction_parts = str.split(instructions[previous_ins_address], ' ')
            if len(instruction_parts) > 1 and instruction_parts[0].startswith('PUSH', 0):
                target_address = int(instruction_parts[1], 16)
                edges[key].append(target_address)
                # print "jumping to %d" % target_address
            else:
                print "WARNING: looking for a PUSH instruction, found %s" % instructions[previous_ins_address]
                print "WARNING: cannot resolve the jump at %d" % jump_instr
                edges[key].append(-1)


def execute():
    sorted_addresses = sorted(vertices.keys())
    # executing, starting from beginning
    for address in sorted_addresses:
        stack = []
        mem = {}
        visited = set([])
        execute_block(address, stack, visited, mem)


def print_state(block_address, stack, mem):
    print "Address: %d" % block_address
    print str(stack)
    print str(mem)


# partially evaluating a block from the start address
def execute_block(start, stack, visited, mem):
    # visited is a set of visited block addresses
    # stack captures partially the execution stack, we only know about some elements on the top

    # do not visit node that has been visited in the path history
    # e.g. in case of loops
    if start in visited or start < 0:
        return
    block_ins = vertices[start].get_instructions()
    for instr in block_ins:
        execute_ins(start, instr, stack, mem)
    visited.add(start)
    for successor in edges[start]:
        stack1 = list(stack)
        mem1 = dict(mem)
        visited1 = visited.copy()
        execute_block(successor, stack1, visited1, mem1)


# partially evaluating an instruction
def execute_ins(start, instr, stack, mem):
    instr_parts = str.split(instr, ' ')
    if instr_parts[0].startswith('PUSH', 0):  # this is a push instruction
        pushed_value = int(instr_parts[1], 16)
        stack.insert(0, pushed_value)
    elif instr_parts[0] == "MSTORE":
        if len(stack) > 1:
            stored_address = stack.pop(0)
            stored_value = stack.pop(0)
            if stored_address == "unknown":
                mem.clear()  # very conservative
            else:
                mem[stored_address] = stored_value  # note that the stored_value could be unknown
        elif len(stack) == 1:
            stored_address = stack.pop()
            if stored_address == "unknown":
                mem.clear()  # very conservative
            else:
                mem[stored_address] = "unknown"
        else:  # the stack is empty
            mem.clear()
    elif instr_parts[0] == "EXP":
        if len(stack) > 1:
            base = stack.pop(0)
            exponent = stack.pop(0)
            if base == "unknown" or exponent == "unknown":
                stack.insert(0, "unknown")
            else:
                stack.insert(0, base ** exponent)
        else:
            del stack[:]
            stack.insert(0, "unknown")
    elif instr_parts[0] == "ADD":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if first == "unknown" or second == "unknown":
                stack.insert(0, "unknown")
            else:
                stack.insert(0, first + second)
        else:
            del stack[:]
            stack.insert(0, "unknown")
    elif instr_parts[0] == "MUL":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if first == "unknown" or second == "unknown":
                stack.insert(0, "unknown")
            else:
                stack.insert(0, first * second)
        else:
            del stack[:]
            stack.insert(0, "unknown")
    elif instr_parts[0] == "SUB":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if first == "unknown" or second == "unknown":
                stack.insert(0, "unknown")
            else:
                stack.insert(0, first - second)
        else:
            del stack[:]
            stack.insert(0, "unknown")
    elif instr_parts[0] == "DIV":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if first == "unknown" or second == "unknown":
                stack.insert(0, "unknown")
            else:
                stack.insert(0, first // second)
        else:
            del stack[:]
            stack.insert(0, "unknown")
    elif instr_parts[0] == "MOD":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if first == "unknown" or second == "unknown":
                stack.insert(0, "unknown")
            else:
                if second == 0:
                    stack.insert(0, 0)
                else:
                    stack.insert(0, first % second)
        else:
            del stack[:]
            stack.insert(0, "unknown")
    elif instr_parts[0] == "EQ":
        if len(stack) > 1:
            first = stack.pop(0)
            second = stack.pop(0)
            if first == "unknown" or second == "unknown":
                stack.insert(0, "unknown")
            else:
                if first == second:
                    stack.insert(0, 1)
                else:
                    stack.insert(0, 0)
        else:
            del stack[:]
            stack.insert(0, "unknown")
    elif instr_parts[0] == "JUMPDEST":
        pass
    elif instr_parts[0] == "CALLDATALOAD":  # from input data from environment
        if len(stack) > 0:
            stack.pop(0)
        stack.insert(0, "unknown")
        # We do not know about the input data
        # in the future, should proceed by creating new symbolic variable
    elif instr_parts[0].startswith("DUP", 0):
        position = int(instr_parts[0][3:], 10) - 1
        if len(stack) > position:
            duplicate = stack[position]
            stack.insert(0, duplicate)
        else:
            stack.insert(0, "unknown")
    elif instr_parts[0].startswith("SWAP", 0):
        position = int(instr_parts[0][4:], 10)
        length = len(stack)
        while length <= position:  # increase the stack with unknowns (at the bottom)
            stack.append("unknown")
            length += 1
        temp = stack[position]
        stack[position] = stack[0]
        stack[0] = temp
    elif instr_parts[0] == "JUMP":
        if len(stack) > 0:
            target_address = stack.pop(0)
            if target_address != "unknown" and target_address not in edges[start]:
                edges[start].append(target_address)
                if -1 in edges[start]:
                    edges[start].remove(-1)
    elif instr_parts[0] == "JUMPI":
        if len(stack) > 0:
            target_address = stack.pop(0)
            if len(stack) > 0:
                stack.pop(0)
            if target_address != "unknown" and target_address not in edges[start]:
                edges[start].append(target_address)
                if -1 in edges[start]:
                    edges[start].remove(-1)
    elif instr_parts[0] == "POP":
        if len(stack) > 0:
            stack.pop(0)
    elif instr_parts[0] == "MLOAD":
        if len(stack) > 0:
            address = stack.pop(0)
            if address != "unknown" and address in mem:
                value = mem[address]
                stack.insert(0, value)
            else:
                stack.insert(0, "unknown")
    elif instr_parts[0] == "RETURN":
        if len(stack) > 1:
            begin_address = stack.pop(0)
            end_address = stack.pop(0)
            if end_address != "unknown":
               end_address -= 1
            # TODO
            pass
    else:
        print "UNKNOWN INSTRUCTION: " + instr_parts[0]

    print "DEBUG INFO: "
    print "EXECUTED: " + instr
    print_state(start, stack, mem)


if __name__ == '__main__':
    main()