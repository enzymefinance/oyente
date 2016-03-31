contract Foo2{
	address  owner;
    bool lock;


	function Foo2()
	{
		owner = msg.sender;
        lock = true;
	}

	function()
	{
		if (lock)
		{
            lock = false;
            owner.send(1);
		}
		else
		{
		    lock = true;
		    msg.sender.send(1);
		}
	}
}
