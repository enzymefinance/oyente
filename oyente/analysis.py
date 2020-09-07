import logging
import math
import six
from opcodes import *
from z3 import *
from z3.z3util import *
from vargenerator import *
from utils import *
import global_params

log = logging.getLogger(__name__)

# THIS IS TO DEFINE A SKELETON FOR ANALYSIS
# FOR NEW TYPE OF ANALYSIS: add necessary details to the skeleton functions

def set_cur_file(c_file):
    global cur_file
    cur_file = c_file

def init_analysis():
    analysis = {
        "gas": 0,
        "gas_mem": 0,
        "money_flow": [("Is", "Ia", "Iv")],  # (source, destination, amount)
        "reentrancy_bug":[],
        "money_concurrency_bug": [],
        "time_dependency_bug": {}
    }
    return analysis


# Money flow: (source, destination, amount)

def display_analysis(analysis):
    log.debug("Money flow: " + str(analysis["money_flow"]))

# Check if this call has the Reentrancy bug
# Return true if it does, false otherwise
def check_reentrancy_bug(path_conditions_and_vars, stack, global_state):
    path_condition = path_conditions_and_vars["path_condition"]
    new_path_condition = []
    for expr in path_condition:
        if not is_expr(expr):
            continue
        list_vars = get_vars(expr)
        for var in list_vars:
            # check if a var is global
            if is_storage_var(var):
                pos = get_storage_position(var)
                if pos in global_state['Ia']:
                    new_path_condition.append(var == global_state['Ia'][pos])
    transfer_amount = stack[2]
    if isSymbolic(transfer_amount) and is_storage_var(transfer_amount):
        pos = get_storage_position(transfer_amount)
        if pos in global_state['Ia']:
            new_path_condition.append(global_state['Ia'][pos] != 0)
    if global_params.DEBUG_MODE:
        log.info("=>>>>>> New PC: " + str(new_path_condition))

    solver = Solver()
    solver.set("timeout", global_params.TIMEOUT)
    solver.add(path_condition)
    solver.add(new_path_condition)
    # 2300 is the outgas used by transfer and send.
    # If outgas > 2300 when using call.gas.value then the contract will be considered to contain reentrancy bug
    solver.add(stack[0] > 2300)
    # transfer_amount > deposit_amount => reentrancy
    solver.add(stack[2] > BitVec('Iv', 256))
    # if it is not feasible to re-execute the call, its not a bug
    ret_val = not (solver.check() == unsat)
    if global_params.DEBUG_MODE:
        log.info("Reentrancy_bug? " + str(ret_val))
    return ret_val

