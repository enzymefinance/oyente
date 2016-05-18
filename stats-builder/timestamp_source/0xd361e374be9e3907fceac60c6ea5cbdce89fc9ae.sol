contract Highlander {

  struct Contestant {
      address etherAddress;
  }

  Contestant[] public contestant;

  uint public PreviousTime;
  uint public CurrentTime;
  uint public active = 1;
  uint public Current_balance = 0;
  address public owner;

  modifier onlyowner { if (msg.sender == owner) _ }


  function Highlander() {
    owner = msg.sender;
  }

  function() {
    enter();
  }
  
  function enter() {

  	if(msg.value != 5 ether){
		msg.sender.send(msg.value);
		return;
	}
	
	uint idx = contestant.length;
    contestant.length += 1;
    contestant[idx].etherAddress = msg.sender;

	owner.send(msg.value / 10);
	Current_balance = this.balance;
	CurrentTime = now;
 
	if(idx == 0){
	PreviousTime = now;
	return;
	}
	
	if(CurrentTime - PreviousTime &gt; 1 days){

	contestant[idx-1].etherAddress.send(this.balance - 5 ether);
	PreviousTime = CurrentTime;

	} else
		{
		PreviousTime = CurrentTime;
		}

	Current_balance = this.balance;		
	}
	
  function kill(){
  if(msg.sender == owner &amp;&amp; this.balance &lt;= 5) {
  active = 0;
  suicide(owner);
  
  }
  }
  function setOwner(address _owner) onlyowner {
      owner = _owner;
  }	

   // for website
      function CT() constant returns (uint CurrTime) {
        CurrTime = CurrentTime;
    }
      function PT() constant returns (uint PrevTime) {
        PrevTime = PreviousTime;
    }
      function bal() constant returns (uint WebBal) {
        WebBal = Current_balance;
    }	
	
}