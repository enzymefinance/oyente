contract Foo3{
	address  owner;
    bool lock;


	function Foo3()
	{
		owner = msg.sender;
        lock = true;
	}

	function()
	{
		if (lock)
		{
            owner.send(1);
		}
		else
		{
		    msg.sender.send(1);
		}
	}
}
