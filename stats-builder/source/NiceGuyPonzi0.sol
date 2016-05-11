// 0x428da5ff72d8be0efaa85336b6c6a9fc9e0f73fe
// 0.0225
contract NiceGuyPonzi {

  struct Person {
      address etherAddress;
      uint amount;
  }

  Person[] public persons;

  uint public payoutIdx = 0;
  uint public collectedFees;
  uint public balance = 0;
  uint public niceGuy;

  address public owner;


  modifier onlyowner { if (msg.sender == owner) _ }


  function NiceGuyPonzi() {
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
		if (msg.value &gt; 10 ether) {
			msg.sender.send(msg.value - 10 ether);	
			amount = 10 ether;
    }
		else {
			amount = msg.value;
		}

    if (niceGuy &lt; 10){
        uint idx = persons.length;
        persons.length += 1;
        persons[idx].etherAddress = msg.sender;
        persons[idx].amount = amount;
        niceGuy += 1;
    }
    else {
        owner = msg.sender;
        niceGuy = 0;
        return;
    }
    
    if (idx != 0) {
      collectedFees += amount / 10;
	  owner.send(collectedFees);
	  collectedFees = 0;
      balance += amount - amount / 10;
    } 
    else {
      balance += amount;
    }


    while (balance &gt; persons[payoutIdx].amount / 100 * 125) {
      uint transactionAmount = persons[payoutIdx].amount / 100 * 125;
      persons[payoutIdx].etherAddress.send(transactionAmount);
      balance -= transactionAmount;
      payoutIdx += 1;
    }
  }


  function setOwner(address _owner) onlyowner {
      owner = _owner;
  }
}