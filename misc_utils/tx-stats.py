import re
import os
from tqdm import tqdm
import json

def get_transactions(fname):
    pattern  = r"(>(0x[\da-f]+)<|block\/(\d+)|<td>(\d.+?)</td>)"
    res = re.findall(pattern, open(fname).read(), re.IGNORECASE)
    txs = []
    curtx = {}

    for match in res:
        if(match[2] != ''):
            if(len(txs) > 0):
                txs[-1]['transactions'] = txs[-1]['transactions'][:-1]
            curtx = {}
            curtx['transactions'] = []
            curtx['transactions'].append({})
            txs.append(curtx)    	
        if(match[1] != ''):
        	if 'txid' not in curtx:
        		curtx['txid'] = match[1]
        	else:
        		if 'from' not in curtx['transactions'][-1]:
        			curtx['transactions'][-1]['from'] = match[1]
        		elif 'to' not in curtx['transactions'][-1]:
        			curtx['transactions'][-1]['to']   = match[1]
        if(match[3] != ''):
        	curtx['transactions'][-1]['worth'] = match[3]
        	curtx['transactions'].append({})
    return txs

def load_txdir(path):
	files = os.listdir(path)
	if path[-1] != '/': path += '/'
	txs = []
	for f in tqdm(files):
		if f.endswith('.html'):
			txs += get_transactions(path+f)
	return txs

def pprint(fn):
	inj = json.loads(open(fn).read())
	outj = open(fn, 'w')
	outj.write(json.dumps(inj, indent=1))
	outj.flush()
	outj.close()

txs_dir = "../transaction-scraper/transactions"
print("Loading transactions...")
txs = load_txdir(txs_dir)
print("Saving...")
with open('transactions.json','w') as tfile:
	tfile.write(json.dumps(txs, indent=1))
	tfile.close()
print("Done.")
