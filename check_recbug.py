import os, sys, re
import json
import subprocess
import operator
import glob

filter_rexp = r"GAS[^\n]*?\n[^\n]+?\n[\d\s]*?CALL\s"

counter = 0

def load_json(filename):
    global counter
    temp_file = "tmp_"

    with open(filename) as json_file:
        c = json.load(json_file)

        #Find and write the source code to disk for disassembly
        for contract, data in c.iteritems(): 
            with open(temp_file+contract+".code", 'w') as tfile:
                tfile.write(data[0][2:])
                tfile.write("\n")
                tfile.close()
            # print("\tRunning disassembly on contract %s..." % (contract))
            sys.stdout.write("\tRunning disassembly on contract %s...\t\r" % (contract))
            sys.stdout.flush()
            # print "Command: " + ("cat %s.code | disasm > %s.evm" % (temp_file+contract, temp_file+contract))
            os.system("cat %s.code | disasm > %s.evm" % (temp_file+contract, temp_file+contract))
            # with open(temp_file+contract+".evm", 'r') as disasm:

            disasm_str = open(temp_file+contract+".evm").read()
            if re.search(filter_rexp, disasm_str):
                # print "Possible Recursive bug. Investigating..."
                os.system('python symExec.py '+temp_file+contract+'.evm')

    os.system('rm tmp_*')

with open('re_report.report', 'w') as f: f.write('') 

for filen in glob.glob('contracts/contract_data/*.json'):
    load_json(filen)

# os.system('rm tmp_*.code && rm tmp_*.evm')

print "Found %d contracts with possible recursive splitting bugs." % counter
