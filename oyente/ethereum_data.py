# this the interface to create your own data source
# this class pings etherscan to get the latest code and balance information

import json
import re
import requests

class EthereumData:
	def __init__(self):
		self.apiDomain = "https://api.etherscan.io/api"
		self.apikey = "VT4IW6VK7VES1Q9NYFI74YKH8U7QW9XRHN"

	def getBalance(self, address):
		apiEndPoint = self.apiDomain + "?module=account&action=balance&address=" + address + "&tag=latest&apikey=" + self.apikey
		r = requests.get(apiEndPoint)
		result = json.loads(r.text)
		status = result['message']
		if status == "OK":
			return result['result']
		return -1

	#  def getCode(self, address):
		#  # apiEndPoint = self.apiDomain + "" + address + "&tag=latest&apikey=" + apikey
		#  # no direct endpoint for this
		#  r = requests.get("https://etherscan.io/address/" + address + "#code")
		#  html = r.text
		#  code = re.findall("<div id='verifiedbytecode2'>(\w*)<\/div>", html)[0]
		#  return code

	def getCode(self, address):
            r = requests.get("https://api.etherscan.io/api?module=proxy&action=eth_getCode&address=%s&tag=latest&apikey=%s" % (address, self.apikey))
            try:
                result = r.json()["result"]
            except Exception as e:
                with open("get_code_log", "a") as f:
                    f.write(str(e) + "\n")
                    f.write(str(address) + "\n")
                result = ""
            return result

        def getStorageAt(self, address, position):
            r = requests.get("https://api.etherscan.io/api?module=proxy&action=eth_getStorageAt&address=%s&position=%s&tag=latest&apikey=%s" % (address, hex(position), self.apikey))
            try:
                result = r.json()["result"]
            except Exception as e:
                with open("get_storage_log", "a") as f:
                    f.write(str(e) + "\n")
                    f.write(str(address) + ", " + str(position) + "\n")
                result = ""
            return result
