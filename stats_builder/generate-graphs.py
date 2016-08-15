from tqdm import tqdm
import json
import re
import numpy as np
import os
import glob
# from fuzzywuzzy import fuzz, process

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
    weiconst = 1000000000000000000
    for contract in tqdm(cfile):
        if contract in cbalancefile:
            balances.append(cbalancefile[contract]/weiconst)
        else:
            balances.append(0)

    print "Min Balance: %d, Max Balance: %d, Sum: %f, Mean Balance: %f, Median Balance: %f" % (np.min(balances), np.max(balances), np.sum(balances), np.mean(balances), np.median(balances))
    balances = sorted(balances, reverse=True)
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

def load_report(filen, contract_name, contract_sats, failed):
    try:
        with open(filen) as f:
            explored_paths = int(f.readline())
            pathno = int(re.findall(r"number of path: ([\d]+)", f.readline())[0])
            f.readline()
            f.readline()
            concurrency_pairs = int(f.readline())
            f.readline()
            timestamp_dependent = False
            td = f.readline()
            if td[0:2] == "no": 
                timestamp_dependent = False
            elif td[0:3] == "yes":
                timestamp_dependent = True
            else:
                failed.append(filen)
                return
            exec_time = 0
            try:        
                exec_time = float(f.readline())
            except:
                failed.append(filen)
                return
            contract_sats.append((contract_name, explored_paths, pathno, concurrency_pairs, timestamp_dependent, exec_time))
    except ValueError:
        return
        print "ValueError in file %s. contents - " % filen
        with open(filen) as f:
            print f.read()

def load_sat_stats():
    dirname = "stats"
    files = os.listdir(dirname)
    pattern = r"(0x[a-f\d]+)\."
    contract_sats = []
    failed = []
    for filen in tqdm(files):
        if filen.endswith(".report"):
            contract_name = re.findall(pattern,filen)[0]
            load_report(dirname + "/" + filen, contract_name, contract_sats, failed)
    print "Loading contract db..."
    contracts = json.loads(open('contracts.json').read())
    stats = []
    for entry in contract_sats:
        if entry[0] in contracts:
            stats.append((entry[1], entry[5]))
    stats = sorted(stats, key = lambda k : k[0])
    print "Writing..."
    with open('running-time.csv', 'w') as rtcsv:
        rtcsv.write("contract,paths,time\n")
        for i in tqdm(xrange(0, len(stats))):
            rtcsv.write("%d,%d,%f\n" % (i, stats[i][0], stats[i][1]))
    print "Done."
    with open('sat_stats.json','w') as of:
        of.write(json.dumps(contract_sats, indent=1))
    transaction_race = 0
    timestamp = 0
    paths = []
    for entry in contract_sats: 
        paths.append(entry[1])
        if entry[3] > 0: transaction_race+=1
        if entry[4] == True: timestamp += 1 
    print "Average number of paths: %d" % np.mean(paths)
    print "Transaction Race: %d" % transaction_race
    print "TimeStamp Dependence: %d" % timestamp
    print "Average time: %f" % np.mean([entry[5] for entry in contract_sats])

# load_sat_stats()

def check_unique():
    # Load all contracts
    cpath = "../contracts/contract_data"
    cfiles = os.listdir(cpath)
    contracts = {}
    cmains = {}

    for cfile in tqdm(cfiles):
        if not cfile.endswith('.json'): continue
        if cfile == "contract_balance.json": continue
        cjson = json.loads(open(cpath+'/'+cfile).read())
        contracts.update(cjson)
        for contract in cjson:
            cmains[contract] = cjson[contract][1]

    print "Loaded %d contracts." % len(cmains)
    print "Removing duplicates..."

    original_cmains = {}

    for element in tqdm(cmains):
        found = False
        for o in original_cmains:
            if cmains[element] == original_cmains[o]: 
                found = True
                break
        if not found:
            original_cmains[element] = cmains[element]

    print "%d original contracts." % len(original_cmains)

    with open('unique_contracts.json', 'w') as of:
        of.write(json.dumps(original_cmains, indent=1))
        of.flush()
        of.close()

    print "merging..."

    duplicates = []

    for contract in tqdm(cmains):
        found = False
        for l in duplicates:
            if cmains[l[0]] == cmains[contract]:
                l.append(contract)
                found = True
                break
        if not found:
            duplicates.append([contract])

    print "%d elements in merge list." % len(duplicates)

    with open('duplicate_contracts.json', 'w') as of:
        of.write(json.dumps(duplicates, indent=1))
        of.flush()
        of.close()    

# check_unique()

