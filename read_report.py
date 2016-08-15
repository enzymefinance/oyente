from stats_builder import get_source
from tqdm import tqdm
import sys
import glob
import json

print "Loading json files..."
contract_json = {}
for filen in tqdm(glob.glob('contracts/contract_data/contract*.json')):
    j = json.loads(open(filen).read())
    contract_json.update(j)

code = []

reentrancy_json = []

def get_source_for_report(rname, prefix):
    global code
    lines = open(rname).read().split('\n')
    for line in tqdm(lines):
        if len(line) > 0:
            # # Save into JSON
            # reentrancy_json.append(line[:42])

            # # Find unique number
            # if line[:42] not in contract_json:
            #     print "Contract "+line[:42]+" not found in the json."
            #     continue
            # if contract_json[line[:42]][0] not in code:
            #     code.append(contract_json[line[:42]][0])

            # Get and save source code
            name, source = get_source.get_contract_code(line[:42])
            if len(source) == 0: continue
            sfile = None
            if len(name) != 0:
                sfile = open('re_source/'+prefix+name[0],'w')
            else:
                sfile = open('re_source/'+prefix+line[:42])
            sfile.write(source[0])
            sfile.flush()
            sfile.close()
    # with open('stats_builder/re_stats.json', 'w') as refile:
    #     refile.write(json.dumps(reentrancy_json, indent = 1))


get_source_for_report('re_report.report', 'filtered/')
# get_source_for_report('re_report_non_filtered.report', 'unfiltered/')