def calculate_gas(opcode, stack, mem, global_state, analysis, solver):
    gas_increment = get_ins_cost(opcode) # base cost
    gas_memory = analysis["gas_mem"]
    # In some opcodes, gas cost is not only depend on opcode itself but also current state of evm
    # For symbolic variables, we only add base cost part for simplicity
    if opcode in ("LOG0", "LOG1", "LOG2", "LOG3", "LOG4") and len(stack) > 1:
        if isReal(stack[1]):
            gas_increment += GCOST["Glogdata"] * stack[1]
    elif opcode == "EXP" and len(stack) > 1:
        if isReal(stack[1]) and stack[1] > 0:
            gas_increment += GCOST["Gexpbyte"] * (1 + math.floor(math.log(stack[1], 256)))
    elif opcode == "EXTCODECOPY" and len(stack) > 2:
        if isReal(stack[2]):
            gas_increment += GCOST["Gcopy"] * math.ceil(stack[2] / 32)
    elif opcode in ("CALLDATACOPY", "CODECOPY") and len(stack) > 3:
        if isReal(stack[3]):
            gas_increment += GCOST["Gcopy"] * math.ceil(stack[3] / 32)
    elif opcode == "SSTORE" and len(stack) > 1:
        if isReal(stack[1]):
            try:
                try:
                    storage_value = global_state["Ia"][int(stack[0])]
                except:
                    storage_value = global_state["Ia"][str(stack[0])]
                # when we change storage value from zero to non-zero
                if storage_value == 0 and stack[1] != 0:
                    gas_increment += GCOST["Gsset"]
                else:
                    gas_increment += GCOST["Gsreset"]
            except: # when storage address at considered key is empty
                if stack[1] != 0:
                    gas_increment += GCOST["Gsset"]
                elif stack[1] == 0:
                    gas_increment += GCOST["Gsreset"]
        else:
            try:
                try:
                    storage_value = global_state["Ia"][int(stack[0])]
                except:
                    storage_value = global_state["Ia"][str(stack[0])]
                solver.push()
                solver.add(Not( And(storage_value == 0, stack[1] != 0) ))
                if solver.check() == unsat:
                    gas_increment += GCOST["Gsset"]
                else:
                    gas_increment += GCOST["Gsreset"]
                solver.pop()
            except Exception as e:
                if str(e) == "canceled":
                    solver.pop()
                solver.push()
                solver.add(Not( stack[1] != 0 ))
                if solver.check() == unsat:
                    gas_increment += GCOST["Gsset"]
                else:
                    gas_increment += GCOST["Gsreset"]
                solver.pop()
    elif opcode == "SUICIDE" and len(stack) > 1:
        if isReal(stack[1]):
            address = stack[1] % 2**160
            if address not in global_state:
                gas_increment += GCOST["Gnewaccount"]
        else:
            address = str(stack[1])
            if address not in global_state:
                gas_increment += GCOST["Gnewaccount"]
    elif opcode in ("CALL", "CALLCODE", "DELEGATECALL") and len(stack) > 2:
        # Not fully correct yet
        gas_increment += GCOST["Gcall"]
        if isReal(stack[2]):
            if stack[2] != 0:
                gas_increment += GCOST["Gcallvalue"]
        else:
            solver.push()
            solver.add(Not (stack[2] != 0))
            if check_sat(solver) == unsat:
                gas_increment += GCOST["Gcallvalue"]
            solver.pop()
    elif opcode == "SHA3" and isReal(stack[1]):
        pass # Not handle


    #Calculate gas memory, add it to total gas used
    length = len(mem.keys()) # number of memory words
    new_gas_memory = GCOST["Gmemory"] * length + (length ** 2) // 512
    gas_increment += new_gas_memory - gas_memory

    return (gas_increment, new_gas_memory)

def update_analysis(analysis, opcode, stack, mem, global_state, path_conditions_and_vars, solver):
    gas_increment, gas_memory = calculate_gas(opcode, stack, mem, global_state, analysis, solver)
    analysis["gas"] += gas_increment
    analysis["gas_mem"] = gas_memory

    if opcode == "CALL":
        recipient = stack[1]
        transfer_amount = stack[2]
        if isReal(transfer_amount) and transfer_amount == 0:
            return
        if isSymbolic(recipient):
            recipient = simplify(recipient)

        reentrancy_result = check_reentrancy_bug(path_conditions_and_vars, stack, global_state)
        analysis["reentrancy_bug"].append(reentrancy_result)

        analysis["money_concurrency_bug"].append(global_state["pc"])
        analysis["money_flow"].append( ("Ia", str(recipient), str(transfer_amount)))
    elif opcode == "SUICIDE":
        recipient = stack[0]
        if isSymbolic(recipient):
            recipient = simplify(recipient)
        analysis['money_concurrency_bug'].append(global_state['pc'])
        analysis["money_flow"].append(("Ia", str(recipient), "all_remaining"))

# Check if it is possible to execute a path after a previous path
# Previous path has prev_pc (previous path condition) and set global state variables as in gstate (only storage values)
# Current path has curr_pc
def is_feasible(prev_pc, gstate, curr_pc):
    curr_pc = list(curr_pc)
    new_pc = []
    for var in get_all_vars(curr_pc):
        if is_storage_var(var):
            pos = get_storage_position(var)
            if pos in gstate:
                new_pc.append(var == gstate[pos])
    curr_pc += new_pc
    curr_pc += prev_pc
    solver = Solver()
    solver.set("timeout", global_params.TIMEOUT)
    solver.add(curr_pc)
    if solver.check() == unsat:
        return False
    else:
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

    # rename global variables in path i
    set_of_pcs, statei = rename_vars(pathi, statei)
    log.debug("Set of PCs after renaming global vars" + str(set_of_pcs))
    log.debug("Global state values in path " + str(i) + " after renaming: " + str(statei))
    if is_feasible(set_of_pcs, statei, pathj):
        return False
    else:
        return True


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
            solver.set("timeout", global_params.TIMEOUT)
            solver.add(tx_cd)

            if solver.check() == sat:
                return 1
        except Exception as e:
            return 1
    return 0
