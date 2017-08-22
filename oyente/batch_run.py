import json
import glob
from tqdm import tqdm
import os
import sys
import urllib2

contract_dir = 'contract_data'

cfiles = glob.glob(contract_dir+'/contract1.json')

cjson = {}

print "Loading contracts..."

for cfile in tqdm(cfiles):
	cjson.update(json.loads(open(cfile).read()))

results = {}
missed = []

print "Running analysis..."

contracts = cjson.keys()

if os.path.isfile('results.json'):
	old_res = json.loads(open('results.json').read())
	old_res = old_res.keys()
	contracts = [c for c in contracts if c not in old_res]

cores=0
job=0

if len(sys.argv)>=3:
	cores = int(sys.argv[1])
	job = int(sys.argv[2])
	contracts = contracts[(len(contracts)/cores)*job:(len(contracts)/cores)*(job+1)]
	print "Job %d: Running on %d contracts..." % (job, len(contracts))

for c in tqdm(contracts):
	with open('tmp.evm','w') as of:
		of.write(cjson[c][1][2:])
	os.system('python oyente/oyente.py -ll 30 -s tmp.evm -j -b')
	try:
		results[c] = json.loads(open('tmp.evm.json').read())
	except:
		missed.append(c)
	with open('results.json', 'w') as of:
		of.write(json.dumps(results,indent=1))
	with open('missed.json', 'w') as of:
		of.write(json.dumps(missed,indent=1))
	# urllib2.urlopen('https://dweet.io/dweet/for/oyente-%d-%d?completed=%d&missed=%d&remaining=%d' % (job,cores,len(results),len(missed),len(contracts)-len(results)-len(missed)))

print "Completed."
