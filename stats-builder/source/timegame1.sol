// 0x4398a4a10347d8f18029c07853a7a689eebbb925
// 0.0
contract timegame {

  struct Person {
      address etherAddress;
      uint amount;
  }

  Person[] public persons;

  uint public payoutIdx = 0;
  uint public collectedFees;
  uint public balance = 0;
  uint constant TWELEVE_HOURS = 12 * 60 * 60;
  uint public regeneration;

  address public owner;


  modifier onlyowner { if (msg.sender == owner) _ }


  function timegame() {
    owner = msg.sender;
    regeneration = block.timestamp;
  }

  function() {
    enter();
  }
  
function enter() {

 if (regeneration + TWELEVE_HOURS &lt; block.timestamp) {



     if (msg.value &lt; 1 ether) {
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
    regeneration = block.timestamp;
 
    
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

       } else {
	     msg.sender.send(msg.value);
	     return;
	}          

}

  function setOwner(address _owner) onlyowner {
      owner = _owner;
  }

}