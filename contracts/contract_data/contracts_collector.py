import urllib
import urllib2
import requests
import threading
import json
from time import sleep
url = 'http://localhost:8545/'
import os.path

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

        self.data_get_TX = {'jsonrpc': '2.0',
                               'method': 'eth_getTransactionByHash',
                               'params': [],
                               'id': 5 + index * 100}

        self.data_get_TX_receipt = {'jsonrpc': '2.0',
                               'method': 'eth_getTransactionReceipt',
                               'params': [],
                               'id': 6 + index * 100}
        self.list_address = []
        self.list_contract = {}
        self.index = index

        self.low = index*10000
        self.high = (index + 1)*10000
        # print self.low, self.high
        self.sess = requests.Session()
        self.adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
        self.sess.mount('http://', self.adapter)

    def run(self):
        for i in range(self.low, self.high):
            if i%1000 == 0:
                print 'Thread ' + str(self.index) + ' is processing block: ' + str(i)
                print "Number of contracts in Thread " + str(self.index) + " so far: " + str(len(self.list_contract))
            #     with open('contract_' + str(i) + '.json', 'w') as outfile:
            #         json.dump(self.list_contract, outfile)
            #         self.list_contract.clear()
            self.data_TX_count['params'] = [str(hex(i))]
            r = self.sess.get(url, data=json.dumps(self.data_TX_count), allow_redirects=True)
            tx_count = int(get_result(r.content), 16)
            r.close()
            for tx_id in range(tx_count):
                self.data_get_TX_by_index['params'] = [str(hex(i)), str(hex(tx_id))]
                r = self.sess.get(url, data=json.dumps(self.data_get_TX_by_index), allow_redirects=True)
                tx = get_result(r.content)
                r.close()
                if (tx['to'] == None):  # this TX creates a contract
                    self.data_get_TX_receipt['params'] = [tx['hash']]
                    r = self.sess.get(url, data=json.dumps(self.data_get_TX_receipt), allow_redirects=True)
                    tx_receipt = get_result(r.content)
                    r.close()
                    if tx_receipt['contractAddress'] == None:
                        continue

                    self.data_getCode['params'][0] = tx_receipt['contractAddress']
                    r = self.sess.get(url, data=json.dumps(self.data_getCode), allow_redirects=True)
                    code = get_result(r.content)
                    r.close()

                    if len(code) > 2:
                        self.data_get_TX['params'] = [tx['hash']]
                        r = self.sess.get(url, data=json.dumps(self.data_get_TX), allow_redirects=True)
                        tx_detail = get_result(r.content)
                        r.close()
                        tx_input = tx_detail['input']
                        # init_data = tx_input[:len(tx_input)-len(code)+2]
                        self.list_contract[tx_receipt['contractAddress']] = [tx_input, code, tx['hash']]

        # Print the last run
        print 'Thread ' + str(self.index) + ' is processing block: ' + str(i)
        print "Number of contracts in Thread " + str(self.index) + " so far: " + str(len(self.list_contract))
        with open('contract_' + str(self.high) + '.json', 'w') as outfile:
            json.dump(self.list_contract, outfile)
            self.list_contract.clear()

list_threads = []
try:
    for i in range(0, 4):
        new_thread = MyThread(i)
        list_threads.append(new_thread)
    for my_thread in list_threads:
        my_thread.start()
except Exception as e:
    print e
    print "Error: unable to start thread"