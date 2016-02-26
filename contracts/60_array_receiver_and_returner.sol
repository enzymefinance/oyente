contract ArrayRR {

    address creator;
    uint8 arraylength = 10;
    uint8[10] integers; // NOTE 1 see below
    int8 setarraysuccessful = -1; // 1 success, 0 fail, -1 not yet tried

    function ArrayRR() 
    {
        creator = msg.sender;
        uint8 x = 0;
        while(x < integers.length)
        {
        	integers[x] = 1; // initialize array to all zeros
        	x++;
        }
    }
    
    function setArray(uint8[10] incoming)  // NOTE 2 see below. Also, use enough gas.
    {
    	setarraysuccessful = 0;
    	uint8 x = 0;
        while(x < arraylength)
        {
        	integers[x] = incoming[x]; // initialize array to all zeros
        	x++;
        }
        setarraysuccessful = 1;
    	return;
    }
    
    function getArraySettingResult() constant returns (int8)
    {
    	return setarraysuccessful;
    }
    
    function getArray() constant returns (uint8[10])  // NOTE 3 see below
    {
    	return integers;
    }
    
    function getValue(uint8 x) constant returns (uint8)
    {
    	return integers[x];
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

// NOTES 1, 2, 3
// because "integers" is declared as uint8[10], getArray() must return type uint8[10].
// setArray(...) does not require uint8[10] input, but you'd then have to check to make sure the two arrays were of the same type and length.

// If "integers" were declared as uint8[] (dynamic length), then I'd have used getArray() and setArray() with uint8[] instead. 
// setArray would then obviously require a length check for compatibility.

/*

> arrayrr.getValue(3);
1
> arrayrr.setArray.sendTransaction([0,1,2,3,4,5,6,7,8,9], {from:eth.coinbase});
"0xe54bf5d62f6b45f8761d5bcdd7d919bf1b51eade0ed5dc43bea828f927731fdb"
> arrayrr.getArraySettingResult();
-1
> arrayrr.getArraySettingResult();
-1
> arrayrr.setArray.sendTransaction([0,1,2,3,4,5,6,7,8,9], {from:eth.coinbase,gas:1000000});
"0x3e0bbb151e10a316fbc201ca4e78ebd4c1f6bc827f83d72cff39e5dfb0aba18d"
> arrayrr.getArraySettingResult();
1
> arrayrr.getArray();
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

*/