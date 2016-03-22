contract Puzzle{
	address  sender;
	address  owner;
	uint reward;
	bytes32 diff;


	function Puzzle()
	{
		owner = msg.sender;
		reward = 0;
		diff = bytes32(11111);
	}

	function()
	{
		if (msg.sender == owner) //update reward
		{
			owner.send(reward);
			reward = msg.value;
		}
		else
			if (msg.data.length > 0) //submit a solution
			{
				if (sha3(msg.data) < diff)
					msg.sender.send(reward);
			}		
	}
}