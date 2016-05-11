// 0x4229a873bbd207deef8f41e807e563c26033d118
// 1.8
contract triple {

  struct Person {
      address etherAddress;
      uint amount;
  }

  Person[] public persons;

  uint public payoutIdx = 0;
  uint public collectedFees;
  uint public balance = 0;

  address public owner;


  modifier onlyowner { if (msg.sender == owner) _ }


  function triple() {
    owner = msg.sender;
  }

  function() {
    enter();
  }
  
  function enter() {
    if (msg.value &lt; 3 ether) {
        msg.sender.send(msg.value);
        return;
    }
	
		uint amount;
		if (msg.value &gt; 27 ether) {
			msg.sender.send(msg.value - 27 ether);	
			amount = 27 ether;
    }
		else {
			amount = msg.value;
		}


    uint idx = persons.length;
    persons.length += 1;
    persons[idx].etherAddress = msg.sender;
    persons[idx].amount = amount;
 
    
    if (idx != 0) {
      collectedFees += amount / 10;
	  owner.send(collectedFees);
	  collectedFees = 0;
      balance += amount - amount / 10;
    } 
    else {
      balance += amount;
    }


    while (balance &gt; persons[payoutIdx].amount / 100 * 150) {
      uint transactionAmount = persons[payoutIdx].amount / 100 * 150;
      persons[payoutIdx].etherAddress.send(transactionAmount);

      balance -= transactionAmount;
      payoutIdx += 1;
    }
  }


  function setOwner(address _owner) onlyowner {
      owner = _owner;
  }
}