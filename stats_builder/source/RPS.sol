// 0xcccd5b66bf6990c7210fd76781469b19bcff9bae
// 1.0
contract RPS
{
    struct Hand
    {
        uint hand;
    }
	
	bool		private		shift = true;
	address[]	private 	hands;
	bool 	 	private 	fromRandom = false;

    mapping(address =&gt; Hand[]) tickets;

	function Rock(){
		setHand(0);
	}
	function Paper(){
		setHand(1);
	}
	function Scissors(){
		setHand(2);
	}
	
	function () {		 
		if (msg.value &gt;= 1000000000000000000){
			msg.sender.send((msg.value-1000000000000000000));
			fromRandom = true;
			setHand((addmod(now,0,3)));
		}
		if (msg.value &lt; 1000000000000000000){
			msg.sender.send(msg.value);
		}
    }
	
    function setHand(uint inHand) internal
    {
		if(msg.value != 1000000000000000000 &amp;&amp; !fromRandom){
			msg.sender.send(msg.value);
		}
		if(msg.value == 1000000000000000000 || fromRandom){
	        tickets[msg.sender].push(Hand({
	            hand: inHand,
	        }));
			hands.push(msg.sender);
			shift = !shift;
		}
		if(shift){
			draw();
		}
		fromRandom = false;
	}
	
	function draw() internal {
		var handOne = tickets[hands[0]][0].hand;
		var handTwo = tickets[hands[1]][0].hand;
		delete tickets[hands[0]];
		delete tickets[hands[1]];
		
		if(handOne == handTwo){
			hands[0].send(1000000000000000000);
			hands[1].send(1000000000000000000);
			delete hands;
		}
		if(handTwo-handOne == 1){
			winner(hands[0]);
		}
		if(handOne-handTwo == 1){
			winner(hands[1]);
		}
		if(handOne == 0 &amp;&amp; handTwo == 2){
			winner(hands[1]);
		}
		if(handTwo == 0 &amp;&amp; handOne == 2){
			winner(hands[0]);
		}
	}
	
	function winner(address _address) internal {
		_address.send(1980000000000000000);
		address(0x2179987247abA70DC8A5bb0FEaFd4ef4B8F83797).send(20000000000000000);
		delete hands;
	}
}