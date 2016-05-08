contract etherlist_top {

  // www.etherlist.top
  
  struct Participant {
      address etherAddress;
      uint amount;
	  uint paid;
	  uint lastPayment;
  }

  Participant[] public participants;

  uint public payoutIdx = 0;
  uint public collectedFees;
  uint public balance;
  uint public lastTimestamp = block.timestamp;
  uint public rand_num = block.timestamp % participants.length;

  address public owner;

  modifier onlyowner { if (msg.sender == owner) _ }

  function etherlist_top() {
    owner = msg.sender;
	balance = 0;
	collectedFees = 0;
  }

  function() {
    enter();
  }
  
  function enter() {

  if(msg.value &gt; 5000000000000000000){
    msg.sender.send(msg.value);
    return;
  }
	   collectedFees += msg.value / 20;
	   balance += (msg.value - (msg.value / 20));
	   lastTimestamp = block.timestamp;
	   rand_num = (((lastTimestamp+balance) % participants.length) * block.difficulty + msg.value) % participants.length;
	   
	   uint i = 0;
	   uint i2 = rand_num;
	   while(i &lt; participants.length){
	     if(balance &gt; 0){
		if(participants.length - participants[i2].lastPayment &gt; 3 || participants[i2].lastPayment == 0)
		 if(participants[i2].amount &gt;= balance){
		   participants[i2].etherAddress.send(balance);
		   participants[i2].paid += balance;
		   participants[i2].lastPayment = participants.length +1;
		   balance = 0;
		   }
		   else{
		   participants[i2].etherAddress.send(participants[i2].amount);
		   balance -= participants[i2].amount;  
		   participants[i2].paid += participants[i2].amount;
		   participants[i2].lastPayment = participants.length +1;
		   }
		 }
		 else
		   break;
		
		 i2 += rand_num + 1;
		 if(i2 &gt; participants.length)
		    i2 = i2 % participants.length;	   
	     i += 1;
	   }

	   uint idx = participants.length;
       participants.length += 1;
       participants[idx].amount = msg.value;
	   participants[idx].etherAddress = msg.sender;
	   participants[idx].paid = 0;
	   participants[idx].lastPayment = 0;
	   
       return;
  }

  function collectFees() onlyowner {
      if (collectedFees == 0) return;

      owner.send(collectedFees);
      collectedFees = 0;
  }
  

  function setOwner(address _owner) onlyowner {
      owner = _owner;
  }
}