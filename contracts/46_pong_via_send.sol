/***
 *     _    _  ___  ______ _   _ _____ _   _ _____ 
 *    | |  | |/ _ \ | ___ \ \ | |_   _| \ | |  __ \
 *    | |  | / /_\ \| |_/ /  \| | | | |  \| | |  \/
 *    | |/\| |  _  ||    /| . ` | | | | . ` | | __ 
 *    \  /\  / | | || |\ \| |\  |_| |_| |\  | |_\ \
 *     \/  \/\_| |_/\_| \_\_| \_/\___/\_| \_/\____/
 *                                                 
 *   This contract DOES NOT WORK at the moment. 9/22/2015                                     
 */

// 1. Deploy Pong .
// 2. Deploy Ping, giving it the address of Pong.
// 3. Call Ping.touchPong() using a <pongaddress>.send()
// 4. ... which does... something ...

contract Pong {

    address creator;
    int8 constructortouches = 0;
    int8 namelesstouches = 0;
    
	/*********
 	 Step 1: Deploy Pong
 	 *********/
    function Pong() 
    {
        creator = msg.sender; 
        constructortouches = constructortouches + 1;
    }
	
	/*********
	 Step 4. Accept generic transaction (send(), hopefully)
	 *********/	
	function () 
	{
    	namelesstouches = namelesstouches + 1;
    	return;
    }
    
// ----------------------------------------------------------------------------------------------------------------------------------------
    	
	function getBalance() public constant returns (uint)
	{
		return this.balance;
	}
	
    /*********
	 touches getters
	 *********/
	function getConstructorTouches() public constant returns (int8)
    {
    	return constructortouches;
    } 
	
	function getNamelessTouches() public constant returns (int8)
	{
		return namelesstouches;
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
