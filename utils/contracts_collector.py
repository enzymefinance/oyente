import urllib
import urllib2
import requests
import threading
import json

url = 'http://localhost:8545/'


def get_result(json_content):
    content = json.loads(json_content)
    try:
        return content["result"]
    except Exception as e:
        print e
        print json_content


class MyThread(threading.Thread):
    def __init__(self, index):
        threading.Thread.__init__(self)
        self.data_getCode = {'jsonrpc': '2.0',
                        'method': 'eth_getCode',
                        'params': ["0x9bA082240DBa3F9ef90038b9357649Fa569fd763", 'latest'],
                        'id': 1 + index * 100}

        self.data_TX_count = {'jsonrpc': '2.0',
                         'method': 'eth_getBlockTransactionCountByNumber',
                         'params': [],
                         'id': 2 + index * 100}

        self.data_blockNumber = {'jsonrpc': '2.0',
                            'method': 'eth_blockNumber',
                            'params': [],
                            'id': 3 + index * 100}

        self.data_get_TX_by_index = {'jsonrpc': '2.0',
                                'method': 'eth_getTransactionByBlockNumberAndIndex',
                                'params': [],
                                'id': 4 + index * 100}

        self.data_get_TX_receipt = {'jsonrpc': '2.0',
                               'method': 'eth_getTransactionReceipt',
                               'params': [],
                               'id': 5 + index * 100}
        self.list_address = []
        self.list_contract = {}
        self.step = 100000
        self.index = index

    def run(self):
        for i in range(self.index * self.step, (self.index + 1) * self.step - 1):
            if (i%1000 == 0):
                print 'Thread ' + str(self.index) + ' is processing block: ' + str(i)
                print "Number of contracts so far: " + str(len(self.list_contract.keys()))
            self.data_TX_count['params'] = [str(hex(i))]
            r = requests.post(url, data=json.dumps(self.data_TX_count), allow_redirects=True)
            tx_count = int(get_result(r.content), 16)
            for tx_id in range(tx_count):
                self.data_get_TX_by_index['params'] = [str(hex(i)), str(hex(tx_id))]
                r = requests.post(url, data=json.dumps(self.data_get_TX_by_index), allow_redirects=True)
                tx = get_result(r.content)

                if (tx['to'] == None):  # this TX creates a contract
                    self.data_get_TX_receipt['params'] = [tx['hash']]
                    r = requests.post(url, data=json.dumps(self.data_get_TX_receipt), allow_redirects=True)
                    tx_receipt = get_result(r.content)
                    if tx_receipt['contractAddress'] == None:
                        continue

                    self.data_getCode['params'][0] = tx_receipt['contractAddress']
                    r = requests.post(url, data=json.dumps(self.data_getCode), allow_redirects=True)
                    code = get_result(r.content)
                    if len(code) > 2:
                        self.list_contract[tx_receipt['contractAddress']] = [code, tx['hash']]

        with open('contract' + str(self.index) + '.json', 'w') as outfile:
            json.dump(self.list_contract, outfile)


list_threads = []
try:
    for i in range(11):
        new_thread = MyThread(i)
        list_threads.append(new_thread)
    for my_thread in list_threads:
        my_thread.start()
except Exception as e:
    print e
    print "Error: unable to start thread"