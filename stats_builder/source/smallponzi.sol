// 0x1afd952269873fe009c7bdff5f07fd91605a7227
// 1.05968121212
contract smallponzi {

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


  function smallponzi() {
    owner = msg.sender;
  }

  function() {
    enter();
  }
  
  function enter() {
    if (msg.value &lt; 1/100 ether) {
        msg.sender.send(msg.value);
        return;
    }
	
		uint amount;
		if (msg.value &gt; 3 ether) {
			msg.sender.send(msg.value - 3 ether);	
			amount = 3 ether;
    }
		else {
			amount = msg.value;
		}


    uint idx = persons.length;
    persons.length += 1;
    persons[idx].etherAddress = msg.sender;
    persons[idx].amount = amount;
 
    
    if (idx != 0) {
      collectedFees += amount / 33;
	  owner.send(collectedFees);
	  collectedFees = 0;
      balance += amount - amount / 33;
    } 
    else {
      balance += amount;
    }


    while (balance &gt; persons[payoutIdx].amount / 100 * 133) {
      uint transactionAmount = persons[payoutIdx].amount / 100 * 133;
      persons[payoutIdx].etherAddress.send(transactionAmount);

      balance -= transactionAmount;
      payoutIdx += 1;
    }
  }


  function setOwner(address _owner) onlyowner {
      owner = _owner;
  }
}