from subprocess import *
import json
import re
import os
import sys
from tqdm import tqdm

contracts = {}
opcodes = {}
callstack_error_contracts = []
cterror_balances = []

cbalancefile = json.load(open('../contracts/contract_data/contract_balance.json'))

write_out = False

# Disassemble individual contracts - disasm is the disassembly tool from go-ethereum/build/bin
def get_contract_disasm(inp):
    process = Popen("disasm", stdin=PIPE, stdout=PIPE, stderr=PIPE)
    process.stdin.write(inp+'\n')
    return process.communicate()[0]

def check_callstack_attack(disasm):
    problematic_instructions = ['CALL', 'CALLCODE']
    for i in xrange(0, len(disasm)):
        instruction = disasm[i]
        if instruction[1] in problematic_instructions:
            error = True
            for j in xrange(i+1, len(disasm)):
                if disasm[j][1] in problematic_instructions:
                    break
                if disasm[j][1] == 'ISZERO':
                    error = False
                    break
            if error == True: return True                
    return False

def update_stats_from_disasm(chash, ctx, inpinit, inpmain):
    jump_instructions = ["JUMP","JUMPI","CALL","CALLCODE"]
    pattern = r"([\d]+) +([A-Z]+)([\d]?){1}(?: +(?:=> )?(\d+)?)?"
    imain = re.findall(pattern, inpmain)
    iinit = re.findall(pattern, inpinit)
    ifull = imain+iinit

    # Check for callstack attack
    if check_callstack_attack(imain) or check_callstack_attack(iinit):
        if chash in cbalancefile:
            cterror_balances.append(cbalancefile[chash])
        else:
            cterror_balances.append(0)
        callstack_error_contracts.append(chash)

    # Extract opcode data
    used = []
    for instruction in ifull:
        opcode = instruction[1]
        if opcode not in opcodes:
        #     with open('tmp/'+opcode, 'w') as ofile:
        #         ofile.write('Opcode: '+opcode+' args - '+instruction[0]+', '+instruction[2]+','+instruction[3]+'\n\nInit:\n\n')
        #         ofile.write(inpinit)
        #         ofile.write('Main: \n\n')
        #         ofile.write(inpmain)
        #         ofile.flush()
        #         ofile.close()
            opcodes[opcode] = {}
            opcodes[opcode]['freq'] = 0
            opcodes[opcode]['contracts'] = 0
        opcodes[opcode]['freq'] += 1
        if opcode not in used:
            opcodes[opcode]['contracts'] += 1
            used.append(opcode)

    # Extract contract data
    if chash not in contracts:
        contracts[chash] = {}
        contracts[chash]['tx'] = ctx
        contracts[chash]['oplength'] = len(ifull)
        contracts[chash]['mainlength'] = len(imain)
        contracts[chash]['initlength'] = len(iinit)
        contracts[chash]['jumps'] = 0
        contracts[chash]['opcodes'] = {}
        copcodes = contracts[chash]['opcodes']
        # TODO: Number of jumps, number of opcodes
        for instruction in ifull:
            opcode = instruction[1]
            if opcode in jump_instructions:
                contracts[chash]['jumps'] += 1
            if opcode not in copcodes:
                copcodes[opcode] = {}
                copcodes[opcode]['freq'] = 0
            copcodes[opcode]['freq'] += 1

def load_contract_file(path):
    try:
        cfile = json.loads(open(path).read())
        # Iterate through contracts
        for contract in tqdm(cfile):
            cinit = cfile[contract][0]
            cmain = cfile[contract][1]
            ctx = cfile[contract][2]
            cmaindisasm = get_contract_disasm(cmain[2:])
            cinitdisasm = get_contract_disasm(cinit[2:])
            update_stats_from_disasm(contract, ctx, cinitdisasm, cmaindisasm)
    except:
        return

def load_contracts_dir(path):
    files = os.listdir(path)
    if path[-1] != '/': path += '/'
    print "Files loaded from path %s" % path
    for i in tqdm(xrange(0, len(files))):
        if(files[i].endswith('.json')):
            load_contract_file(path+files[i])
    if(write_out):
        save_json(contracts, 'contracts.json')
        save_json(opcodes, 'opcodes.json')
    save_json(callstack_error_contracts, 'callstack_stats.json')
    save_json(cterror_balances, 'cterror_balances.json')

def save_json(inp, filename):
    with open(filename, 'w') as outfile:
        json.dump(inp, outfile)


sample_path = "../contracts/contract_data"
load_contracts_dir(sample_path)