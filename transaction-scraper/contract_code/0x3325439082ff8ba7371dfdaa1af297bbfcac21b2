//[ETH] Wealth Redistribution Contract
//
//Please keep in mind this contract is for educational and entertainment purposes only and was created to understand the limitations of Ethereum contracts.
//

contract WealthRedistributionProject {

  struct BenefactorArray {
      address etherAddress;
      uint amount;
  }

  BenefactorArray[] public benefactor;

  uint public balance = 0;
  uint public totalBalance = 0;

  function() {
    enter();
  }
  
  function enter() {
    if (msg.value != 1 ether) { //return payment if it&#39;s not 1 ETH
        msg.sender.send(msg.value);
        return;
    }
   
    uint transactionAmount;
    uint k = 0;

    // add a new participant to array
    uint total_inv = benefactor.length;
    benefactor.length += 1;
    benefactor[total_inv].etherAddress = msg.sender;
    benefactor[total_inv].amount = msg.value;

	balance += msg.value;  //keep track of amount available

   // payment gets distributed to all benefactors based on what % of the total was contributed by them    
    while (k&lt;total_inv) 
    { 
    	transactionAmount = msg.value * benefactor[k].amount / totalBalance;       //Calculate amount to send
		benefactor[k].etherAddress.send(transactionAmount);    					//Wealth redistribution
		balance -= transactionAmount;                        					//Keep track of available balance
        k += 1; //LOOP next benefactor
    }
    
	totalBalance += msg.value;  //keep track of total amount contributed
    
    
  }

}