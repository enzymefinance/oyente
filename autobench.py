import os, sys
import json
import subprocess
import operator

log_file = "log.csv"
jp_file = "jump_prev.csv"
if_file = "instruction_frequency.csv"
chain_file = "chains.csv"

def load_json(filename, jump_prev, instruction_freq, all_chains):
    temp_file = "tmp_"

    with open(filename) as json_file:
        c = json.load(json_file)

        #Find and write the source code to disk for disassembly
        for contract, data in c.iteritems(): 
            with open(temp_file+contract+".code", 'w') as tfile:
                tfile.write(data[0][2:])
                tfile.write("\n")
                tfile.close()
            sys.stdout.write("\tRunning disassembly on contract %s...\t\r" % (contract))
            sys.stdout.flush()
            # print "Command: " + ("cat %s.code | disasm > %s.evm" % (temp_file+contract, temp_file+contract))
            os.system("cat %s.code | disasm > %s.evm" % (temp_file+contract, temp_file+contract))
            missed_jumps = 0
            jumps = 0
            instructions = -2
            with open(temp_file+contract+".evm", 'r') as disasm:
                last_jump = 1
                instruction_list = [line.strip() for line in disasm]
                prev_line = []
                total_distance = 0
                for i in xrange(1, len(instruction_list)):
                    line = instruction_list[i]
                    if(len(line.split()) > 1):
                        instruction = line.split()[1]
                        if instruction not in instruction_freq:
                            instruction_freq[instruction] = 0
                        instruction_freq[instruction] += 1
                    instructions+=1
                    if "CALLCODE" in line:
                        print line
                    if ("JUMP" in line or "JUMPI" in line) and "JUMPDEST" not in line:
                        jumps+=1
                        distance = 0
                        chain = []
                        for p in range(i-1, last_jump, -1):
                            if(len(instruction_list[p].split()) < 1):
                                missed_jumps+=1
                                break
                            if "PUSH" not in instruction_list[p]:
                                chain.append(instruction_list[p].split()[1])
                                distance += 1
                                cur_instr = instruction_list[p].split()[1]
                                if cur_instr not in jump_prev:
                                    jump_prev[cur_instr] = 0
                                jump_prev[cur_instr] += 1
                                if p == last_jump-1:
                                    missed_jumps+=1    
                            else: 
                                break
                        if(len(chain) > 0):
                            all_chains.append(chain)
                        last_jump = i
                        total_distance += 1
                    prev_line = line
                disasm.close()
            with open(log_file, 'a') as lf:
                lf.write("%s, %d, %d, %d, %f, %f, %d\n" %(contract, instructions, jumps, missed_jumps, 0 if instructions == 0 else missed_jumps/float(instructions), 0 if jumps == 0 else missed_jumps/float(jumps), total_distance))
                lf.close()
            os.system("rm -rf %s*" % (temp_file))
    return jump_prev, instruction_freq, all_chains

def chain_score(jp, chain):
    return sum([jp[instr] for instr in chain])

def merge_chains(all_chains):
    new_chains = [" ".join(x) for x in all_chains]
    freq_dict =  {x:new_chains.count(x) for x in set(new_chains)}
    return [{'path':k, 'freq':v} for k, v in freq_dict.iteritems()]

def compare_jp(jp):
    def compare_chain(a, b):
        for i in xrange(0, min(len(a), len(b))):
            if a[i] == b[i] or jp[a[i]] == jp[b[i]]: 
                continue
            else:
                jp[a[i]] - jp[b[i]]
        return 0
    return compare_chain

def main():
    if(len(sys.argv) < 2):
        print "Usage: python autobench.py <contract.json>"
        print "Example: python autobench.py contract.json"
        return

    with open(log_file, "w") as lf:
        lf.write("Contract ID, Instructions, Jumps, Unprocessed Jumps, UJ/I, UJ/J, Total Distance\n")
        lf.close()

    jump_prev = {}
    instruction_freq = {}
    all_chains = []
    instruction_freq_contract = {}

    for i in xrange(1, len(sys.argv)):
        jump_prev, instruction_freq, all_chains = load_json(sys.argv[i], jump_prev, instruction_freq, all_chains)

    sorted(all_chains, cmp=compare_jp(jump_prev))

    with open(if_file, "w") as ifile:
        ifile.write("Instruction, Frequency\n")
        keys = sorted(instruction_freq, key=instruction_freq.get, reverse=True)
        for i in keys:
            f = instruction_freq[i]
            ifile.write("%s, %d\n" % (i,f))
        ifile.close()

    with open(jp_file, "w") as jpfile:
        jpfile.write("Instruction, Frequency\n")
        keys = sorted(jump_prev, key=jump_prev.get, reverse=True)
        for i in keys:
            f = jump_prev[i]
            jpfile.write("%s, %d\n" % (i,f)) 
        jpfile.close()

    merged_chains = merge_chains(all_chains)
    # sorted(merged_chains, key=operator.itemgetter('freq'))

    with open(chain_file, "w") as cfile:
        cfile.write("Frequency, Chain\n")
        for c in sorted(merged_chains, key=operator.itemgetter('freq'), reverse=True):
            cfile.write("%d, %s\n" % (c['freq'], c['path']))
        cfile.close()


if __name__ == '__main__':
    main()