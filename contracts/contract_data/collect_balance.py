import urllib
import urllib2
import requests
import threading
import json
url = 'http://localhost:8545/'
result = [{}]

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
        self.data_getBalance = {'jsonrpc': '2.0',
                        'method': 'eth_getBalance',
                        'params': ["0x9bA082240DBa3F9ef90038b9357649Fa569fd763", 'latest'],
                        'id': 1 + index * 100}

        self.filename = "contract_" + str(index) + "0000.json"
        print "starting thread " + str(index)
        self.balance = {}
        self.index = index
        self.sess = requests.Session()
        self.adapter = requests.adapters.HTTPAdapter(pool_connections=100, pool_maxsize=100)
        self.sess.mount('http://', self.adapter)


    def run(self):
        with open(self.filename) as json_file:
            c = json.load(json_file)
            i = 0;
            for address in c:
                i += 1
                if i%1000 == 0:
                    print 'Thread ' + str(self.filename) + ' is processing contract: ' + str(i)
                try:
                    self.data_getBalance['params'][0] = address
                    r = self.sess.get(url, data=json.dumps(self.data_getBalance), allow_redirects=True)
                    self.balance[address] = int(get_result(r.content), 16)
                    r.close()
                except Exception as e:
                    print str(e)
        # print self.balance
        result[self.index] = self.balance

list_threads = []
try:
    for i in range(1, 147):
        new_thread = MyThread(i)
        list_threads.append(new_thread)
        result.append({})
    for my_thread in list_threads:
        my_thread.start()
    for my_thread in list_threads:
        my_thread.join()
    super_dict = {}
    for small_dict in result:
        super_dict.update(small_dict)
    with open('contract_balance.json', 'w') as outfile:
        json.dump(super_dict, outfile)
except Exception as e:
    print e
    print "Error: unable to start thread"