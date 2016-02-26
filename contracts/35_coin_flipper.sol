// This contract is designed to demonstrate the generation of a random number.
// If you submit a betAndFlip() request after block 180,000 has just been mined,
// (i.e. when block 180,000 is the "best block" on stats.ethdev.gov and the most recent listed on any block explorer site), 
// then the transaction will get mined/processed in block 180,001. (most of the time, anyway... it may be a block or two later)
// Once the transaction is mined, then block.number will become 180,002 while the flipping is underway.
// Any attempt to get block.blockhash(180,002) will return 0x000000000...
// That's why betAndFlip uses blocknumber - 1 for its hash.
// At first I thought "Wait, if we have to use the block in past, couldn't the gambler know that?" And the answer is "no". 
// All the gambler knows at the time of bet submission is 180,000. We use 180,001 which is brand new and known and 180,002 is underway.

// NOTE: This contract is only meant to be used by you for testing purposes. I'm not responsible for lost funds if it's not bulletproof.
// 		 You can change msg.sender.send(...) to creator.send(...) in betAndFlip() to make sure funds only go back to YOUR account. 

// NOTE: I don't know how this will behave with multiple potential bettors (or even just multiple bets) per block. It is meant for your single, one-per-block use only.

// NOTE: Use more gas on the betAndFlip(). I set mine to 1,000,000 and the rest is automatically refunded (I think). At current prices 9/3/2015, it's negligible anyway.

