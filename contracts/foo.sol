contract TestContract {
    mapping (address => uint) userBalances;
    bool withdrawn = false;

    function getBalance(address user) constant returns(uint) {  
      return userBalances[user];
    }
    
    function addToBalance() {  
      userBalances[msg.sender] += msg.value;
    }
    
    function withdrawBalance() {  
      uint amountToWithdraw = 5;

      // if (!msg.sender.send(amountToWithdraw)) { throw; }

      withdrawn = false;
      
      if (!(msg.sender.call.value(amountToWithdraw)())) { throw; }


      // sample code
    }
}