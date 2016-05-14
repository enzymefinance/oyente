import os
import re
import json
from datetime import date
# import dateutil.parser as dparser
from datetime import datetime
import csv

def extract_date(timestamp):
    if timestamp == None:
        return None
    #timestamp should be in this form (8/24/2015 12:32:21 PM)
    timestamp = re.sub('[()]', '', timestamp).split()[0]
    timestamp = timestamp.split('/')
    return date(int(timestamp[2]), int(timestamp[1]), int(timestamp[0]))


def get_block_time(block_no):
    print "Getting info for block... " + str(block_no)
    file_name = "tmp/" + str(block_no) + ".html"
    try:
        try:
            with open(file_name, 'r') as myfile:
                data = myfile.read().replace('\n', '')
        except Exception as e:
            os.system("wget -O %s http://etherscan.io/block/%s" % (file_name, block_no))
            with open(file_name, 'r') as myfile:
                data = myfile.read().replace('\n', '')
        match = re.search(r'\d+/\d+/\d{4}', data)
        return datetime.strptime(match.group(), '%m/%d/%Y').date()
    except Exception as e:
        print e
        return None


contracts = []
number = 0
for i in range(5, 146):
    filename = "contract_" + str(i*10000) + ".json"
    with open(filename) as json_file:
        c = json.load(json_file)
        number += len(c)
        contract_date = None
        while not contract_date:
            contract_date = get_block_time(i*10000)
            print contract_date
        contracts.append({'number': number, 'date': contract_date})

with open("stats.csv", "w") as stats_file:
    fp = csv.writer(stats_file, delimiter=',')
    fp.writerow(["date", "contracts"])
    counter = 0
    for item in contracts:
        counter += 1
        if counter%10 == 0:
            fp.writerow([item['date'].strftime('%Y-%m-%d'), item['number']])
    item = contracts[len(contracts)-1]
    fp.writerow([item['date'].strftime('%Y-%m-%d'), item['number']])
print contracts

