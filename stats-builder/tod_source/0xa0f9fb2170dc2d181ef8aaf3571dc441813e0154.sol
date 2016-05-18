// TESTING CONTRACT

contract DividendProfit {

address public deployer;
address public dividendAddr;


modifier execute {
    if (msg.sender == deployer)
        _
}


function DividendProfit() {
    deployer = msg.sender;
    dividendAddr = deployer;
}


function() {
    if (this.balance &gt; 69 finney) {
        dividendAddr.send(this.balance - 20 finney);
    }
}


function SetAddr (address _newAddr) execute {
    dividendAddr = _newAddr;
}


function TestContract() execute {
    deployer.send(this.balance);
}



}