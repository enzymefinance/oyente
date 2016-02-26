import json

#Pretty Printing Tools
def prRed(prt): print("\033[91m {}\033[00m" .format(prt))
def prGreen(prt): print("\033[92m {}\033[00m" .format(prt))
def prYellow(prt): print("\033[93m {}\033[00m" .format(prt))
def prLightPurple(prt): print("\033[94m {}\033[00m" .format(prt))
def prPurple(prt): print("\033[95m {}\033[00m" .format(prt))
def prCyan(prt): print("\033[96m {}\033[00m" .format(prt))
def prLightGray(prt): print("\033[97m {}\033[00m" .format(prt))
def prBlack(prt): print("\033[98m {}\033[00m" .format(prt))

finalout = " "

tablevel = 0

def tabprint(instr):
	global tablevel
	tstr = ""
	for i in xrange(0, tablevel):
		tstr = tstr + "  |"
	prGreen("%s%s" % (tstr, instr))

def tabprintpurple(instr):
	global tablevel
	tstr = ""
	for i in xrange(0, tablevel):
		tstr = tstr + "  |"
	prPurple("%s%s" % (tstr, instr))

def explore(jsonobject):
	global tablevel
	tablevel+=1
	global finalout

	if ('name' in jsonobject) and ('attributes' in jsonobject):
		if 'name' in jsonobject['attributes']:
			for i in xrange(0, tablevel):
				finalout += "  "
			finalout += jsonobject['name'] + " "
			finalout += (jsonobject['attributes']['name'])
			finalout += "\n"

	if 'name' in jsonobject:
		tabprintpurple("Type: %s" % (jsonobject['name']))
	if 'attributes' in jsonobject:
		tabprint("Attributes -  ")
		for k, v in jsonobject['attributes'].iteritems():
			tabprint("%s: %s" % (k,v))
	if 'children' in jsonobject:
		for child in jsonobject['children']:
			explore(child)
	tablevel-=1


with open('foo.astjson') as jsonfile:
	rootjson = json.load(jsonfile)

explore(rootjson['children'][0])

print "Final:"
print finalout