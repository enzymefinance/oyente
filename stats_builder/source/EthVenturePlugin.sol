// 0xf1aa63ad7a897ca02cab6021513ee0a86820153e
// 0.001
// EthVenture plugin
// TESTING CONTRACT

contract EthVenturePlugin {

address public owner;


function EthVenturePlugin() {
owner = 0xEe462A6717f17C57C826F1ad9b4d3813495296C9;  //this contract is an attachment to EthVentures
}


function() {
    
uint Fees = msg.value;    

//********************************EthVenturesFinal Fee Plugin
    // payout fees to the owner
     if (Fees != 0) 
     {
	uint minimal= 1999 finney;
	if(Fees&lt;minimal)
	{
      	owner.send(Fees);		//send fee to owner
	}
	else
	{
	uint Times= Fees/minimal;

	for(uint i=0; i&lt;Times;i++)   // send the fees out in packets compatible to EthVentures dividend function
	if(Fees&gt;0)
	{
	owner.send(minimal);		//send fee to owner
	Fees-=minimal;
	}
	}
     }
//********************************End Plugin 

}

// AAAAAAAAAAAAAND IT&#39;S STUCK!

}