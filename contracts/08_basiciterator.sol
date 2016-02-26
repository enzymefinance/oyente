/*
	This is a very simple demonstration of a while loops. Same as JS/c.
*/

contract BasicIterator {

    address creator;
    uint8[10] integers;

    function BasicIterator() 
    {
        creator = msg.sender;
        uint8 x = 0;
        while(x < integers.length)
        {
        	integers[x] = x;
        	x++;
        }
    }
    
    function getSum() constant returns (uint)
    {
    	uint8 sum = 0;
    	uint8 x = 0;
    	while(x < integers.length)
        {
        	sum = sum + integers[x];
        	x++;
        }
    	return sum;
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