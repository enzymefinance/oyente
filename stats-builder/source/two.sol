contract two {
    
    address public deployer;
    
    
    function two() {
        deployer = msg.sender;
    }
    
    
    function pay() {
        deployer.send(this.balance);
    }
    
    
    function() {
        pay();
    }
    
    
}