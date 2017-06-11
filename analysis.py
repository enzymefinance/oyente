import logging
import math
from opcodes import *
from z3 import *
from z3.z3util import *
from vargenerator import *
from utils import *
import global_params

log = logging.getLogger(__name__)

# THIS IS TO DEFINE A SKELETON FOR ANALYSIS
# FOR NEW TYPE OF ANALYSIS: add necessary details to the skeleton functions
cur_file = ""
reported = False
reentrancy_report_file = "re_report.report"

def set_cur_file(c_file):
    global cur_file
    cur_file = c_file

def init_analysis():
    analysis = {
        "gas": 0,
        "gas_mem": 0,
        "money_flow": [("Is", "Ia", "Iv")],  # (source, destination, amount)
        "sload": [],
        "sstore": {},
        "reentrancy_bug":[]
    }
    return analysis


# Money flow: (source, destination, amount)

def display_analysis(analysis):
    logging.debug("Money flow: " + str(analysis["money_flow"]))

# Check if this call has the Reentrancy bug
# Return true if it does, false otherwise
def check_reentrancy_bug(path_conditions_and_vars, global_state):
    path_condition = path_conditions_and_vars["path_condition"]
    new_path_condition = []
    for expr in path_condition:
        if not is_expr(expr):
            continue
        list_vars = get_vars(expr)
        for var in list_vars:
            var_name = var.decl().name()
            # check if a var is global
            if var_name.startswith("Ia_store_"):
                storage_key = var_name.split("Ia_store_")[1]
                if storage_key in global_state["Ia"]:
                    new_path_condition.append(var == global_state["Ia"][storage_key])
    log.info("=>>>>>> New PC: " + str(new_path_condition))

    solver = Solver()
    solver.set("timeout", global_params.TIMEOUT)
    solver.push()
    solver.add(path_condition)
    solver.add(new_path_condition)
    # if it is not feasible to re-execute the call, its not a bug
    ret_val = not (solver.check() == unsat)
    solver.pop()
    log.info("Reentrancy_bug? " + str(ret_val))
    global reported
    if not reported:
        with open(reentrancy_report_file, 'a') as r_report:
            r_report.write('\n'+cur_file)
        reported = True
    return ret_val

def calculate_gas(opcode, stack, mem, global_state, analysis, solver):
    gas_increment = get_ins_cost(opcode) # base cost
    gas_memory = analysis["gas_mem"]
    # In some opcodes, gas cost is not only depend on opcode itself but also current state of evm
    # For symbolic variables, we only add base cost part for simplicity
    if opcode in ("LOG0", "LOG1", "LOG2", "LOG3", "LOG4") and len(stack) > 1:
        if isinstance(stack[1], (int, long)):
            gas_increment += GCOST["Glogdata"] * stack[1]
    elif opcode == "EXP" and len(stack) > 1:
        if isinstance(stack[1], (int, long)) and stack[1] > 0:
            gas_increment += GCOST["Gexpbyte"] * (1 + math.floor(math.log(stack[1], 256)))
    elif opcode == "EXTCODECOPY" and len(stack) > 2:
        if isinstance(stack[2], (int, long)):
            gas_increment += GCOST["Gcopy"] * math.ceil(stack[2] / 32)
    elif opcode in ("CALLDATACOPY", "CODECOPY") and len(stack) > 3:
        if isinstance(stack[3], (int, long)):
            gas_increment += GCOST["Gcopy"] * math.ceil(stack[3] / 32)
    elif opcode == "SSTORE" and len(stack) > 1:
        if isinstance(stack[1], (int, long)):
            try:
                storage_value = global_state['Ia'][str(stack[0])]
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
                storage_value = global_state['Ia'][str(stack[0])]
                solver.push()
                solver.add(Not( And(storage_value == 0, stack[1] != 0) ))
                if solver.check() == unsat:
                    gas_increment += GCOST["Gsset"]
                else:
                    gas_increment += GCOST["Gsreset"]
                solver.pop()
            except:
                solver.push()
                solver.add(Not( stack[1] != 0 ))
                if solver.check() == unsat:
                    gas_increment += GCOST["Gsset"]
                else:
                    gas_increment += GCOST["Gsreset"]
                solver.pop()
    elif opcode == "SUICIDE" and len(stack) > 1:
        if isinstance(stack[1], (int, long)):
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
        if isinstance(stack[2], (int, long)):
            if stack[2] != 0:
                gas_increment += GCOST["Gcallvalue"]
        else:
            solver.push()
            solver.add(Not (stack[2] != 0))
            if solver.check() == unsat:
                gas_increment += GCOST["Gcallvalue"]
            solver.pop()
    elif opcode == "SHA3" and isinstance(stack[1], (int, long)):
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
        reentrancy_result = check_reentrancy_bug(path_conditions_and_vars, global_state)
        analysis["reentrancy_bug"].append(reentrancy_result)
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
    elif global_params.DATA_FLOW:
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
                log.debug(type(stored_address))
                # a temporary fix, not a good one.
                # TODO move to z3 4.4.2 in which BitVecRef is hashable
                if not isinstance(stored_address, (int, long)):
                    stored_address = str(stored_address)
                log.debug("storing value " + str(stored_value) + " to address " + str(stored_address))
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
    solver = Solver()
    solver.set("timeout", global_params.TIMEOUT)
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

    # rename global variables in path i
    set_of_pcs, statei = rename_vars(pathi, statei)
    log.debug("Set of PCs after renaming global vars" + str(set_of_pcs))
    log.debug("Global state values in path " + str(i) + " after renaming: " + str(statei))
    if is_feasible(set_of_pcs, statei, pathj):
        return 0
    else:
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
            solver.set("timeout", global_params.TIMEOUT)
            solver.push()
            solver.add(tx_cd)

            if solver.check() == sat:
                solver.pop()
                return 1
            solver.pop()
        except Exception as e:
            return 1
    return 0
