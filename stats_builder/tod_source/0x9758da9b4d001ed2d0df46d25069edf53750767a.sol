contract Etheramid {

    struct Participant {
        address inviter;
        address itself;
        uint totalPayout;
    }
    
    mapping (address =&gt; Participant) Tree;
    mapping (uint =&gt; address) Index;
	
	uint Count = 0;
    address top;
    uint constant contribution = 1 ether;
 
    function Etheramid() {
        addParticipant(msg.sender,msg.sender);
        top = msg.sender;
    }
    
    function() {
		uint rand = uint(msg.sender) % Count;
        enter(Index[rand]);
    }
    
    function getParticipantById (uint id) constant public returns ( address inviter, address itself, uint totalPayout ){
		if (id &gt;= Count) return;
		address ida = Index[id];
        inviter = Tree[ida].inviter;
        itself = Tree[ida].itself;
        totalPayout = Tree[ida].totalPayout;
    }
	function getParticipantByAddress (address adr) constant public returns ( address inviter, address itself, uint totalPayout ){
		if (Tree[adr].itself == 0x0) return;
        inviter = Tree[adr].inviter;
        itself = Tree[adr].itself;
        totalPayout = Tree[adr].totalPayout;
    }
    
    function addParticipant(address itself, address inviter) private{
        Index[Count] = itself;
		Tree[itself] = Participant( {itself: itself, inviter: inviter, totalPayout: 0});
        Count +=1;
    }
    
    function getParticipantCount () public constant returns ( uint count ){
       count = Count;
    }
    
    function enter(address inviter) public {
        uint amount = msg.value;
        if ((amount &lt; contribution) || (Tree[msg.sender].inviter != 0x0) || (Tree[inviter].inviter == 0x0)) {
            msg.sender.send(msg.value);
            return;
        }
        
        addParticipant(msg.sender, inviter);
        address next = inviter;
        uint rest = amount;
        uint level = 1;
        while ( (next != top) &amp;&amp; (level &lt; 7) ){
            uint toSend = rest/2;
            next.send(toSend);
            Tree[next].totalPayout += toSend;
            rest -= toSend;
            next = Tree[next].inviter;
            level++;
        }
        next.send(rest);
		Tree[next].totalPayout += rest;
    }
}