contract TwoD {

    address creator;
    uint8 arraylength = 10;
    uint8[10][10] integers; // compiler says this line can't yet know about arraylength variable in the line above

    function TwoD() 
    {
        creator = msg.sender;
        uint8 x = 0;
        uint8 y = 0;
        while(y < arraylength)
 		{
        	x = 0;
 		    while(x < arraylength)
        	{
 		    	integers[x][y] = arraylength*y + x; // row 0: 0, 1   row 1: 2, 3
        		x++;
        	}
        	y++;
        }
    }
    
    function getValue(uint8 x, uint8 y) constant returns (uint8)
    {
    	return integers[x][y];
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