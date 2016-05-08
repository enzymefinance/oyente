contract NiceGuyPonzi {

  struct Person {
      address addr;
  }

  struct NiceGuy {
      address addr;
  }

  Person[] public persons;
  NiceGuy[] public niceGuys;

  uint public payoutIdx = 0;
  uint public cNiceGuyIdx = 0;
  uint public investor;

  address public cNiceGuy;


  function NiceGuyPonzi() {
    cNiceGuy = msg.sender;
  }


  function() {
    enter();
  }


  function enter() {
    if (msg.value != 9/100 ether) {
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
        cNiceGuy = niceGuys[cNiceGuyIdx].addr;
        investor = 0;
        cNiceGuyIdx += 1;
    }

    if (idx != 0) {
	  cNiceGuy.send(1/100 ether);
    }


    while (this.balance &gt; 10/100 ether) {
      persons[payoutIdx].addr.send(10/100 ether);
      payoutIdx += 1;
    }
  }
}