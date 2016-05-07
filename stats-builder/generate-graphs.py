from tqdm import tqdm
import json
import re

def gen_opcode_hist():
    # load opcodes
    opcodes = json.load(open('opcodes.json'))

    opc_contracts = [(opcode, opcodes[opcode]['contracts']) for opcode in opcodes]
    opc_contracts = sorted(opc_contracts, key = lambda k: k[1], reverse=True)

    opcodes = [(opcode, opcodes[opcode]['freq']) for opcode in opcodes]
    opcodes = sorted(opcodes, key = lambda k: k[1], reverse=True)

    print "length: %d" % len(opcodes)

    with open('opcodehist.dat', 'w') as of:
        of.write('opcode frequency\n')
        for i in xrange(0,25):
            of.write('%s %d\n' % (opcodes[i][0], opcodes[i][1]))
        of.flush()
        of.close()

    with open('opcodecont.dat', 'w') as of:
        of.write('opcode contracts\n')
        for i in xrange(0,25):
            of.write('%s %d\n' % (opc_contracts[i][0], opc_contracts[i][1]))
        of.flush()
        of.close()        

def gen_txnesting_hist(tfile):
    nesting = [(transaction['txid'],len(transaction['transactions'])) for transaction in tqdm(tfile)]
    nesting = sorted(nesting, key = lambda k: k[1], reverse=True)
    with open('txnesting.dat','w') as of:
        of.write('txid nesting\n')
        for element in nesting:
            of.write('%s %d\n' % (element[0], element[1]))
        of.flush()
        of.close()

def process_worth_str(istr):
    tag_pattern = r"<.+?>"
    outstr = re.sub(tag_pattern, "", istr).lower()
    # It's wei or ether
    factor = 1
    if(outstr.find('wei') > 0):
        factor = 1000000000000000000
    outstr = re.sub("ether", "", outstr)
    outstr = re.sub("wei", "", outstr)
    outstr = re.sub(",", "", outstr)
    outval = float(outstr)
    return outval * factor

def gen_txworth_hist(tfile):
    txworth = [(transaction['txid'], process_worth_str(transaction['worth'])) for transaction in tqdm(tfile)]
    txworth = sorted(txworth, key = lambda k : k[1], reverse=True)
    with open('txworth.dat', 'w') as of:
        of.write('txid worth\n')
        for element in nesting:
            of.write('%s %f\n' % (element[0], element[1]))
        of.flush()
        of.close()

tfile = json.loads(open('transactions.json').read())

gen_opcode_hist()
gen_txnesting_hist(tfile)
gen_txworth_hist(tfile)