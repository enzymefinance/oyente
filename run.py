import shlex
import subprocess
import os
import re
import sys

def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

def main():
	fail_str = "Usage: python run.py <solidity file> <contract name>"

	if not cmd_exists("disasm"):
		print "disasm is missing. Please install go-ethereum and make sure disasm is in the path."
		return

	if not cmd_exists("solc"):
		print "solc is missing. Please install the solidity compiler and make sure solc is in the path."
		return

	if(len(sys.argv) < 3):
		print fail_str
		return

	# Compile first

	solc_cmd = "solc --optimize --bin-runtime %s"

	FNULL = open(os.devnull, 'w')

	solc_p = subprocess.Popen(shlex.split(solc_cmd % sys.argv[1]), stdout = subprocess.PIPE, stderr=FNULL)
	solc_out = solc_p.communicate()

	bin_str = ""
	try:
		bin_str = re.search(r"part: \n(.*?)\n", solc_out[0]).groups()[0]
	except:
		print("Compilation failed. Please fix any errors in the source code and ensure that compiling with your global solc produces a valid binary.")
		return

	bin_str += "\0"

	disasm_out = ""
	try:
		disasm_p = subprocess.Popen(shlex.split('disasm'), stdout=subprocess.PIPE, stdin=subprocess.PIPE)
		disasm_out = disasm_p.communicate(input=bin_str)[0]

	except:
		print "Disassembly failed."

	# Run symExec

	with open(sys.argv[1]+'.evm', 'w') as of:
		of.write(disasm_out)

	os.system('python symExec.py %s.evm' % (sys.argv[1]))

	os.system('rm %s.evm' % (sys.argv[1]))


if __name__ == '__main__':
	main()