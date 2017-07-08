# this the interface to create your own data source 
# this class pings a private / public blockchain to get the balance and code information 

from web3 import Web3, KeepAliveRPCProvider

class EthereumData:
	def __init__(self):
		self.host = 'x.x.x.x'
		self.port = '8545'
		self.web3 = Web3(KeepAliveRPCProvider(host=self.host, port=self.port))		

	def getBalance(self, address): 
		return self.web3.eth.getBalance(address)

	def getCode(self, address):		
		return self.web3.eth.getCode(address)