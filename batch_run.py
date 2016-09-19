import json
import glob
from tqdm import tqdm
import os

contract_dir = 'contract_data' 

cfiles = glob.glob(contract_dir+'/contract*.json')

cjson = {}

print "Loading contracts..."

for cfile in tqdm(cfiles):
	cjson.update(json.loads(open(cfile).read()))

results = {}
missed = []

print "Running analysis..."

contracts = cjson.keys()

if len(sys.argv)>3:
	cores = int(sys.argv[1])
	job = int(sys.argv[2])
	contracts = contracts[(len(contracts)/cores)*job:(len(contracts)/cores)*(job+1)]
	print "Job %d: Running on %d contracts..." % (job, len(contracts))

for c in tqdm(contracts):
	with open('tmp.evm','w') as of:
		# print "Out: "+cjson[c][1][2:]
		of.write(cjson[c][1][2:]+"\0")
	os.system('python oyente.py tmp.evm -j -b')
	try:
		results[c] = json.loads(open('tmp.evm.json').read())
	except:
		missed.append(c)
	with open('results.json', 'w') as of:
		of.write(json.dumps(results,indent=1))
	with open('missed.json', 'w') as of:
		of.write(json.dumps(missed,indent=1))

print "Completed."
