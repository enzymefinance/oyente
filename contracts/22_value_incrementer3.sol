// This contract demonstrates a simple non-constant (transactional) function you can call from geth.
// increment() takes TWO parameters and increments the interation value by howmuch and also sets an arbitrary customvalue.
// See below for how to make the call in geth. (incrementer3.increment.sendTransaction(3,9, {from:eth.coinbase,gas:1000000});)
// note that we needed more than the (geth) default gas of 90k this time. I chose 1 mil. (unused gas is refunded anyway)

contract Incrementer3 {

    address creator;
    int iteration;
    string whathappened;
    int customvalue;

    function Incrementer3() 
    {
        creator = msg.sender; 								
        iteration = 0;
        whathappened = "constructor executed";
    }

	// call this in geth like so: > incrementer3.increment.sendTransaction(3, 8, {from:eth.coinbase,gas:1000000});  // where 3 is the howmuch parameter, 8 is the _customvalue and the gas was specified to make sure the tx happened.
    function increment(int howmuch, int _customvalue) 
    {
    	customvalue = _customvalue;
    	if(howmuch == 0)
    	{
    		iteration = iteration + 1;
    		whathappened = "howmuch was zero. Incremented by 1. customvalue also set.";
    	}
    	else
    	{
        	iteration = iteration + howmuch;
        	whathappened = "howmuch was nonzero. Incremented by its value. customvalue also set.";
        }
        return;
    }
    
    function getCustomValue() constant returns (int)
    {
    	return customvalue;
    }
    
    function getWhatHappened() constant returns (string)
    {
    	return whathappened;
    }
    
    function getIteration() constant returns (int) 
    {
        return iteration;
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

> incrementer3.increment.sendTransaction(3,9, {from:eth.coinbase});
"0x7731880bef6e5122aead43a1e60ffda7fad0508013a8045c9c256da78fb769b2"
> incrementer3.getIteration();
0
> incrementer3.getWhatHappened();
"constructor executed"
> var tx = incrementer3.increment.sendTransaction(4,19, {from:eth.coinbase});
undefined
> tx
"0x64ddd3334cf86e6f1ec3e07d913d8da842a77758f71f6793eaf876a27caf1e3e"
> incrementer3.getWhatHappened();
"constructor executed"
> incrementer3.getIteration();
0
> var r = web3.eth.getTransactionReceipt(tx);
undefined
> r
{
  blockHash: "0xd6423bbb563808ac91ffdc1c95a0e2965d90cf24e3cc68e6284da45aba4c4ec7",
  blockNumber: 179636,
  contractAddress: null,
  cumulativeGasUsed: 111000,																// this is how much gas was needed
  gasUsed: 90000,																			// it appears that gasUsed defaults to the gas sent if it wasn't enough. more tests below.
  logs: [],
  transactionHash: "0x64ddd3334cf86e6f1ec3e07d913d8da842a77758f71f6793eaf876a27caf1e3e",
  transactionIndex: 1
}
> incrementer3.getWhatHappened();
"constructor executed"
> incrementer3.getIteration();
0
> incrementer3.getWhatHappened();
"constructor executed"
> incrementer3.getWhatHappened();
"constructor executed"
> incrementer3.increment.sendTransaction(3,9, {from:eth.coinbase,gas:10000000});
Exceeds block gas limit
    at InvalidResponse (<anonymous>:-81076:-79)
    at send (<anonymous>:-154580:-79)
    at sendTransaction (<anonymous>:-131712:-79)
    at sendTransaction (<anonymous>:-105847:-79)
    at <anonymous>:1:1

> incrementer3.increment.sendTransaction(3,9, {from:eth.coinbase,gas:1000000});
"0xca564a1a9890296893abe16ee8a3dcee9166f7a91aed5e0ab3cb182fad57288d"
> incrementer3.getWhatHappened();
"constructor executed"
> incrementer3.getWhatHappened();
"constructor executed"
> incrementer3.getWhatHappened();
"constructor executed"
> incrementer3.getIteration();
3
> incrementer3.getWhatHappened();
"howmuch was nonzero. Incremented by its value. customvalue also set."
> incrementer3.getCustomValue();
9
> {nsole.log(e, contract);endTransaction(3,8, {from:eth.coinbase});
    console.log('Contract mined! address: ' + contract.address + ' transactionHash: ' + contract.transactionHash);
> incrementer3.kill.sendTransaction({from: eth.coinbase});
"0x35599d37542ff6d1cfffbbccb122eec4d1b7289c35f9f5bfd5ddf9df7502fe69"
> var r = web3.eth.getTransactionReceipt('0xca564a1a9890296893abe16ee8a3dcee9166f7a91aed5e0ab3cb182fad57288d'); // this is the 3,9 call, not the kill.
undefined
> r
{
  blockHash: "0xd76b3a350b71bea75ab87986465b56aad781d787c98a4344a0e02fef4a6e5e12",
  blockNumber: 179674,
  contractAddress: null,
  cumulativeGasUsed: 112584,
  gasUsed: 112584,
  logs: [],
  transactionHash: "0xca564a1a9890296893abe16ee8a3dcee9166f7a91aed5e0ab3cb182fad57288d",
  transactionIndex: 0
}

/*************************** Testing low gas sent. Transaction fails without any error being obvious

> incrementer3.increment.sendTransaction(13,19, {from:eth.coinbase,gas:25000});
"0x3127dfb39dd5ef22bcdaadcf90fb7a5f7b1c16cf632d642624f2c99643dfb252"
> var r = web3.eth.getTransactionReceipt('0x3127dfb39dd5ef22bcdaadcf90fb7a5f7b1c16cf632d642624f2c99643dfb252');
undefined
> r
{
  blockHash: "0x2fd44040c30bcb9b4853afe90f7604740dcf4d7439205a7bc7f9e7c4a12bd052",
  blockNumber: 179703,
  contractAddress: null,
  cumulativeGasUsed: 25000,
  gasUsed: 25000,				// all gas used, but it wasn't enough
  logs: [],
  transactionHash: "0x3127dfb39dd5ef22bcdaadcf90fb7a5f7b1c16cf632d642624f2c99643dfb252",
  transactionIndex: 0
}
> {nsole.log(e, contract);endTransaction(13,19, {from:eth.coinbase,gas:25000});
    console.log('Contract mined! address: ' + contract.address + ' transactionHash: ' + contract.transactionHash);
> incrementer3.getWhatHappened();
"constructor executed"
> incrementer3.getIteration();
0


*/