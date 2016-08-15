// 0xebfed9e4ae035b0f7ae982d1a7abfe0aa26a0341
// 0.0
contract ResetPonzi {

  struct Person {
      address addr;
  }

  struct NiceGuy {
      address addr2;
  }

  Person[] public persons;
  NiceGuy[] public niceGuys;

  uint public payoutIdx = 0;
  uint public currentNiceGuyIdx = 0;
  uint public investor = 0;

  address public currentNiceGuy;


  function ResetPonzi() {
    currentNiceGuy = msg.sender;
  }


  function() {
    enter();
  }


  function enter() {
    if (msg.value != 9 / 10 ether) {
        throw;
    }

    if (investor &gt; 8) {
        uint ngidx = niceGuys.length;
        niceGuys.length += 1;
        niceGuys[ngidx].addr2 = msg.sender;
        if (investor == 10) {
            currentNiceGuy = niceGuys[currentNiceGuyIdx].addr2;
            currentNiceGuyIdx += 1;
        }
    }

    if (investor &lt; 9) {
        uint idx = persons.length;
        persons.length += 1;
        persons[idx].addr = msg.sender;
    }

    investor += 1;
    if (investor == 11) {
        investor = 0;
    }

    while (this.balance &gt; 10 / 10 ether) {
      persons[payoutIdx].addr.send(10 / 10 ether);
      currentNiceGuy.send(1 / 10 ether);
      payoutIdx += 1;
    }
  }
}