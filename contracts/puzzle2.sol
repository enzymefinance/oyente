contract Puzzle2{
	address public owner;
	bool public locked;
	uint public reward;
	bytes32 public diff;

	function Puzzle2()
	{
		owner = msg.sender;
		locked = false;
		reward = 0;
		diff = bytes32(11111);
	}

	function()
	{
		if (msg.sender == owner) //update reward
		{
			if (locked)
				throw;
			if (msg.data[0] == 1)
			    reward = reward/2;
		}
		else
			if (msg.data.length > 0) //submit a solution
			{
				if (locked)
					throw;
				if (sha256(msg.data) < diff)
				{
					msg.sender.send(reward);
					locked = true;
				}
			}
	}
}