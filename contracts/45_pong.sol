// Supposedly, contracts can get non-constant return values from other contracts. (Whereas you can't from web3/geth.)
// These two contracts are meant to test this. Like so:

// 1. Deploy Pong with a pongval.
// 2. Deploy Ping, giving it the address of Pong.
// 3. Call Ping.getPongvalRemote() using a sendTransaction...
// 4. ... which retreives the value of pongval from Pong.
// 5. If successful Ping.getPongval() should return the value from step 1.

// UPDATE: Pong doesn't need a copy of PongvalRetriever.
//contract PongvalRetriever {
// 	int8 pongval_tx_retrieval_attempted = 0;
//	function getPongvalTransactional() public returns (int8){	// tells Ping how to interact with Pong.
//		pongval_tx_retrieval_attempted = -1;
//		return pongval_tx_retrieval_attempted;
//	}
//}

contract Pong {

    address creator;
    int8 pongval;
    int8 pongval_tx_retrieval_attempted = 0;
    
	/*********
 	 Step 1: Deploy Pong
 	 *********/
    function Pong(int8 _pongval) 
    {
        creator = msg.sender; 
        pongval = _pongval;
    }
	
	/*********
	 Step 4. Transactionally return pongval, overriding PongvalRetriever
	 *********/	
	function getPongvalTransactional() public returns (int8)
    {
    	pongval_tx_retrieval_attempted = 1;
    	return pongval;
    }
    
// ----------------------------------------------------------------------------------------------------------------------------------------
    
    /*********
	 pongval getter/setter, just in case.
	 *********/
	function getPongvalConstant() public constant returns (int8)
    {
    	return pongval;
    } 
	 	
	function setPongval(int8 _pongval)
	{
		pongval = _pongval;
	}
	
	function getPongvalTxRetrievalAttempted() constant returns (int8)
	{
		return pongval_tx_retrieval_attempted;
	}
	
	/****
	 For double-checking this contract's address
	 ****/
	function getAddress() constant returns (address)
	{
		return this;
	}
	
    /**********
     Standard kill() function to recover funds 
     **********/
    
    function kill()
    { 
        if (msg.sender == creator)
            suicide(creator);  // kills this contract and sends remaining funds back to creator
    }
}

