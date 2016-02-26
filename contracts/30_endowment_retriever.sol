contract EndowmentRetriever {

    address creator;
    uint contract_creation_value; // original endowment

    function EndowmentRetriever() public 
    {
        creator = msg.sender; 								
        contract_creation_value = msg.value;  				// the endowment of this contract in wei 
    }
	
    function getContractCreationValue() constant returns (uint) // returns the original endowment of the contract
    {										              		// set at creation time with "value: <someweivalue>"	
    	return contract_creation_value;                         // this was the "balance" of the contract at creation time
    }
    
    function sendOneEtherHome() public         	
    {						
    	creator.send(1000000000000000000);				// send 1 ETH home
    }
        
    /**********
     Standard kill() function to recover funds 
     **********/
    
    function kill()
    { 
        if (msg.sender == creator)
        {
            suicide(creator);  // kills this contract and sends remaining funds back to creator
        }
    }
        
}


/*

********************** DEPLOYED WITH ******************************

var endowmentretrieverContract = web3.eth.contract([{
    "constant": false,
    "inputs": [],
    "name": "kill",
    "outputs": [],
    "type": "function"
}, {
    "constant": true,
    "inputs": [],
    "name": "getContractCreationValue",
    "outputs": [{
        "name": "",
        "type": "uint256"
    }],
    "type": "function"
}, {
    "constant": false,
    "inputs": [],
    "name": "sendOneEtherHome",
    "outputs": [],
    "type": "function"
}, {
    "inputs": [],
    "type": "constructor"
}]);

var endowmentretriever = endowmentretrieverContract.new({
    from: web3.eth.accounts[0],
    data: '60606040525b33600060006101000a81548173ffffffffffffffffffffffffffffffffffffffff02191690830217905550346001600050819055505b6101908061004a6000396000f30060606040526000357c01000000000000000000000000000000000000000000000000000000009004806341c0e1b51461004f5780636c6f1d931461005c578063f239e5281461007d5761004d565b005b61005a6004506100fc565b005b61006760045061008a565b6040518082815260200191505060405180910390f35b61008860045061009c565b005b60006001600050549050610099565b90565b600060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff166000670de0b6b3a7640000604051809050600060405180830381858888f19350505050505b565b600060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff16141561018d57600060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16ff5b5b56',
    gas: 1000000,
    value: 3000000000000000000 // START CONTRACT WITH AN ENDOWMENT OF 3 ETH
}, function(e, contract) {
    if (typeof contract.address != 'undefined') {
        console.log(e, contract);
        console.log('Contract mined! address: ' + contract.address + ' transactionHash: ' + contract.transactionHash);
    }
})


********************** EXECUTION IN GETH ******************************

> endowmentretriever.getContractCreationValue();
3000000000000000000
> web3.fromWei(endowmentretriever.getContractCreationValue());
3																						    // After creation, we can verify it holds 3 ETH
> web3.fromWei(eth.getBalance(eth.coinbase));										
6.75688459417901484																			// Our coinbase now holds 6.75 vs 9.75 before
>  var receipt = web3.eth.getTransactionReceipt('0x1d81b2dc3c3930edd766e153c30e598994018aeac36a9beee982a392b4bc200f');
undefined
> receipt
{
  blockHash: "0x04246ae26cb9b51128d1c87e8363d4bcefad90ea98586f606522a348d2305eee",
  blockNumber: 174093,
  contractAddress: "0x1c7c3f36d59bcaa4a7dfdf58f347ff6f675bf4d3",
  cumulativeGasUsed: 169243,
  gasUsed: 169243,
  logs: [],
  transactionHash: "0x1d81b2dc3c3930edd766e153c30e598994018aeac36a9beee982a392b4bc200f",
  transactionIndex: 0
}
> var tx = endowmentretriever.sendOneEtherHome.sendTransaction({from:eth.coinbase});
undefined
> var sentHomeReceipt = web3.eth.getTransactionReceipt(tx);
undefined
> sentHomeReceipt
{
  blockHash: "0x19293ed30899b637510390cbfb1fe7ed8638524ebd322dc2f9889b7216b1f357",
  blockNumber: 174119,
  contractAddress: null,
  cumulativeGasUsed: 28302,
  gasUsed: 28302,
  logs: [],
  transactionHash: "0xeaea5f0bf9dd8df4a74c43b1e20bbc08d7c02b6707b0ece724df91f6ce67fb17",
  transactionIndex: 0
}
> web3.fromWei(eth.getBalance('0x1c7c3f36d59bcaa4a7dfdf58f347ff6f675bf4d3'));
2																							// after the first exec, the balance is down to 2
> web3.fromWei(eth.getBalance(eth.coinbase));										
7.75688459417901484																			// coinbase up to 7.75 from 6.75
> var tx = endowmentretriever.sendOneEtherHome.sendTransaction({from:eth.coinbase});
undefined
> var sentHomeReceipt = web3.eth.getTransactionReceipt(tx);
undefined
> sentHomeReceipt
{
  blockHash: "0x8fdd9829040c25e0bd902fdc35e643b1f85f326c8b58a16db5897f26619ae83a",
  blockNumber: 174128,
  contractAddress: null,
  cumulativeGasUsed: 28302,
  gasUsed: 28302,
  logs: [],
  transactionHash: "0x009c584a521bef7c209fd879cafc27be6bb86eb70f54b46568a972e694fec82c",
  transactionIndex: 0
}
> web3.fromWei(eth.getBalance('0x1c7c3f36d59bcaa4a7dfdf58f347ff6f675bf4d3'));
1																							// after the first exec, the balance is down to 2
> web3.fromWei(eth.getBalance(eth.coinbase));										
8.75688459417901484																			// coinbase up to 8.75 from 7.75
> var tx = endowmentretriever.sendOneEtherHome.sendTransaction({from:eth.coinbase});
undefined
> var sentHomeReceipt = web3.eth.getTransactionReceipt(tx);
undefined
> sentHomeReceipt
{
  blockHash: "0xa63fce8addb966d9d2ab4fc9e05498af1fd6e0e6dcee258d22bed1882806d770",
  blockNumber: 174133,
  contractAddress: null,
  cumulativeGasUsed: 28302,
  gasUsed: 28302,
  logs: [],
  transactionHash: "0x39b945115e98b390041cf39886d67cd1fe0c265f74f49df15651a35f822faaaa",
  transactionIndex: 0
}
> web3.fromWei(eth.getBalance(eth.coinbase));
9.75546949417901484																			// coinbase back to original value of 9.75
> web3.fromWei(eth.getBalance('0x1c7c3f36d59bcaa4a7dfdf58f347ff6f675bf4d3'));
0																						    // contract endowment fully depleted
> endowmentretriever.kill.sendTransaction({from:eth.coinbase});
"0x588fd4e3f2fad1a61af08aaaf9f3ab8c7ad677dc4510b65d666bac644e7ca352"

*/