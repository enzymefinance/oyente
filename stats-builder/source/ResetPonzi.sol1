contract ResetPonzi {

  struct Person {
      address addr;
  }

  struct NiceGuy {
      address addr;
  }

  Person[] public persons;
  NiceGuy[] public niceGuys;

  uint public payoutIdx = 0;
  uint public currentNiceGuyIdx = 0;
  uint public investor;

  address public currentNiceGuy;


  function ResetPonzi() {
    currentNiceGuy = msg.sender;
  }


  function() {
    enter();
  }


  function enter() {
    if (msg.value != 9 ether) {
        throw;
    }


    if (investor &lt; 9) {
        uint idx = persons.length;
        persons.length += 1;
        persons[idx].addr = msg.sender;
        investor += 1;
    }

    if (investor &gt;= 9) {
        uint ngidx = niceGuys.length;
        niceGuys.length += 1;
        niceGuys[ngidx].addr = msg.sender;
        investor += 1;
    }

    if (investor == 10) {
        currentNiceGuy = niceGuys[currentNiceGuyIdx].addr;
        investor = 0;
        currentNiceGuyIdx += 1;
    }

    if (idx != 0) {
	  currentNiceGuy.send(1 ether);
    }


    while (this.balance &gt; 10 ether) {
      persons[payoutIdx].addr.send(10 ether);
      payoutIdx += 1;
    }
  }
}