import json
import requests

class EthereumData:
	def __init__(self):
		self.apiDomain = "https://api.etherscan.io/api"
		self.apikey = "VT4IW6VK7VES1Q9NYFI74YKH8U7QW9XRHN"

	def getBalance(address):
		apiEndPoint = self.apiDomain + "?module=account&action=balance&address=" + address + "&tag=latest&apikey=" + apikey
		r = requests.get(apiEndPoint)
		result = json.loads(r.text)
		status = result['message']
		if status == "OK":
			return result['result'] 
		return -1