/*
 var _pongval = -22;

var pongContract = web3.eth.contract([{
    "constant": false,
    "inputs": [{
        "name": "_pongval",
        "type": "int8"
    }],
    "name": "setPongval",
    "outputs": [],
    "type": "function"
}, {
    "constant": true,
    "inputs": [],
    "name": "getAddress",
    "outputs": [{
        "name": "",
        "type": "address"
    }],
    "type": "function"
}, {
    "constant": true,
    "inputs": [],
    "name": "getPongvalConstant",
    "outputs": [{
        "name": "",
        "type": "int8"
    }],
    "type": "function"
}, {
    "constant": false,
    "inputs": [],
    "name": "kill",
    "outputs": [],
    "type": "function"
}, {
    "constant": true,
    "inputs": [],
    "name": "getPongvalTxRetrievalAttempted",
    "outputs": [{
        "name": "",
        "type": "int8"
    }],
    "type": "function"
}, {
    "constant": false,
    "inputs": [],
    "name": "getPongvalTransactional",
    "outputs": [{
        "name": "",
        "type": "int8"
    }],
    "type": "function"
}, {
    "inputs": [{
        "name": "_pongval",
        "type": "int8"
    }],
    "type": "constructor"
}]);
var pong = pongContract.new(
    _pongval, {
        from: web3.eth.accounts[0],
        data: '60606040526000600060156101000a81548160ff02191690837f01000000000000000000000000000000000000000000000000000000000000009081020402179055506040516020806103808339016040526060805190602001505b33600060006101000a81548173ffffffffffffffffffffffffffffffffffffffff0219169083021790555080600060146101000a81548160ff02191690837f01000000000000000000000000000000000000000000000000000000000000009081020402179055505b506102ad806100d36000396000f360606040523615610074576000357c01000000000000000000000000000000000000000000000000000000009004806323a1c2711461007657806338cc48311461008957806340193d17146100c057806341c0e1b5146100e4578063a396541e146100f1578063fb5d57291461011557610074565b005b6100876004803590602001506101d8565b005b610094600450610155565b604051808273ffffffffffffffffffffffffffffffffffffffff16815260200191505060405180910390f35b6100cb6004506101bc565b604051808260000b815260200191505060405180910390f35b6100ef600450610219565b005b6100fc600450610139565b604051808260000b815260200191505060405180910390f35b610120600450610162565b604051808260000b815260200191505060405180910390f35b6000600060159054906101000a900460000b9050610152565b90565b600030905061015f565b90565b60006001600060156101000a81548160ff02191690837f0100000000000000000000000000000000000000000000000000000000000000908102040217905550600060149054906101000a900460000b90506101b9565b90565b6000600060149054906101000a900460000b90506101d5565b90565b80600060146101000a81548160ff02191690837f01000000000000000000000000000000000000000000000000000000000000009081020402179055505b50565b600060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff1614156102aa57600060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16ff5b5b56',
        gas: 1000000
    },
    function(e, contract) {
        if (typeof contract.address != 'undefined') {
            console.log(e, contract);
            console.log('Contract mined! address: ' + contract.address + ' transactionHash: ' + contract.transactionHash);
        }
    });
																					// ****************************************************************** IMPORTANT!!!!!
var _pongAddress = web3.toBigNumber('0xbfb1316ab1b8e9a2a39c1c96ad325ea80c9e041f');  // ****************************************************************** IMPORTANT!!!!!
																					// ****************************************************************** IMPORTANT!!!!!

var pingContract = web3.eth.contract([{
    "constant": false,
    "inputs": [],
    "name": "getAddress",
    "outputs": [{
        "name": "",
        "type": "address"
    }],
    "type": "function"
}, {
    "constant": false,
    "inputs": [{
        "name": "_pongAddress",
        "type": "address"
    }],
    "name": "setPongAddress",
    "outputs": [],
    "type": "function"
}, {
    "constant": false,
    "inputs": [],
    "name": "getPongvalRemote",
    "outputs": [],
    "type": "function"
}, {
    "constant": true,
    "inputs": [],
    "name": "getPongvalConstant",
    "outputs": [{
        "name": "",
        "type": "int8"
    }],
    "type": "function"
}, {
    "constant": false,
    "inputs": [],
    "name": "kill",
    "outputs": [],
    "type": "function"
}, {
    "constant": true,
    "inputs": [],
    "name": "getPongAddress",
    "outputs": [{
        "name": "",
        "type": "address"
    }],
    "type": "function"
}, {
    "constant": false,
    "inputs": [],
    "name": "getPongvalTransactional",
    "outputs": [{
        "name": "",
        "type": "int8"
    }],
    "type": "function"
}, {
    "inputs": [{
        "name": "_pongAddress",
        "type": "address"
    }],
    "type": "constructor"
}]);
var ping = pingContract.new(
    _pongAddress, {
        from: web3.eth.accounts[0],
        data: '60606040526000600060006101000a81548160ff02191690837f01000000000000000000000000000000000000000000000000000000000000009081020402179055506040516020806104dc8339016040526060805190602001505b33600160006101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908302179055507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff600060016101000a81548160ff02191690837f010000000000000000000000000000000000000000000000000000000000000090810204021790555080600060026101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908302179055505b506103be8061011e6000396000f36060604052361561007f576000357c01000000000000000000000000000000000000000000000000000000009004806338cc48311461008157806339df1608146100b85780633af94817146100cb57806340193d17146100d857806341c0e1b5146100fc578063fab43cb114610109578063fb5d5729146101405761007f565b005b61008c60045061031d565b604051808273ffffffffffffffffffffffffffffffffffffffff16815260200191505060405180910390f35b6100c96004803590602001506102bf565b005b6100d66004506101dd565b005b6100e36004506102a3565b604051808260000b815260200191505060405180910390f35b61010760045061032a565b005b6101146004506102ee565b604051808273ffffffffffffffffffffffffffffffffffffffff16815260200191505060405180910390f35b61014b600450610164565b604051808260000b815260200191505060405180910390f35b60007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff600060006101000a81548160ff02191690837f0100000000000000000000000000000000000000000000000000000000000000908102040217905550600060009054906101000a900460000b90506101da565b90565b600060029054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1663fb5d5729604051817c01000000000000000000000000000000000000000000000000000000000281526004018090506020604051808303816000876161da5a03f1156100025750505060405151600060016101000a81548160ff02191690837f01000000000000000000000000000000000000000000000000000000000000009081020402179055505b565b6000600060019054906101000a900460000b90506102bc565b90565b80600060026101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908302179055505b50565b6000600060029054906101000a900473ffffffffffffffffffffffffffffffffffffffff16905061031a565b90565b6000309050610327565b90565b600160009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff1614156103bb57600160009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16ff5b5b56',
        gas: 1000000
    },
    function(e, contract) {
        if (typeof contract.address != 'undefined') {
            console.log(e, contract);
            console.log('Contract mined! address: ' + contract.address + ' transactionHash: ' + contract.transactionHash);
        }
    });

> pong.getPongvalConstant(); // Was Pong.pongval initialized correctly?
- 22 // yes
    > ping.getPongvalConstant(); // Does Ping know what pongval is yet?
- 1 // Nope. (This is correct at this point.)
    > ping.getPongvalRemote.sendTransaction({
    from: eth.coinbase,
    gas: 1000000
}); // Tell Ping to get the pongval from Pong.
"0xc0ec18186cfccecc231af16c3caff6ee217c05833834dfaebe6ca119b51ca3a7" > ping.getPongvalConstant(); // Does Ping know what pongval is yet?
- 1 // Nope. Tx hasn't been mined yet.
    > ping.getPongvalConstant(); // How about now?
- 22 // yep! Success!

*/
