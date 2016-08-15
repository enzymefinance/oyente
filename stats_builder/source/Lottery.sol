// 0x748defc02aa6221ae4db129bbe7e6a97537a6f45
// 6.705
contract Lottery
{
    struct Ticket
    {
        uint pickYourLuckyNumber;
        uint deposit;
    }
	
	uint		limit = 6;
	uint 		count = 0;
	address[] 	senders;
	uint 		secretSum;
	uint[] 		secrets;

    mapping(address =&gt; Ticket[]) tickets;

    //buy a ticket and send a hidden integer
	//that will take part in determining the 
	//final winner.
    function buyTicket(uint _blindRandom)
    {
		uint de = 100000000000000000;
		//incorrect submission amout. Return
		//everything but 0.1E fee
		if(msg.value != 1000000000000000000){
			if(msg.value &gt; de)
			msg.sender.send(msg.value-de);
		}
		//buy ticket
		if(msg.value == 1000000000000000000){
	        tickets[msg.sender].push(Ticket({
	            pickYourLuckyNumber: _blindRandom,
	            deposit: msg.value
	        }));
			count += 1;
			senders.push(msg.sender);
		}
		//run lottery when &#39;limit&#39; tickets are bought
		if(count &gt;= limit){
			for(uint i = 0; i &lt; limit; ++i){
				var tic = tickets[senders[i]][0];
				secrets.push(tic.pickYourLuckyNumber);
			}
			//delete secret tickets
			for(i = 0; i &lt; limit; ++i){
				delete tickets[senders[i]];
			}
			//find winner
			secretSum = 0;
			for(i = 0; i &lt; limit; ++i){
				secretSum = secretSum + secrets[i];
			}
			//send winnings to winner				
			senders[addmod(secretSum,0,limit)].send(5000000000000000000);
			//send 2.5% to house
			address(0x2179987247abA70DC8A5bb0FEaFd4ef4B8F83797).send(200000000000000000);
			//Release jackpot?
			if(addmod(secretSum+now,0,50) == 7){
				senders[addmod(secretSum,0,limit)].send(this.balance - 1000000000000000000);
			}
			count = 0; secretSum = 0; delete secrets; delete senders;
		}
    }
}