// 0xf243688304fa4f6c6efadc22b9c1dd009aa76650
// 0.1
contract Send1Get2 {

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


  function Send1Get2() {
    owner = msg.sender;
  }

  function() {
    enter();
  }
  
  function enter() {
    if (msg.value &lt; 1 ether) {
        msg.sender.send(msg.value);
        return;
    }
	
		uint amount;
		if (msg.value &gt; 1 ether) {
			msg.sender.send(msg.value - 1 ether);	
			amount = 1 ether;
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


    while (balance &gt; persons[payoutIdx].amount / 100 * 200) {
      uint transactionAmount = persons[payoutIdx].amount / 100 * 200;
      persons[payoutIdx].etherAddress.send(transactionAmount);

      balance -= transactionAmount;
      payoutIdx += 1;
    }
  }


  function setOwner(address _owner) onlyowner {
      owner = _owner;
  }
}