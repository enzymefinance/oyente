# return true if the two paths have different flows of money
# later on we may want to return more meaningful output: e.g. if the concurrency changes
# the amount of money or the recipient.
from z3 import *
from z3util import get_vars
import json
import mmap
import os
import csv
import re
import difflib

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

    for var in global_state["Ia"]:
        if is_storage_var(var):
            new_gstate[var] = global_state["Ia"][var]
    return new_gstate


# check if a variable is in an expression
def is_in_expr(var, expr):
    list_vars = get_vars(expr)
    set_vars = set(i.decl().name() for i in list_vars)
    return var in set_vars


# check if an expression has any storage variables
def has_storage_vars(expr, storage_vars):
    list_vars = get_vars(expr)
    for var in list_vars:
        if var in storage_vars:
            return True
    return False


def get_all_vars(list_of_storage_exprs):
    ret_vars = []
    for expr in list_of_storage_exprs:
        ret_vars += get_vars(list_of_storage_exprs[expr])
    return ret_vars


# rename variables to distinguish variables in two different paths.
# e.g. Ia_store_0 in path i becomes Ia_store_0_old if Ia_store_0 is modified
# else we must keep Ia_store_0 if its not modified
def rename_vars(pcs, global_states):
    ret_pcs = []
    vars_mapping = {}

    for expr in pcs:
        list_vars = get_vars(expr)
        for var in list_vars:
            if var in vars_mapping:
                expr = substitute(expr, (var, vars_mapping[var]))
                continue
            var_name = var.decl().name()
            # check if a var is global
            if var_name.startswith("Ia_store_"):
                position = int(var_name.split('_')[len(var_name.split('_'))-1])
                # if it is not modified then keep the previous name
                if position not in global_states:
                    continue
            # otherwise, change the name of the variable
            new_var_name = var_name + '_old'
            new_var = BitVec(new_var_name, 256)
            vars_mapping[var] = new_var
            expr = substitute(expr, (var, vars_mapping[var]))
        ret_pcs.append(expr)

    ret_gs = {}
    # replace variable in storage expression
    for storage_addr in global_states:
        expr = global_states[storage_addr]
        # stupid z3 4.1 makes me add this line
        if is_expr(expr):
            list_vars = get_vars(expr)
            for var in list_vars:
                if var in vars_mapping:
                    expr = substitute(expr, (var, vars_mapping[var]))
                    continue
                var_name = var.decl().name()
                # check if a var is global
                if var_name.startswith("Ia_store_"):
                    position = int(var_name.split('_')[len(var_name.split('_'))-1])
                    # if it is not modified
                    if position not in global_states:
                        continue
                # otherwise, change the name of the variable
                new_var_name = var_name + '_old'
                new_var = BitVec(new_var_name, 256)
                vars_mapping[var] = new_var
                expr = substitute(expr, (var, vars_mapping[var]))
        ret_gs[storage_addr] = expr

    return ret_pcs, ret_gs


#split a file into smaller files
def split_dicts(filename, nsub = 500):
    with open(filename) as json_file:
        c = json.load(json_file)
        current_file = {}
        file_index = 1
        for u, v in c.iteritems():
            current_file[u] = v
            if len(current_file) == nsub:
                with open(filename.split(".")[0] + "_" + str(file_index) + '.json', 'w') as outfile:
                    json.dump(current_file, outfile)
                    file_index += 1
                    current_file.clear()
        if len(current_file):
            with open(filename.split(".")[0] + "_" + str(file_index) + '.json', 'w') as outfile:
                json.dump(current_file, outfile)
                current_file.clear()


def do_split_dicts():
    for i in range(11):
        split_dicts("contract" + str(i) + ".json")
        os.remove("contract" + str(i) + ".json")


def run_re_file(re_str, fn):
    size = os.stat(fn).st_size
    with open(fn, 'r') as tf:
        data = mmap.mmap(tf.fileno(), size, access=mmap.ACCESS_READ)
        return re.findall(re_str, data)


