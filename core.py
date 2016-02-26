#BASH Code - cat testfile | ./disasm) >> testfiledisasm

import sys, tokenize
from tokenize import NUMBER, STRING, NAME, OP, NEWLINE
from neo4jrestclient.client import GraphDatabase
 
db = GraphDatabase("http://localhost:7474", username="neo4j", password="1.66Planck")

def loadfile():
	labels = db.labels.create("JumpDests")
	labdict = {}
	calldict = {}
	jumptype = {}
	with open(sys.argv[1], 'r') as opfile:
		opfile.readline() #Remove first line
		tokens = tokenize.generate_tokens(opfile.readline)
		last_line = 0
		wait_for_push = False
		last_push = 0
		labdict[0] = db.nodes.create(name="main")
		labels.add(labdict[0])
		curblock = 0
		for tok_type, tok_string, (srow, scol), _, lineno in tokens:
			if wait_for_push == True:
				pval = ""
				for ptok_type, ptok_string, _, _, _ in tokens:
					if ptok_type == NEWLINE:
						break
					try:
						int(ptok_string, 16)
						pval += ptok_string
					except ValueError:
						pass					
				last_push = int(pval, 16)
				wait_for_push = False
			if tok_type == NUMBER:
				try:
					last_line = int(tok_string)
				except ValueError:
					last_line = int(tok_string, 16)
			elif tok_type == NAME:
				if tok_string == "JUMPDEST":
					print "Jump Destination Found: 0x%04x or %d" % (last_line, last_line)
					labdict[last_line] = db.nodes.create(name=("0x%04x" % (last_line)))
					labels.add(labdict[last_line])
					labdict[curblock].relationships.create("falls to", labdict[last_line])
					print "Block %d now falls to %d" % (curblock, last_line)
					curblock = last_line
				elif tok_string == "PUSH2":
					wait_for_push = True
				elif tok_string == "JUMP" or tok_string == "JUMPI":
					print "Jump detected to %04x or %d on line %d" % (last_push, last_push, srow+1)
					calldict[curblock] = last_push
					jumptype[curblock] = "JUMP" if tok_string == "JUMP" else "COND"

	for caller in calldict:
		try:
			if jumptype[caller] == "JUMP":
				labdict[caller].relationships.create("calls", labdict[calldict[caller]])
			else:
				labdict[caller].relationships.create("conditionals", labdict[calldict[caller]])
		except KeyError:
			print "The Call %d, %04x - %d, %04x did not work out" % (caller, caller, calldict[caller], calldict[caller])
			for i in xrange(calldict[caller],0,-1):
				if i in labdict:
					print "We made do with the block %d, %04x" % (i, i)
					labdict[caller].relationships.create("calls", labdict[i])
					break

					


def main():
	if len(sys.argv) == 1:
		print "Usage: python core.py <opcodefile>"
		return

	loadfile()



if __name__ == '__main__':
	main()