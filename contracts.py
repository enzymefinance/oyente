import urllib
import urllib2
import requests
from subprocess import call, check_output
import json
url = 'http://localhost:8545/'
data_getCode = {'jsonrpc': '2.0',
			'method':'eth_getCode',
			'params':["0x9bA082240DBa3F9ef90038b9357649Fa569fd763", 'latest'],
			'id': 1}

data_TX_count = {'jsonrpc': '2.0',
			'method':'eth_getBlockTransactionCountByNumber',
			'params':[],
			'id': 2}

data_blockNumber = {'jsonrpc': '2.0',
			'method':'eth_blockNumber',
			'params':[],
			'id': 87}

data_get_TX_by_index = 	{'jsonrpc': '2.0',
			'method':'eth_getTransactionByBlockNumberAndIndex',
			'params':[],
			'id': 3}

data_get_TX_receipt = 	{'jsonrpc': '2.0',
			'method':'eth_getTransactionReceipt',
			'params':[],
			'id': 4}

def get_result(json_content):
	content = json.loads(json_content)
	try:
		return content["result"]
	except Exception as e:
		print e
		print json_content

list_address = []
list_contract = {}
r = requests.post(url, data=json.dumps(data_blockNumber), allow_redirects=True)
block_num = int(get_result(r.content), 16)
# block_num = 1097983
print block_num
for i in range(block_num):
	print 'processing block: ' + str(i)
	print "Number of contracts so far: " + str(len(list_contract.keys()))
	data_TX_count['params'] = [str(hex(i))]	
	r = requests.post(url, data=json.dumps(data_TX_count), allow_redirects=True)
	tx_count = int(get_result(r.content), 16)
	for tx_id in range(tx_count):
		data_get_TX_by_index['params'] = [str(hex(i)), str(hex(tx_id))]
		r = requests.post(url, data=json.dumps(data_get_TX_by_index), allow_redirects=True)
		tx = get_result(r.content)

		if (tx['to'] == None): #this TX creates a contract
			data_get_TX_receipt['params'] = [tx['hash']]
			r = requests.post(url, data=json.dumps(data_get_TX_receipt), allow_redirects=True)
			tx_receipt = get_result(r.content)
			if tx_receipt['contractAddress'] == None:
				continue

			data_getCode['params'][0] = tx_receipt['contractAddress']
			r = requests.post(url, data=json.dumps(data_getCode), allow_redirects=True)
			code = get_result(r.content)
			if len(code) > 2:
				list_contract[tx_receipt['contractAddress']] = [code, tx['hash']]

with open('contract.json', 'w') as outfile:
    json.dump(list_contract, outfile)
    

# print str(values)
# # print url + " -X POST --data" + str(values)
# print check_output(['curl', url, "-X",  "POST", "--data", str(values)])