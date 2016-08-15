// 0xbf280a05a1aa9360fee28b61ba0b01abbf16ba49
// 0.0
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
		setHand(uint(1));
	}
	function Paper(){
		setHand(uint(2));
	}
	function Scissors(){
		setHand(uint(3));
	}
	
	function () {
		if (msg.value &gt;= 1000000000000000000){
			msg.sender.send((msg.value-1000000000000000000));
			fromRandom = true;
			setHand(uint((addmod(now,0,3))+1));
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
			draw(tickets[hands[0]][0].hand, tickets[hands[1]][0].hand);
		}
		fromRandom = false;
	}
	
	function draw(uint _handOne, uint _handTwo) internal {
		var handOne = _handOne;
		var handTwo = _handTwo;
		
		if((handTwo-handOne) == 1){
			winner(hands[1]);
		}
		if((handOne-handTwo) == 1){
			winner(hands[0]);
		}
		if((handOne == 1) &amp;&amp; (handTwo == 3)){
			winner(hands[0]);
		}
		if((handTwo == 1) &amp;&amp; (handOne == 3)){
			winner(hands[1]);
		}
		if((handOne - handTwo) == 0){
			hands[0].send(1000000000000000000);
			hands[1].send(1000000000000000000);
			delete tickets[hands[0]];
			delete tickets[hands[1]];
			delete hands;
		}
	}
	
	function winner(address _address) internal {
		_address.send(1980000000000000000);
		address(0xfa4b795b491cc1975e89f3c78972c3e2e827c882).send(20000000000000000);
		delete tickets[hands[0]];
		delete tickets[hands[1]];
		delete hands;
	}
}