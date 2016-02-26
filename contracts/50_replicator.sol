
contract ReplicatorB {

    address creator;
    uint blockCreatedOn;

    function Replicator() 
    {
        creator = msg.sender;
       // next = new ReplicatorA();    // Replicator B can't instantiate A because it doesn't yet know about A
       								   // At the time of this writing (Sept 2015), It's impossible to create cyclical relationships
       								   // either with self-replicating contracts or A-B-A-B 
        blockCreatedOn = block.number;
    }
	
	function getBlockCreatedOn() constant returns (uint)
	{
		return blockCreatedOn;
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

contract ReplicatorA {

    address creator;
	address baddress;
	uint blockCreatedOn;

    function Replicator() 
    {
        creator = msg.sender;
        baddress = new ReplicatorB();		 // This works just fine because A already knows about B
        blockCreatedOn = block.number;
    }

	function getBAddress() constant returns (address)
	{
		return baddress;
	}
	
	function getBlockCreatedOn() constant returns (uint)
	{
		return blockCreatedOn;
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
