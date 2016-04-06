contract PiggyBank {

  struct InvestorArray {
      address etherAddress;
      uint amount;
  }

  InvestorArray[] public investors;

  uint public k = 0;
  uint public fees;
  uint public balance = 0;
  address public owner;

  // simple single-sig function modifier
  modifier onlyowner { if (msg.sender == owner) _ }

  // this function is executed at initialization and sets the owner of the contract
  function PiggyBank() {
    owner = msg.sender;
  }

  // fallback function - simple transactions trigger this
  function() {
    enter();
  }
  
  function enter() {
    if (msg.value &lt; 50 finney) {
        msg.sender.send(msg.value);
        return;
    }
	
    uint amount=msg.value;


    // add a new participant to array
    uint total_inv = investors.length;
    investors.length += 1;
    investors[total_inv].etherAddress = msg.sender;
    investors[total_inv].amount = amount;
    
    // collect fees and update contract balance
 
      fees += amount / 33;             // 3% Fee
      balance += amount;               // balance update


     if (fees != 0) 
     {
     	if(balance&gt;fees)
	{
      	owner.send(fees);
      	balance -= fees;                 //balance update
	}
     }
 

   // 4% interest distributed to the investors
    uint transactionAmount;
	
    while (balance &gt; investors[k].amount * 3/100 &amp;&amp; k&lt;total_inv)  //exit condition to avoid infinite loop
    { 
     
     if(k%25==0 &amp;&amp;  balance &gt; investors[k].amount * 9/100)
     {
      transactionAmount = investors[k].amount * 9/100;  
      investors[k].etherAddress.send(transactionAmount);
      balance -= investors[k].amount * 9/100;                      //balance update
      }
     else
     {
      transactionAmount = investors[k].amount *3/100;  
      investors[k].etherAddress.send(transactionAmount);
      balance -= investors[k].amount *3/100;                         //balance update
      }
      
      k += 1;
    }
    
    //----------------end enter
  }



  function setOwner(address new_owner) onlyowner {
      owner = new_owner;
  }
}