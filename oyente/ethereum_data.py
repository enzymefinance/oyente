# this the interface to create your own data source
# this class pings etherscan to get the latest code and balance information

import requests
import logging

log = logging.getLogger(__name__)

class EthereumData:
        def __init__(self, contract_address):
            self.apiDomain = "https://api.etherscan.io/api"
            self.apikey = "VT4IW6VK7VES1Q9NYFI74YKH8U7QW9XRHN"
            self.contract_addr = contract_address

        def getBalance(self, address):
            try:
                apiEndPoint = "%s?module=account&action=balance&address=%s&tag=latest&apikey=%s" % (self.apiDomain, address, self.apikey)
                r = requests.get(apiEndPoint)
                result = r.json()
                status = result['message']
                if status == "OK":
                    result = result['result']
            except Exception as e:
                log.exception("Error at: contract address: %s" % address)
                raise e
            return result

        def getCode(self, address):
            try:
                apiEndPoint = "%s?module=proxy&action=eth_getCode&address=%s&tag=latest&apikey=%s" % (self.apiDomain, address, self.apikey)
                r = requests.get(apiEndPoint)
                result = r.json()["result"]
            except Exception as e:
                log.exception("Error at: contract address: %s" % address)
                raise e
            return result

        def getStorageAt(self, position):
            try:
                apiEndPoint = "%s?module=proxy&action=eth_getStorageAt&address=%s&position=%s&tag=latest&apikey=%s" % (self.apiDomain, self.contract_addr, hex(position), self.apikey)
                r = requests.get(apiEndPoint)
                result = r.json()["result"]
            except Exception as e:
                log.exception("Error at: contract address: %s, position: %s" % (self.contract_addr, position))
                raise e
            return int(result, 16)
