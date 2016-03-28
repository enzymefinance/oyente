# return true if the two paths have different flows of money
# later on we may want to return more meaningful output: e.g. if the concurrency changes
# the amount of money or the recipient.
from z3 import *
from z3util import get_vars


# detect if two flows are not really having race condition
# 1. We first start with a simple check to see if a path edit some storage variable
# which makes the other path infeasible
# 2. We then check if two paths cannot be executed next to each other, for example they
# are two paths yielded from this branch condition ``if (locked)"
# 3. More checks are to come
def is_false_positive(flow1, flow2):
    return 0


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
        solver = Solver()
        solver.push()
        solver.add(tx_cd)

        if solver.check() == sat:
            solver.pop()
            return 1
        solver.pop()
    return 0


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


# check if a variable is a storage address in a contract
def is_storage_var(var):
    if isinstance(var, (int, long)):
        return True
    else:
        return isinstance(var, str) and var.startswith("Ia_store_")


# copy only storage values/ variables from a given global state
# TODO: add balance in the future
def copy_global_values(global_state):
    new_gstate = {}
    for var in global_state["Ia"]:
        if is_storage_var(var):
            new_gstate[var] = global_state["Ia"][var]
