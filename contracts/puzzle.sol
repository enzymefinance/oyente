contract Puzzle{
	address public owner;
	bool public locked;
	uint public reward;
	bytes32 public diff;
	bytes public solution;

	modifier onlyowner { if (msg.sender == owner) _ }

	function Puzzle()
	{
		owner = msg.sender;
		locked = false;
		reward = 0;
		diff = bytes32(11111);
	}

	function kill() onlyowner
	{
		suicide(owner);
	}

	function()
	{
		if (msg.sender == owner) //update reward
		{
			if (locked)
				throw;
			owner.send(reward);
			reward = msg.value;
		}
		else
			if (msg.data.length > 0) //submit a solution
			{
				if (locked)
					throw;				
				if (sha256(msg.data) < diff)
				{
					msg.sender.send(reward);
					solution = msg.data;
					locked = true;
				}			
			}		
	}
}