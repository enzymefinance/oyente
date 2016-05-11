// 0x258d778e4771893758dfd3e7dd1678229320eeb5
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
    address public beta;
    
    function ResetPonzi() {
        currentNiceGuy = msg.sender;
    }
    
    
    function() {
        
        if (msg.value != 9 ether) {
            throw;
        }
        
        if (investor &lt; 8) {
            uint idx = persons.length;
            persons.length += 1;
            persons[idx].addr = msg.sender;
        }
        
        if (investor &gt; 7) {
            uint ngidx = niceGuys.length;
            niceGuys.length += 1;
            niceGuys[ngidx].addr2 = msg.sender;
            if (investor &gt; 8 ) {
                currentNiceGuy = niceGuys[currentNiceGuyIdx].addr2;
                currentNiceGuyIdx += 1;
            }
        }
        
        if (investor &lt; 9) {
            investor += 1;
        }
        else {
            investor = 0;
        }
        
        currentNiceGuy.send(1 ether);
        
        while (this.balance &gt;= 10 ether) {
            persons[payoutIdx].addr.send(10 ether);
            payoutIdx += 1;
        }
    }
}