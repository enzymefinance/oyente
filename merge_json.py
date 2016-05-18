# merge all json files of the contracts into 40 files.
import json
import sys
SIZE = 500
from itertools import islice


def chunk(all_contracts):
    it = iter(all_contracts)
    for i in xrange(0, len(all_contracts), SIZE):
        yield {k: all_contracts[k] for k in islice(it, SIZE)}


def main():
    if (len(sys.argv) < 2):
        print "Usage: python check_concurrency.py <list of contract.json>"
        print "Example: python check_concurrency.py contract.json"
        return

    list_threads = []
    all_contracts = {}
    for i in range(1, len(sys.argv)):
        filename = sys.argv[i]
        with open(filename) as json_file:
            c = json.load(json_file)
            all_contracts.update(c)

    index = 1
    for item in chunk(all_contracts):
        with open("contract" + str(index) + '.json', 'w') as outfile:
            json.dump(item, outfile)
        index += 1

main()
