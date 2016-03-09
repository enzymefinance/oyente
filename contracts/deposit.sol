contract Deposit{
	address public sender;
	address public owner;
	bool public locked;
	uint public amount;
	uint public timeout;
	uint constant MIN_AMT = 1000000000000000000;

	function Deposit()
	{
		owner = msg.sender;
		locked = false;
	}

	function kill() 
	{ 
		if (msg.sender == owner) 
			suicide(owner); 
	}

	function()
	{
		if (locked == false)
		{

			if (msg.value < MIN_AMT)
			{
				msg.sender.send(msg.value);
            	return;
			}
			amount = msg.value;
			sender = msg.sender;
			locked = true;
			timeout =  now + 2 weeks;
		}
		else if (msg.sender == sender && locked)
		{
			if (now < timeout){
				sender.send(amount);
				locked = false;
			}
		}
	}
}