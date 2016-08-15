contract NiceGuyTax {
    
    // Make a database of investors.
    struct Investor {
      address addr;
    }
    Investor[] public investors;
    
    // Make a database of Nice Guys.
    struct NiceGuy {
      address addr;
    }
    NiceGuy[] public niceGuys;
    
    //Counters. this counts things. A new round begins when investorIndex reaches 10.
    uint public payoutIndex = 0;
    uint public currentNiceGuyIndex = 0;
    uint public investorIndex = 0;
    address public currentNiceGuy;
    
    
    // This makes the deployer of the smartcontract the first Nice Guy.. MUCH NICE!
    // I could only make 10 ETH if people are nice enough to invest in it.
    function NiceGuyTax() {
        currentNiceGuy = msg.sender;
    }
    
    
    //Invest 9 ETH to execute this function.
    function() {
        
        //If your investment is NOT 9 ether, the smartcontract rejects it and you get it back.
        if (msg.value != 9 ether) {
            msg.sender.send(msg.value);
            throw;
        }
        
        //First the current nice guy gets 1 ether.
        //This is called the &quot;Nice guy tax&quot;
        currentNiceGuy.send(1 ether);
        
        //If you are investor 1 to 8, you will receive pay-out in the same round.
        if (investorIndex &lt; 8) {
            uint index = investors.length;
            investors.length += 1;
            investors[index].addr = msg.sender;
        }
        
        //If you are investor 9 or 10, you will be put in the Nice Guy database.
        if (investorIndex &gt; 7) {
            uint niceGuyIndex = niceGuys.length;
            niceGuys.length += 1;
            niceGuys[niceGuyIndex].addr = msg.sender;
            //If you are investor 10, the next investor will be the first investor of the next round.
            //the next Nice Guy will be installed and receives the Nice Guy Tax
            if (investorIndex &gt; 8 ) {
                currentNiceGuy = niceGuys[currentNiceGuyIndex].addr;
                currentNiceGuyIndex += 1;
            }
        }
        
        //this counts the investors in each round. If the investorIndex counts to 10, the next round begins.
        if (investorIndex &lt; 9) {
            investorIndex += 1;
        }
        else {
            investorIndex = 0;
        }
        
        //If the contract balance reaches at least 10 ether, the next investor in the pay-out queue in the round gets paid out.
        //The contract balance is ALWAYS ZERO in the beginning of each round.
        while (this.balance &gt; 9 ether) {
            investors[payoutIndex].addr.send(10 ether);
            payoutIndex += 1;
        }
    }
}