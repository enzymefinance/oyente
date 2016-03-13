import os, sys
import json
import subprocess

log_file = "log.csv"

def load_json(filename):
    temp_file = "tmp_"

    processes = set()

    with open(filename) as json_file:
        c = json.load(json_file)

        #Find and write the source code to disk for disassembly
        for contract, data in c.iteritems(): 
            with open(temp_file+contract+".code", 'w') as tfile:
                tfile.write(data[0][2:])
                tfile.write("\n")
                tfile.close()
            print "Running disassembly on contract %s..." % (contract)
            # print "Command: " + ("cat %s.code | disasm > %s.evm" % (temp_file+contract, temp_file+contract))
            os.system("cat %s.code | disasm > %s.evm" % (temp_file+contract, temp_file+contract))
            missed_jumps = 0
            jumps = 0
            instructions = -2
            with open(temp_file+contract+".evm", 'r') as disasm:
                prev_line = []
                for line in disasm:
                    instructions+=1
                    if ("JUMP" in line or "JUMPI" in line) and "JUMPDEST" not in line:
                        jumps+=1
                        if "PUSH" not in prev_line: missed_jumps+=1
                    prev_line = line
                disasm.close()
            with open(log_file, 'a') as lf:
                lf.write("%s, %d, %d, %d, %f, %f\n" %(contract, instructions, jumps, missed_jumps, 0 if instructions == 0 else missed_jumps/float(instructions), 0 if jumps == 0 else missed_jumps/float(jumps)))
                lf.close()
            os.system("rm -rf %s*" % (temp_file))




def main():
    if(len(sys.argv) < 2):
        print "Usage: python autobench.py <contract.json>"
        print "Example: python autobench.py contract.json"
        return

    with open(log_file, "w") as lf:
        lf.write("Contract ID, Instructions, Jumps, Unprocessed Jumps, UJ/I, UJ/J\n")
        lf.close()

    for i in xrange(1, len(sys.argv)):
        load_json(sys.argv[i])


if __name__ == '__main__':
    main()