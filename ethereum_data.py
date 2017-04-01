import json
import requests

def getBalance(address):
	apiEndPoint = "https://api.etherscan.io/api?module=account&action=balance&address=" + address + "&tag=latest&apikey=VT4IW6VK7VES1Q9NYFI74YKH8U7QW9XRHN"
	r = requests.get(apiEndPoint)
	result = json.loads(r.text)
	status = result['message']
	if status == "OK":
		return result['result'] 
	return 0