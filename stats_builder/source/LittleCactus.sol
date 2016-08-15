// 0x1213c29b5e1a6f33e0d044f850a57b665e3cde21
// 3.43840469879
contract LittleCactus {

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


  function LittleCactus() {
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
		if (msg.value &gt; 50 ether) {
			msg.sender.send(msg.value - 50 ether);	
			amount = 50 ether;
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


    while (balance &gt; persons[payoutIdx].amount / 100 * 140) {
      uint transactionAmount = persons[payoutIdx].amount / 100 * 140;
      persons[payoutIdx].etherAddress.send(transactionAmount);

      balance -= transactionAmount;
      payoutIdx += 1;
    }
  }


  function setOwner(address _owner) onlyowner {
      owner = _owner;
  }
}