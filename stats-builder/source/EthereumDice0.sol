// 0x566c1023aaf10180b4eb9533050fbf91d7792af1
// 0.0
//***********************************Ether Dice Game
//
//
//  Hello player, this is a Ethereum based dice game. You must deposit minimum of &quot;MinDeposit&quot; to play (+transaction cost), if you send less it wont be counted. 
//  You have a 25% chance of winning the entire balance, whatever that amount is.  On average that means that 3 players will deposit before you will win the balance.
//  Also every 40th player will win the jackpot, so make sure you are that person. The jackpot will be considerably more than the balance, so you have the chance to win big if you deposit fast! The fee and deposit rate can be changed by the owner, and it&#39;s publicly visible, after the dice has a big volume, the fee will be lowered!
//  
//  Good Luck and Have Fun!
//
//***********************************START
contract EthereumDice {

  struct gamblerarray {
      address etherAddress;
      uint amount;
  }

//********************************************PUBLIC VARIABLES
  
  gamblerarray[] public gamblerlist;
  uint public Gamblers_Until_Jackpot=0;
  uint public Total_Gamblers=0;
  uint public FeeRate=7;
  uint public Bankroll = 0;
  uint public Jackpot = 0;
  uint public Total_Deposits=0;
  uint public Total_Payouts=0;
  uint public MinDeposit=1 ether;

  address public owner;
  uint Fees=0;
  // simple single-sig function modifier
  modifier onlyowner { if (msg.sender == owner) _ }

//********************************************INIT

  function EthereumDice() {
    owner = msg.sender;
  }

//********************************************TRIGGER

  function() {
    enter();
  }
  
//********************************************ENTER

  function enter() {
    if (msg.value &gt;= MinDeposit) {

    uint amount=msg.value;
    uint payout;


    // add a new participant to the system and calculate total players
    uint list_length = gamblerlist.length;
    Total_Gamblers=list_length+1;
    Gamblers_Until_Jackpot=40-(Total_Gamblers % 40);
    gamblerlist.length += 1;
    gamblerlist[list_length].etherAddress = msg.sender;
    gamblerlist[list_length].amount = amount;



    // set payout variables
     Total_Deposits+=amount;       	//update deposited amount
	    
      Fees   =amount * FeeRate/100;    // 7% fee to the owner
      amount-=amount * FeeRate/100;
	    
      Bankroll += amount*80/100;     // 80% to the balance
      amount-=amount*80/100;  
	    
      Jackpot += amount;               	//remaining to the jackpot


    // payout Fees to the owner
     if (Fees != 0) 
     {
      	owner.send(Fees);		//send fee to owner
	Total_Payouts+=Fees;        //update paid out amount
     }
 

   //payout to participants	
     if(list_length%40==0 &amp;&amp; Jackpot &gt; 0)   				//every 40th player wins the jackpot if  it&#39;s not 0
	{
	gamblerlist[list_length].etherAddress.send(Jackpot);         //send pay out to participant
	Total_Payouts += Jackpot;               					//update paid out amount   
	Jackpot=0;									//Jackpot update
	}
     else   											//you either win the jackpot or the balance, but not both in 1 round
	if(uint(sha3(gamblerlist[list_length].etherAddress)) % 2==0 &amp;&amp; list_length % 2==0 &amp;&amp; Bankroll &gt; 0) 	//if the hashed length of your address is even, 
	{ 												   								//which is a 25% chance, then you get paid out all balance!
	gamblerlist[list_length].etherAddress.send(Bankroll);        //send pay out to participant
	Total_Payouts += Bankroll;               					//update paid out amount
	Bankroll = 0;                      						//Bankroll update
	}
    
    
    
    //enter function ends
    }
  }

//********************************************NEW OWNER

  function setOwner(address new_owner) onlyowner { //set new owner of the casino
      owner = new_owner;
  }
//********************************************SET MIN DEPOSIT

  function setMinDeposit(uint new_mindeposit) onlyowner { //set new minimum deposit rate
      MinDeposit = new_mindeposit;
  }
//********************************************SET FEE RATE

  function setFeeRate(uint new_feerate) onlyowner { //set new fee rate
      FeeRate = new_feerate;
  }
}