// 0x6a92b2804eaef97f222d003c94f683333e330693
// 0.0
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