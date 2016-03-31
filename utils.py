# return true if the two paths have different flows of money
# later on we may want to return more meaningful output: e.g. if the concurrency changes
# the amount of money or the recipient.
from z3 import *
from z3util import get_vars
from vargenerator import Generator

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
# currently accept only int addresses in the storage
def is_storage_var(var):
    return isinstance(var, (int, long))
    #     return True
    # else:
    #     return isinstance(var, str) and var.startswith("Ia_store_")


# copy only storage values/ variables from a given global state
# TODO: add balance in the future
def copy_global_values(global_state):
    new_gstate = {}
    gen = Generator()

    for var in global_state["Ia"]:
        if is_storage_var(var):
            new_gstate[gen.gen_owner_store_var(var)] = global_state["Ia"][var]
    return new_gstate


# check if a variable is in an expression
def is_in_expr(var, expr):
    list_vars = get_vars(expr)
    set_vars = set(i.decl().name() for i in list_vars)
    return var in set_vars


# check if an expression has only storage variables
def has_only_storage_vars(expr):
    list_vars = get_vars(expr)
    set_vars = set(i.decl().name() for i in list_vars)
    for var in set_vars:
        if not var.startswith("Ia_store_"):
            return False
    return True


# rename global variables to distinguish variables in two different paths.
# e.g. Ia_store_0 in path i becomes Ia_store_0i
def rename_global_vars(pcs, global_states):
    ret_pcs = []
    vars_mapping = {}
    for expr in pcs:
        list_vars = get_vars(expr)
        for var in list_vars:
            if var in vars_mapping:
                expr = substitute(expr, (var, vars_mapping[var]))
                continue
            var_name = var.decl().name()
            if var_name in global_states:
                # position = int(var_name.split('_')[len(var_name.split('_'))-1])
                new_var_name = var_name + '_old'
                new_var = BitVec(new_var_name, 256)
                vars_mapping[var] = new_var
                expr = substitute(expr, (var, vars_mapping[var]))
        ret_pcs.append(expr)

    ret_gs = {}
    # replace variable in storage expression
    for storage_var in global_states:
        expr = global_states[storage_var]
        list_vars = get_vars(expr)
        for var in list_vars:
            if var in vars_mapping:
                expr = substitute(expr, (var, vars_mapping[var]))
                continue
            var_name = var.decl().name()
            if var_name in global_states:
                new_var_name = var_name + '_old'
                new_var = BitVec(new_var_name, 256)
                vars_mapping[var] = new_var
                expr = substitute(expr, (var, vars_mapping[var]))
        ret_gs[storage_var] = expr

    return ret_pcs, ret_gs
