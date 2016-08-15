// 0xe941e5d4a66123dc74886699544fbbb942f1887a
// 0.042
contract SimpleCoinFlipGame {
    event FlippedCoin(address msgSender, uint msgValue, int coinsFlipped);
    
    int public coinsFlipped = 422;
    int public won = 253;
    int public lost = 169;
    address private owner = msg.sender;
    // uint public lastMsgValue;
    // uint public lastMsgGas;
    // uint public lastRandomNumber;

    function flipTheCoinAndWin() {
        var randomNumber = (uint(sha3(msg.gas)) + uint(coinsFlipped)) % 10;
        
        // lastMsgValue = msg.value;
        // lastMsgGas = msg.gas;
        // lastRandomNumber = randomNumber; 
        
        FlippedCoin(msg.sender, msg.value, coinsFlipped++);
        
        // wager of &gt; 42 Finey is not accepted
        if(msg.value &gt; 42000000000000000){
            msg.sender.send(msg.value - 100000);
            won++;
            return;   
        }
        
        if(randomNumber &lt; 4) {
            msg.sender.send(2 * (msg.value - 100000));
            won++;
            return;
        } 
        lost++;
    } 
    
    function terminate() onlyByOwner { 
            suicide(owner); 
    }
    
    modifier onlyByOwner() {
        if (msg.sender != owner)
            throw;
        _
    }
}