def get_contract_info(contract_addr):
    print "Getting info for contracts... " + contract_addr
    file_name1 = "tmp/" + contract_addr + "_txs.html"
    file_name2 = "tmp/" + contract_addr + ".html"
    # get number of txs
    txs = "unknown"
    value = "unknown"
    re_txs_value = r"<span>A total of (.+?) transactions found for address</span>"
    re_str_value = r"<td>ETH Balance:\n<\/td>\n<td>\n(.+?)\n<\/td>"
    try:
        txs = run_re_file(re_txs_value, file_name1)
        value = run_re_file(re_str_value, file_name2)
    except Exception as e:
        try:
            os.system("wget -O %s http://etherscan.io/txs?a=%s" % (file_name1, contract_addr))
            re_txs_value = r"<span>A total of (.+?) transactions found for address</span>"
            txs = run_re_file(re_txs_value, file_name1)

            # get balance
            re_str_value = r"<td>ETH Balance:\n<\/td>\n<td>\n(.+?)\n<\/td>"
            os.system("wget -O %s https://etherscan.io/address/%s" % (file_name2, contract_addr))
            value = run_re_file(re_str_value, file_name2)
        except Exception as e:
            pass
    return txs, value


def get_contract_stats(list_of_contracts):
    with open("concurr.csv", "w") as stats_file:
        fp = csv.writer(stats_file, delimiter=',')
        fp.writerow(["Contract address", "No. of paths", "No. of concurrency pairs",  "Balance", "No. of TXs", "Note"])
        with open(list_of_contracts, "r") as f:
            for contract in f.readlines():
                contract_addr = contract.split()[0]
                value, txs = get_contract_info(contract_addr)
                fp.writerow([contract_addr, contract.split()[1], contract.split()[2],
                             value, txs, contract.split()[3:]])


def get_time_dependant_contracts(list_of_contracts):
    with open("time.csv", "w") as stats_file:
        fp = csv.writer(stats_file, delimiter=',')
        fp.writerow(["Contract address", "Balance", "No. of TXs", "Note"])
        with open(list_of_contracts, "r") as f:
            for contract in f.readlines():
                if len(contract.strip()) == 0:
                    continue
                contract_addr = contract.split(".")[0].split("_")[1]
                txs, value = get_contract_info(contract_addr)
                fp.writerow([contract_addr, value, txs])


def get_distinct_contracts(list_of_contracts = "concurr.csv"):
    flag = []
    with open(list_of_contracts, "rb") as csvfile:
        contracts = csvfile.readlines()[1:]
        n =len(contracts)
        for i in range(n):
            flag.append(i) # mark which contract is similar to contract_i
        for i in range(n):
            if flag[i] != i:
                continue
            contract_i = contracts[i].split(",")[0]
            npath_i = int(contracts[i].split(",")[1])
            npair_i = int(contracts[i].split(",")[2])
            file_i = "stats/tmp_" + contract_i + ".evm"
            print " reading file " + file_i
            for j in range(i+1, n):
                if flag[j] != j:
                    continue
                contract_j = contracts[j].split(",")[0]
                npath_j = int(contracts[j].split(",")[1])
                npair_j = int(contracts[j].split(",")[2])
                if (npath_i == npath_j) and (npair_i == npair_j):
                    file_j = "stats/tmp_" + contract_j + ".evm"

                    with open(file_i, 'r') as f1, open(file_j, 'r') as f2:
                        code_i = f1.readlines()
                        code_j = f2.readlines()
                        if abs(len(code_i) - len(code_j)) >= 5:
                            continue
                        diff = difflib.ndiff(code_i, code_j)
                        ndiff = 0
                        for line in diff:
                            if line.startswith("+") or line.startswith("-"):
                                ndiff += 1
                        if ndiff < 10:
                            flag[j] = i
    print flag