def get_all():
    sats = json.loads(open('sat_stats.json').read())
    cstack = json.loads(open('callstack_stats.json').read())
    reentrancy = json.loads(open('re_stats.json').read())

    all_problematic = []

    for c in cstack:
        all_problematic.append(c)

    for c in reentrancy:
        all_problematic.append(c)

    # all_problematic = cstack
    t_race = []
    ts_depend = []
    for entry in sats:
        if entry[0] in all_problematic: continue
        if entry[3] > 0: 
            t_race.append(entry[0])
            all_problematic.append(entry[0])
        if entry[4] == True: 
            ts_depend.append(entry[0])
            if entry[0] not in all_problematic: all_problematic.append(entry[0])

    print "%d transaction race, %d timestamp, %d in cstack, %d in reentrancy." % (len(t_race), len(ts_depend), len(cstack), len(reentrancy))

    print "%d problematic contracts" % len(all_problematic)
    print "Loading contract bytecode..."
    # cpath = "../contracts/contract_data"
    # cfiles = os.listdir(cpath)

    cmains = {}

    cfiles = glob.glob('../contracts/contract_data/contract*.json')

    for cfile in tqdm(cfiles):
        # if not cfile.endswith('.json'): continue
        # if cfile == "contract_balance.json": continue
        cjson = json.loads(open(cfile).read())
        for contract in all_problematic:
            if contract in cmains: continue
            if contract in cjson:
                cmains[contract] = cjson[contract][1]

    # Remove duplicates
    cmains_sorted = {}
    # for c in cmains:
    #     cmains_sorted.append((c, cmains[c]))

    # cmains_sorted = sorted(cmains_sorted, lamda k: k[1])

    threshold = 99

    print "Removing duplicates..."

    duplicates = 0

    new_t_race = []
    new_ts_depend = []
    new_cstack = []
    new_reentrancy = []

    print "Transaction Race..."
    for c in tqdm(t_race):
        found = False
        for cont in new_t_race:
            if cmains[cont] == cmains[c]:
                found = True
                break
        if not found:
            new_t_race.append(c)

    print "Timestamp..."
    for c in tqdm(ts_depend):
        found = False
        for cont in new_ts_depend:
            if cmains[cont] == cmains[c]:
                found = True
                break
        if not found:
            new_ts_depend.append(c)

    print "Callstack..."
    for c in tqdm(cstack):
        found = False
        for cont in new_cstack:
            if cmains[cont] == cmains[c]:
                found = True
                break
        if not found:
            new_cstack.append(c)

    print "Reentrancy..."
    for c in tqdm(reentrancy):
        found = False
        for cont in new_reentrancy:
            if cmains[cont] == cmains[c]:
                found = True
                break
        if not found:
            new_reentrancy.append(c)

    print "All..."
    for contract in tqdm(cmains):
        found = False
        for c in cmains_sorted:
            # if fuzz.ratio(cmains_sorted[c], cmains[contract]) >= threshold:
            if cmains[contract] == cmains_sorted[c]:
                found = True
                break
        if not found:
            cmains_sorted[contract] = cmains[contract]
        else:
            duplicates += 1
            # print "duplicate count: %d, original len: %d" % (duplicates, len(cmains_sorted))

    print "Original Contracts: %d" % len(cmains_sorted)

    print "Original Counts - "
    print "CallStack - %d, Transaction Race - %d, Timestamp Dependence - %d, Reentrancy - %d" % (len(new_cstack), len(new_t_race), len(new_ts_depend), len(new_reentrancy))

    # return cmains_sorted

# cmains = get_all()

def get_source_timestamp():
    sats = json.loads(open('sat_stats.json').read())
    source_list = []

    for entry in sats:
        if entry[4] == True:
            source_list.append(entry[0])

    from get_source import get_contract_code

    for c in tqdm(source_list):
        code = get_contract_code(c)

        if len(code[1]) > 0:
            with open('timestamp_source/'+c+'.sol', 'w') as of:
                of.write(code[1][0])
                of.flush()
                of.close()

def get_tsdepend_timestamp():
    sats = json.loads(open('sat_stats.json').read())
    source_list = []

    for entry in sats:
        if entry[3] > 0:
            source_list.append(entry[0])

    from get_source import get_contract_code

    for c in tqdm(source_list):
        code = get_contract_code(c)

        if len(code[1]) > 0:
            with open('tod_source/'+c+'.sol', 'w') as of:
                of.write(code[1][0])
                of.flush()
                of.close()

def get_source_stats():
    contracts = []

    cpath = "../contracts/contract_data"
    cfiles = os.listdir(cpath)

    print "Loading contracts..."

    for cfile in tqdm(cfiles):
        if not cfile.endswith('.json'): continue
        if cfile == "contract_balance.json": continue
        cjson = json.loads(open(cpath+'/'+cfile).read())
        for contract in cjson: contracts.append(contract)

    print "Checking for source..."

    from get_source import get_contract_code

    with_source = 0

    for contract in tqdm(contracts):
        if(len(get_contract_code(contract)[1]) > 0): with_source+=1

    print "%d contracts have source out of %d." % (with_source, len(contracts))

# get_source_stats()


# get_tsdepend_timestamp()

# print "Loading transactions..."
# tfile = json.loads(open('transactions.json').read())
# print "Generating contract txcount and balances..."
# gen_contract_tx(tfile)

# print "Generating Contract oplength..."
# gen_contract_hist()
# print "Generating Opcode histogram..."
# gen_opcode_hist()
# print "Generating Transaction Nesting Histogram..."
# gen_txnesting_hist(tfile)
# print "Generating Transaction worth histogram..."
# gen_txworth_hist(tfile)