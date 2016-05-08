from tqdm import tqdm
import json
import re
import numpy as np

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

def gen_contract_hist():
    contracts = json.load(open('contracts.json'))
    oplengths = [contracts[contract]['oplength'] for contract in contracts]
    oplengths = sorted(oplengths, reverse=True)

    print "Max: %d, Min: %d, Mean: %d, Median: %d" % (max(oplengths), min(oplengths), np.mean(oplengths), np.median(oplengths))

    with open('contract_length.dat', 'w') as of:
        for oplength in oplengths:
            of.write('%d\n' % oplength)
        of.flush()
        of.close() 

def process_worth_str(istr):
    tag_pattern = r"<.+?>"
    outstr = re.sub(tag_pattern, "", istr).lower()
    # It's wei or ether
    # factor = 1
    # if(outstr.find('wei') > 0):
    #     factor = 1000000000000000000
    factor = 1000000000000000000
    if(outstr.find('wei') > 0):
        factor = 1
    outstr = re.sub("ether", "", outstr)
    outstr = re.sub("wei", "", outstr)
    outstr = re.sub(",", "", outstr)
    outval = float(outstr)
    return outval * factor

def gen_txnesting_hist(tfile):
    nesting = [(transaction['txid'],len(transaction['transactions'])) for transaction in tqdm(tfile)]
    nesting = sorted(nesting, key = lambda k: k[1], reverse=True)
    nestingvals = [element[1] for element in nesting]
    print "Writing..."
    with open('txnesting.csv', 'w') as of:
        for element in tqdm(nestingvals):
            of.write('%d\n' % element)
        of.flush()
        of.close()

    hist = np.histogram()

    # with open('txnesting.dat','w') as of:
    #     of.write('txid nesting\n')
    #     for element in nesting:
    #         of.write('%s %d\n' % (element[0], element[1]))
    #     of.flush()
    #     of.close()

def gen_txworth_hist(tfile):
    txworth = [(transaction['txid'], process_worth_str(transaction['transactions'][0]['worth'])) for transaction in tqdm(tfile)]
    txworth = sorted(txworth, key = lambda k : k[1], reverse=True)
    txvalues = [element[1] for element in txworth]
    print "Transaction value - min:%f, max:%f, mean:%f, median:%f" % (np.min(txvalues), np.max(txvalues), np.mean(txvalues), np.median(txvalues))
    with open('txvalueslog.csv', 'w') as of:
        i=0
        for element in txworth:
            if(element[1] > 0): 
                i+=1
                of.write('%f\n' % np.log(element[1]))
        of.flush()
        of.close()
    print "Wrote %d elements." % i
    # with open('txworth.dat', 'w') as of:
    #     of.write('txid worth\n')
    #     for element in txworth:
    #         of.write('%s %f\n' % (element[0], element[1]))
    #     of.flush()
    #     of.close()
    # with open('txworth_nozero_log.dat', 'w') as of:
    #     of.write('txid worth\n')
    #     for element in txworth:
    #         if element[1] > 0: of.write('%s %f\n' % (element[0], log(element[1])))
    #     of.flush()
    #     of.close()
    # with open('txworth_nozero.dat', 'w') as of:
    #     of.write('txid worth\n')
    #     for element in txworth:
    #         if element[1] > 0: of.write('%s %f\n' % (element[0], element[1]))
    #     of.flush()
    #     of.close()

def gen_contract_tx(tfile):
    # Build unique transaction count for contracts
    txcount = {}
    contract_balance = {}
    print "Collecting transaction count..."
    for transaction in tqdm(tfile):
        for tx in transaction['transactions']:
            if 'from' in tx:
                if tx['from'] not in txcount:
                    txcount[tx['from']] = 0
                txcount[tx['from']] += 1
            if 'to' in tx:
                if tx['to'] not in txcount:
                    txcount[tx['to']] = 0
                txcount[tx['to']] += 1
    cbalancefile = json.load(open('../contracts/contract_data/contract_balance.json'))
    cfile = json.load(open('contracts.json'))
    transactions = []
    print "Filtering..."
    for contract in tqdm(cfile):
        if contract in txcount:
            transactions.append(txcount[contract])
        else:
            transactions.append(0)
    # transactions = sorted(transactions, reverse=True)
    downscale_binsize = 100
    dstxs = []
    print "Downscaling..."
    for i in tqdm(xrange(0, len(transactions), downscale_binsize)):
        dstxs.append(np.mean(transactions[i:(i+downscale_binsize)]))
    transactions = dstxs
    print "Writing..."
    with open('ctxcount.csv', 'w') as of:
        for tcount in transactions:
            of.write('%f\n' % tcount)
        of.flush()
        of.close()
    print "loading balances.."
    balances = []
    for contract in tqdm(cfile):
        if contract in cbalancefile:
            balances.append(cbalancefile[contract])
        else:
            balances.append(0)
    # balances = sorted(balances, reverse=True)
    dsbalances = []
    print "Downscaling..."
    for i in tqdm(xrange(0, len(balances), downscale_binsize)):
        dsbalances.append(np.mean(balances[i:(i+downscale_binsize)]))
    balances = dsbalances

    with open('cbalance.csv', 'w') as of:
        for tbalance in balances:
            of.write('%f\n' % tbalance)
        of.flush()
        of.close()
    print "Done."


print "Loading transactions..."
tfile = json.loads(open('transactions.json').read())
print "Generating contract txcount and balances..."
gen_contract_tx(tfile)

# print "Generating Contract oplength..."
# gen_contract_hist()
# print "Generating Opcode histogram..."
# gen_opcode_hist()
# print "Generating Transaction Nesting Histogram..."
# gen_txnesting_hist(tfile)
# print "Generating Transaction worth histogram..."
# gen_txworth_hist(tfile)