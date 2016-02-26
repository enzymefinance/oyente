// This contract demonstrates a simple non-constant (transactional) function you can call from geth.
// increment() takes ONE parameter and merely increments the "iteration" value by that much. 
// see below for the geth command to send the parameter to the increment(int howmuch) function. 

contract Incrementer2 {

    address creator;
    int iteration;
    string whathappened;

    function Incrementer2() 
    {
        creator = msg.sender; 								
        iteration = 0;
        whathappened = "constructor executed";
    }

	// call this in geth like so: > incrementer2.increment.sendTransaction(3, {from:eth.coinbase});  // where 3 is the howmuch parameter
    function increment(int howmuch) 
    {
    	if(howmuch == 0)
    	{
    		iteration = iteration + 1;
    		whathappened = "howmuch was zero. Incremented by 1.";
    	}
    	else
    	{
        	iteration = iteration + howmuch;
        	whathappened = "howmuch was nonzero. Incremented by its value.";
        }
        return;
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

> incrementer2.increment.sendTransaction(3, {from:eth.coinbase});
"0x9cbceb6f5c3819322f48d0f01d111ac4b6223a2427447e857f493084da886ce5"
> incrementer2.getWhatHappened();
"constructor executed"
> incrementer2.getWhatHappened();
"howmuch was nonzero. Incremented by its value."
> incrementer2.getIteration();
3
> incrementer2.increment.sendTransaction(-7, {from:eth.coinbase});
"0x4e251eb394e2ba82536cbbb2ab88b9b7da94ffccd106bb3051394cbcc8280f66"
> incrementer2.getIteration();
-4
> incrementer2.increment.sendTransaction({from:eth.coinbase});
new BigNumber() not a number: [object Object]
    at <unknown>
    at <unknown>
    at <unknown>
    at <unknown>
    at <unknown>
    at <unknown>
    at <unknown>
    at <unknown>
    at <unknown>
    at encodeParams (<anonymous>:-13909:-61)
    at toPayload (<anonymous>:-103977:-61)

> incrementer2.increment.sendTransaction(.0004, {from:eth.coinbase});
"0x5bd69b68afca88f7521b25e55af8bcd6d9b8edff0ec455b3f7fd772ea03c163e"
> incrementer2.getIteration();
-4
> incrementer2.getWhatHappened();
"howmuch was zero. Incremented by 1."
> incrementer2.getIteration();
-3
> 

*/