contract CoinFlipper {

    address creator;
    int lastgainloss;
    string lastresult;
    uint lastblocknumberused;
    bytes32 lastblockhashused;

    function CoinFlipper() private 
    {
        creator = msg.sender; 								
        lastresult = "no wagers yet";
        lastgainloss = 0;
    }
	
    function getEndowmentBalance() constant returns (uint)
    {
    	return this.balance;
    }
    
    // this is probably unnecessary and gas-wasteful. The lastblockhashused should be random enough. Adding the rest of these deterministic factors doesn't change anything. 
    // This does, however, let the bettor introduce a random seed by wagering different amounts. wagering 1 ETH will produce a completely different hash than 1.000000001 ETH
    
    function sha(uint128 wager) constant private returns(uint256)  	// DISCLAIMER: This is pretty random... but not truly random.
    { 
        return uint256(sha3(block.difficulty, block.coinbase, now, lastblockhashused, wager));  
    }
    
    function betAndFlip() public               
    {
    	if(msg.value > 340282366920938463463374607431768211455)  	// value can't be larger than (2^128 - 1) which is the uint128 limit
    	{
    		lastresult = "wager too large";
    		lastgainloss = 0;
    		msg.sender.send(msg.value); // return wager
    		return;
    	}		  
    	else if((msg.value * 2) > this.balance) 					// contract has to have 2*wager funds to be able to pay out. (current balance INCLUDES the wager sent)
    	{
    		lastresult = "wager larger than contract's ability to pay";
    		lastgainloss = 0;
    		msg.sender.send(msg.value); // return wager
    		return;
    	}
    	else if (msg.value == 0)
    	{
    		lastresult = "wager was zero";
    		lastgainloss = 0;
    		// nothing wagered, nothing returned
    		return;
    	}
    		
    	uint128 wager = uint128(msg.value);          				// limiting to uint128 guarantees that conversion to int256 will stay positive
    	
    	lastblocknumberused = block.number - 1 ;
    	lastblockhashused = block.blockhash(lastblocknumberused);
    	uint128 lastblockhashused_uint = uint128(lastblockhashused) + wager;
    	uint hashymchasherton = sha(lastblockhashused_uint);
    	
	    if( hashymchasherton % 2 == 0 )
	   	{
	    	lastgainloss = int(wager) * -1;
	    	lastresult = "loss";
	    	// they lost. Return nothing.
	    	return;
	    }
	    else
	    {
	    	lastgainloss = wager;
	    	lastresult = "win";
	    	msg.sender.send(wager * 2);  // They won. Return bet and winnings.
	    } 		
    }
    
  	function getLastBlockNumberUsed() constant returns (uint)
    {
        return lastblocknumberused;
    }
    
    function getLastBlockHashUsed() constant returns (bytes32)
    {
    	return lastblockhashused;
    }

    function getResultOfLastFlip() constant returns (string)
    {
    	return lastresult;
    }
    
    function getPlayerGainLossOnLastFlip() constant returns (int)
    {
    	return lastgainloss;
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

var coinflipperContract = web3.eth.contract([{
    "constant": true,
    "inputs": [],
    "name": "getPlayerGainLossOnLastFlip",
    "outputs": [{
        "name": "",
        "type": "int256"
    }],
    "type": "function"
}, {
    "constant": false,
    "inputs": [],
    "name": "betAndFlip",
    "outputs": [],
    "type": "function"
}, {
    "constant": true,
    "inputs": [],
    "name": "getLastBlockNumberUsed",
    "outputs": [{
        "name": "",
        "type": "uint256"
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
    "name": "getEndowmentBalance",
    "outputs": [{
        "name": "",
        "type": "uint256"
    }],
    "type": "function"
}, {
    "constant": true,
    "inputs": [],
    "name": "getLastBlockHashUsed",
    "outputs": [{
        "name": "",
        "type": "bytes32"
    }],
    "type": "function"
}, {
    "constant": true,
    "inputs": [],
    "name": "getResultOfLastFlip",
    "outputs": [{
        "name": "",
        "type": "string"
    }],
    "type": "function"
}, {
    "inputs": [],
    "type": "constructor"
}]);

var coinflipper = coinflipperContract.new({
    from: web3.eth.accounts[0],
    data: '60606040525b33600060006101000a81548173ffffffffffffffffffffffffffffffffffffffff02191690830217905550604060405190810160405280600d81526020017f6e6f2077616765727320796574000000000000000000000000000000000000008152602001506003600050908051906020019082805482825590600052602060002090601f0160209004810192821560b7579182015b8281111560b6578251826000505591602001919060010190609a565b5b50905060de919060c2565b8082111560da576000818150600090555060010160c2565b5090565b505060006002600050819055505b610923806100fb6000396000f3006060604052361561007f576000357c0100000000000000000000000000000000000000000000000000000000900480630efafd011461008157806325d8dcf2146100a257806334dbe44d146100af57806341c0e1b5146100d05780635acce36b146100dd57806394c3fa2e146100fe578063cee6f93c1461011f5761007f565b005b61008c6004506107e6565b6040518082815260200191505060405180910390f35b6100ad6004506101bc565b005b6100ba600450610744565b6040518082815260200191505060405180910390f35b6100db6004506107f8565b005b6100e8600450610198565b6040518082815260200191505060405180910390f35b610109600450610756565b6040518082815260200191505060405180910390f35b61012a600450610768565b60405180806020018281038252838181518152602001915080519060200190808383829060006004602084601f0104600302600f01f150905090810190601f16801561018a5780820380516001836020036101000a031916815260200191505b509250505060405180910390f35b60003073ffffffffffffffffffffffffffffffffffffffff163190506101b9565b90565b600060006fffffffffffffffffffffffffffffffff3411156102d657604060405190810160405280600f81526020017f776167657220746f6f206c6172676500000000000000000000000000000000008152602001506003600050908051906020019082805482825590600052602060002090601f01602090048101928215610262579182015b82811115610261578251826000505591602001919060010190610243565b5b50905061028d919061026f565b80821115610289576000818150600090555060010161026f565b5090565b505060006002600050819055503373ffffffffffffffffffffffffffffffffffffffff16600034604051809050600060405180830381858888f1935050505050610740566104ee565b3073ffffffffffffffffffffffffffffffffffffffff163160023402111561041c57606060405190810160405280602b81526020017f7761676572206c6172676572207468616e20636f6e747261637427732061626981526020017f6c69747920746f207061790000000000000000000000000000000000000000008152602001506003600050908051906020019082805482825590600052602060002090601f016020900481019282156103a8579182015b828111156103a7578251826000505591602001919060010190610389565b5b5090506103d391906103b5565b808211156103cf57600081815060009055506001016103b5565b5090565b505060006002600050819055503373ffffffffffffffffffffffffffffffffffffffff16600034604051809050600060405180830381858888f1935050505050610740566104ed565b60003414156104ec57604060405190810160405280600e81526020017f776167657220776173207a65726f0000000000000000000000000000000000008152602001506003600050908051906020019082805482825590600052602060002090601f016020900481019282156104af579182015b828111156104ae578251826000505591602001919060010190610490565b5b5090506104da91906104bc565b808211156104d657600081815060009055506001016104bc565b5090565b50506000600260005081905550610740565b5b5b34915060014303600460005081905550600460005054406005600050819055506105178261088c565b90506000600282061415610623577fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff826fffffffffffffffffffffffffffffffff1602600260005081905550604060405190810160405280600481526020017f6c6f7373000000000000000000000000000000000000000000000000000000008152602001506003600050908051906020019082805482825590600052602060002090601f016020900481019282156105ed579182015b828111156105ec5782518260005055916020019190600101906105ce565b5b50905061061891906105fa565b8082111561061457600081815060009055506001016105fa565b5090565b50506107405661073f565b816fffffffffffffffffffffffffffffffff16600260005081905550604060405190810160405280600381526020017f77696e00000000000000000000000000000000000000000000000000000000008152602001506003600050908051906020019082805482825590600052602060002090601f016020900481019282156106c9579182015b828111156106c85782518260005055916020019190600101906106aa565b5b5090506106f491906106d6565b808211156106f057600081815060009055506001016106d6565b5090565b50503373ffffffffffffffffffffffffffffffffffffffff166000600284026fffffffffffffffffffffffffffffffff16604051809050600060405180830381858888f19350505050505b5b5050565b60006004600050549050610753565b90565b60006005600050549050610765565b90565b60206040519081016040528060008152602001506003600050805480601f016020809104026020016040519081016040528092919081815260200182805480156107d757820191906000526020600020905b8154815290600101906020018083116107ba57829003601f168201915b505050505090506107e3565b90565b600060026000505490506107f5565b90565b600060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff163373ffffffffffffffffffffffffffffffffffffffff16141561088957600060009054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff16ff5b5b565b600044414260056000505485604051808681526020018573ffffffffffffffffffffffffffffffffffffffff166c01000000000000000000000000028152601401848152602001838152602001826fffffffffffffffffffffffffffffffff1670010000000000000000000000000000000002815260100195505050505050604051809103902060019004905061091e565b91905056',
    gas: 1000000,
    value: 1000000000000000000 // endowment of 1 eth
}, function(e, contract) {
    if (typeof contract.address != 'undefined') {
        console.log(e, contract);
        console.log('Contract mined! address: ' + contract.address + ' transactionHash: ' + contract.transactionHash);
    }
});

// ********** after deployment

> coinflipper.getEndowmentBalance();
6000000000000000000
> coinflipper.betAndFlip.sendTransaction({from:eth.coinbase, value: 1000000000000000000}); // 1 ETH. Let's see what happens
"0xc78a24881c7f70d25a817dcfcdce3347ca0cd265b7ba30a60df61e5639482bcf"
> coinflipper.getResultOfLastFlip();
"no wagers yet"
> coinflipper.getResultOfLastFlip(); // has the tx been mined yet?
"no wagers yet"
> coinflipper.getResultOfLastFlip(); // has the tx been mined yet?
"no wagers yet"
> coinflipper.getResultOfLastFlip(); // has the tx been mined yet? I'm waiting...
"no wagers yet"
> coinflipper.getResultOfLastFlip(); // has the tx been mined yet? I'm waiting...
"win"
> coinflipper.getPlayerGainLossOnLastFlip();
1000000000000000000
> web3.fromWei(coinflipper.getPlayerGainLossOnLastFlip());
1
> coinflipper.getEndowmentBalance();
5000000000000000000
> coinflipper.betAndFlip.sendTransaction({from:eth.coinbase, value: 3000000000000000000}); // 3 ETH. Let's see what happens
"0xcae272652649e07c343674d15b40a086c559408d9c66d8022de3f54932bf3d9f"
> coinflipper.getResultOfLastFlip(); // has the tx been mined yet? I'm waiting...
"loss"
> coinflipper.getEndowmentBalance();
8000000000000000000
> web3.fromWei(coinflipper.getPlayerGainLossOnLastFlip());
-3
> web3.eth.getBalance(eth.coinbase);
1806931309200681965
> web3.fromWei(web3.eth.getBalance(eth.coinbase));
1.806931309200681965
> coinflipper.betAndFlip.sendTransaction({from:eth.coinbase, value: 1500000000000000000}); // 1.5 ETH. Let's see what happens
"0xc99add577b3180ca58b1a8219f2cd282f6b77edb63e1e384b05abc434753b1a1"
> coinflipper.getResultOfLastFlip(); // has the tx been mined yet? I'm waiting...
"win"
> web3.fromWei(web3.eth.getBalance(eth.coinbase));
3.304471659200681965
> web3.fromWei(web3.eth.getBalance(eth.coinbase));
> coinflipper.kill.sendTransaction({from:eth.coinbase});
"0xed9f9e49cca76965ba32acce2b2f0b17ada467e52d55b803c26cc7132ba108fa"
  
  
 // ************** after separate deployment with smaller endowment to test payout safety limit
 
  Contract mined! address: 0xb0824b45f4a4c1ee4df356378d555c7f4366fa4c transactionHash: 0x065580a137654a816abdeb27e690e6c96f59dce92a9e8064f6f8c3c49cf0b681

> coinflipper.getEndowmentBalance();   // 1 eth
1000000000000000000
> coinflipper.betAndFlip.sendTransaction({from:eth.coinbase, value: 3000000000000000000}); // 3 ETH, more than endowment can handle. Let's see what happens
"0x66b5ae12f215d1bcf1a1656f79ccedc69612dc891f35dce5dbd6ead8854f0cb1"
> coinflipper.getResultOfLastFlip(); // has the tx been mined yet? I'm waiting...
"no wagers yet"
> coinflipper.getResultOfLastFlip(); // has the tx been mined yet? I'm waiting...
"no wagers yet"
> coinflipper.getResultOfLastFlip(); // has the tx been mined yet? I'm waiting...
"no wagers yet"
> coinflipper.getResultOfLastFlip(); // has the tx been mined yet? I'm waiting...
"wager larger than contract's ability to pay"
> coinflipper.getEndowmentBalance();
1000000000000000000
> coinflipper.betAndFlip.sendTransaction({from:eth.coinbase, value: 500000000000000000}); // .5 ETH.
"0x16ef5f3f0778b1252dcfd3b55f09ab97382f23d8ad7489f1f1b45d88eb7588f5"
> coinflipper.getResultOfLastFlip(); // has the tx been mined yet? I'm waiting...
"loss"
  
  
  
 */