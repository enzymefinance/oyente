import subprocess
import re
import os
import json
from tqdm import tqdm

def get_contract_code(cadd):
    sourcepattern = r"style='max-height: 250px; margin-top: 5px;'>([\s\S]+?)<\/pre>"
    namepattern = r"<td>Contract Name:[\n.]<\/td>[\n.]<td>[.\n]([\s\S]+?)[\n.]<\/td>"
    command = "wget -S -O - 'https://etherscan.io/address/%s#code'" % cadd
    DEVNULL = open(os.devnull, 'wb')
    wget = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=DEVNULL)
    outp = wget.stdout.read()
    return (re.findall(namepattern, outp), re.findall(sourcepattern, outp))

savedcontracts = []

def save_callstack_source(dirname):
    if not dirname.endswith('/'): dirname += '/'
    print("Loading callstack file...")
    cstkfile = json.load(open('callstack_stats.json'))
    cstbfile = json.load(open('cterror_balances.json'))
    for contract in tqdm(cstkfile):
        name, source = get_contract_code(contract)
        if(len(source) <= 0): continue
        source = source[0]
        fname = name[0] if len(name) > 0 else contract
        # print "Saved contract %s to %s.sol" % (contract, fname)
        if os.path.isfile(dirname+fname+'.sol'):
            i=0;
            while os.path.isfile(dirname+fname+str(i)+'.sol'):
                i+=1
            fname += str(i)
        fname += ".sol"
        savedcontracts.append((contract, fname, cstbfile[cstkfile.index(contract)]/1000000000000000000.0))
        with open(dirname + fname, 'w') as of:
            of.write('// '+contract+'\n// '+str(cstbfile[cstkfile.index(contract)]/1000000000000000000.0)+'\n')
            of.write(source)
            of.flush()
            of.close()

if __name__ == '__main__':
    save_callstack_source('source')
