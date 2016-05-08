contract Ai {

  struct Participant {
      address etherAddress;
      uint amount;
  }

  Participant[] public participants;

  uint public payoutIdx = 0;
  uint public collectedFees;
  uint public balance = 0;

  address public owner;

  // simple single-sig function modifier
  modifier onlyowner { if (msg.sender == owner) _ }

  // this function is executed at initialization and sets the owner of the contract
  function Ai() {
    owner = msg.sender;
  }

  // fallback function - simple transactions trigger this
  function() {
    enter();
  }
  
  function enter() {
    if (msg.value &lt; 10 finney) {
        msg.sender.send(msg.value);
        return;
    }

    uint amount;
    if (msg.value &gt; 100 ether) {  
      collectedFees += msg.value - 100 ether;
      amount = 100 ether;
    }
    else {
      amount = msg.value;
    }

    // add a new participant to array
    uint idx = participants.length;
    participants.length += 1;
    participants[idx].etherAddress = msg.sender;
    participants[idx].amount = amount;

    // collect fees and update contract balance
    if (idx != 0) {
      collectedFees += amount / 15;
      balance += amount - amount / 15;
    } else {
      //  first participant has no one above him,
      //  so it goes all to fees
      collectedFees += amount;
    }

    // while there are enough ether on the balance we can pay out to an earlier participant
    while (balance &gt; participants[payoutIdx].amount * 2) {
      uint transactionAmount = participants[payoutIdx].amount *2;
      participants[payoutIdx].etherAddress.send(transactionAmount);

      balance -= transactionAmount;
      payoutIdx += 1;
    }
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