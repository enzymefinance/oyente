from opcodes import *
from math import *
from z3 import *
from z3util import *
from vargenerator import *
from utils import *
from global_params import *

# THIS IS TO DEFINE A SKELETON FOR ANALYSIS
# FOR NEW TYPE OF ANALYSIS: add necessary details to the skeleton functions


def init_analysis():
    analysis = {
        "gas": 0,
        "gas_mem": 0,
        "money_flow": [("Is", "Ia", "Iv")],  # (source, destination, amount)
        "sload": [],
        "sstore": {}
    }
    return analysis


# Money flow: (source, destination, amount)

def display_analysis(analysis):
    # if PRINT_MODE: print "Gas paid for execution: %d" % analysis["gas"]
    # if PRINT_MODE: print "Gas paid for memory usage: %d" % analysis["gas_mem"]
    if PRINT_MODE: print "Money flow: " + str(analysis["money_flow"])


def update_analysis(analysis, opcode, stack, mem, global_state, path_conditions_and_vars):
    gas_increment = get_ins_cost(opcode)
    if opcode in ("LOG0", "LOG1", "LOG2", "LOG3", "LOG4"):
        gas_increment += GCOST["Glogdata"] * stack[1]
    elif opcode == "EXP" and isinstance(stack[1], (int, long)) and stack[1] > 0:
        gas_increment += GCOST["Gexpbyte"] * (1 + floor(log(stack[1], 256)))
    elif opcode == "SSTORE":
        # TODO
        pass

    analysis["gas"] = analysis["gas"] + gas_increment

    # I DON'T THINK THIS FORMULA IS CORRECT YET
    length = len(mem.keys())
    analysis["gas_mem"] = GCOST["Gmemory"] * length + (length ** 2) // 512

    if opcode == "CALL":
        print "THIS IS A CALLLLLLLLLL"
        print str(path_conditions_and_vars)
        print str(global_state)
        recipient = stack[1]
        transfer_amount = stack[2]
        if isinstance(transfer_amount, (int, long)) and transfer_amount == 0:
            return
        if not isinstance(recipient, (int, long)):
            recipient = simplify(recipient)
        analysis["money_flow"].append(("Ia", str(recipient), transfer_amount))
    elif opcode == "SUICIDE":
        recipient = stack[0]
        if not isinstance(recipient, (int, long)):
            recipient = simplify(recipient)
        analysis["money_flow"].append(("Ia", str(recipient), "all_remaining"))
    # this is for data flow
    elif DATA_FLOW:
        if opcode == "SLOAD":
            if len(stack) > 0:
                address = stack[0]
                if not isinstance(address, (int, long)):
                    address = str(address)
                if address not in analysis["sload"]:
                    analysis["sload"].append(address)
            else:
                raise ValueError('STACK underflow')
        elif opcode == "SSTORE":
            if len(stack) > 1:
                stored_address = stack[0]
                stored_value = stack[1]
                if PRINT_MODE: print type(stored_address)
                # a temporary fix, not a good one.
                # TODO move to z3 4.4.2 in which BitVecRef is hashable
                if not isinstance(stored_address, (int, long)):
                    stored_address = str(stored_address)
                if PRINT_MODE: print "storing value " + str(stored_value) + " to address " + str(stored_address)
                if stored_address in analysis["sstore"]:
                    # recording the new values of the item in storage
                    analysis["sstore"][stored_address].append(stored_value)
                else:
                    analysis["sstore"][stored_address] = [stored_value]
            else:
                raise ValueError('STACK underflow')


# Check if it is possible to execute a path after a previous path
# Previous path has prev_pc (previous path condition) and set global state variables as in gstate (only storage values)
# Current path has curr_pc
def is_feasible(prev_pc, gstate, curr_pc):
    vars_mapping = {}
    new_pc = list(curr_pc)
    for expr in new_pc:
        list_vars = get_vars(expr)
        for var in list_vars:
            vars_mapping[var.decl().name()] = var
    new_pc += prev_pc
    gen = Generator()
    for storage_address in gstate:
        var = gen.gen_owner_store_var(storage_address)
        if var in vars_mapping:
            new_pc.append(vars_mapping[var] == gstate[storage_address])
    # if PRINT_MODE: print "Final path condition: ", new_pc
    solver = Solver()
    solver.push()
    solver.add(new_pc)
    if solver.check() == unsat:
        solver.pop()
        return False
    else:
        solver.pop()
        return True


# detect if two flows are not really having race condition, i.e. check if executing path j
# after path i is possible.
# 1. We first start with a simple check to see if a path edit some storage variable
# which makes the other path infeasible
# 2. We then check if two paths cannot be executed next to each other, for example they
# are two paths yielded from this branch condition ``if (locked)"
# 3. More checks are to come
def is_false_positive(i, j, all_gs, path_conditions):
    pathi = path_conditions[i]
    pathj = path_conditions[j]
    statei = all_gs[i]
    # statej = all_gs[j]
    # if PRINT_MODE: print "Path condition " + str(i) + ": " + str(pathi)
    # if PRINT_MODE: print "Path condition " + str(j) + ": " + str(pathj)
    # if PRINT_MODE: print "Global state values in path " + str(i) + ": " + str(statei)
    # if PRINT_MODE: print "Global state values in path " + str(j) + ": " + str(statej)


    # if PRINT_MODE: print "Set of PCs having only global vars" + str(set_of_pcs)
    # rename global variables in path i
    set_of_pcs, statei = rename_vars(pathi, statei)
    if PRINT_MODE: print "Set of PCs after renaming global vars" + str(set_of_pcs)
    if PRINT_MODE: print "Global state values in path " + str(i) + " after renaming: " + str(statei)
    if is_feasible(set_of_pcs, statei, pathj):
        # if PRINT_MODE: print "Its possible to execute path ", i, " after path ", j
        return 0
    else:
        # if PRINT_MODE: print "Its not possible to execute path ", i, " after path ", j
        return 1


# Simple check if two flows of money are different
def is_diff(flow1, flow2):
    if len(flow1) != len(flow2):
        return 1
    n = len(flow1)
    for i in range(n):
        if flow1[i] == flow2[i]:
            continue
        try:
            tx_cd = Or(Not(flow1[i][0] == flow2[i][0]),
                       Not(flow1[i][1] == flow2[i][1]),
                       Not(flow1[i][2] == flow2[i][2]))
            solver = Solver()
            solver.push()
            solver.add(tx_cd)

            if solver.check() == sat:
                solver.pop()
                return 1
            solver.pop()
        except Exception as e:
            return 1
    return 0
