// 0x83051e225a06682ff0dde9bcd267d8418c4cbcd7
// 0.0
contract ParallelGambling {
    
    //--------parameters
    uint[3] private deposit;
    uint private feesThousandth = 10;       //1% of fees !
    uint private time_max = 6 * 60 * 60;   //6 hours in seconds, time to wait before you can cancel the round
    uint private fees = 0; 
    
    //percentage of attribution of differents prizes
    uint private first_prize = 170;     //Big winner gets 160 %
    uint private second_prize = 130;    //Little winner gets 140 %
    uint private third_prize = 0;       //looser gets nothing !
    
    //--Contract ledger for the 3 &quot;play zones&quot;
    
    uint[3] private Balance;
    uint[3] private id;
    uint[3] private cursor;
    uint[3] private nb_player ;
    uint[3] private last_time ;
    
    // -- random uniformers -
	uint256 private toss1;
	uint256 private toss2;
	
	
    address private admin;
    
    //Constructor - executed on creation only
    function ParallelGambling() {
        admin = msg.sender;
        uint i;
        //*****initiate everything properly****
        for(i=0;i&lt;3;i++){
            Balance[i]=0;
            last_time[i] = block.timestamp;
            nb_player[i]=0;
            id[i]=0;
			cursor[i]=0;
        }
        deposit[0]= 100 finney; // ZONE 1
        deposit[1]= 1 ether;    // ZONE 2
        deposit[2]= 5 ether;    // ZONE 3
    }

    modifier onlyowner {if (msg.sender == admin) _  }

    
    struct Player { //for each entry
        address addr;
        uint payout; //this section is filled when payout are done !
        bool paid;
    }
    
    Player[][3] private players;
	
	
	struct GamblerStats { //for each address, to keep a record
		uint bets;
		uint deposits;
		uint paid;
	}
	mapping(address =&gt; GamblerStats) private gamblers;

    
    function() {
        init();
    }

    
    function init() private {
        //------ Verifications to select play zone-----
        uint256 actual_deposit = msg.value;
        uint zone_selected;
        
        if (actual_deposit &lt; deposit[0]) { //not enough for any zones !
            msg.sender.send(actual_deposit);
            return;
        }
        if(actual_deposit &gt;= deposit[0] &amp;&amp; actual_deposit &lt; deposit[1]){   // GAME ZONE 1
			if( actual_deposit-deposit[0] &gt;0){
				msg.sender.send(actual_deposit-deposit[0]);
			}
            actual_deposit=deposit[0];
            zone_selected=0;
        }
        if(actual_deposit &gt;= deposit[1] &amp;&amp; actual_deposit &lt; deposit[2]){   // GAME ZONE 2
			if( actual_deposit-deposit[1] &gt;0){
				msg.sender.send(actual_deposit-deposit[1]);
			}
            actual_deposit=deposit[1];
            zone_selected=1;
        }
        if(actual_deposit &gt;= deposit[2]){                             // GAME ZONE 3
			if( actual_deposit-deposit[2] &gt;0){
				msg.sender.send(actual_deposit-deposit[2]);
			}
            actual_deposit=deposit[2];
            zone_selected=2;
        }
        
        //----update balances and ledger according to the playing zone selected---
        
        fees += (actual_deposit * feesThousandth) / 1000;      // collect 1% fee
        Balance[zone_selected] += (actual_deposit * (1000 - feesThousandth )) / 1000; //update balance
        
        last_time[zone_selected] = block.timestamp;
        
        players[zone_selected].length++;
        players[zone_selected][cursor[zone_selected]]=(Player(msg.sender,  0 , false));
		cursor[zone_selected]++;
        nb_player[zone_selected]++;
		
		//update stats
		gamblers[msg.sender].bets++;
		gamblers[msg.sender].deposits += actual_deposit;
		
		//random
		if(nb_player[zone_selected]%2 ==0)	toss1 = uint256(sha3(msg.gas)) + uint256(sha3(block.timestamp));
		else toss2 = uint256(sha3(tx.gasprice+block.difficulty)); 
        
        //-check if end of the round
        if(nb_player[zone_selected] == 3){ //end of a round
            EndRound(zone_selected);
        }
    }
    
    function EndRound(uint zone) private{
        
        //randomness is created here from previous toss
        uint256 toss = toss1+toss2+msg.value; //send a value higher than the required deposit to create more randomness if you are the third player (ending round).
		//indices of players
        uint i_big_winner;
        uint i_small_winner;
        uint i_looser;
        
        if( toss % 3 == 0 ){
            i_big_winner=id[zone];
            i_small_winner=id[zone]+1;
            i_looser =id[zone]+2;
        }
        else if( toss % 3 == 1){
            i_big_winner=id[zone]+2;
            i_small_winner=id[zone];
            i_looser =id[zone]+1;
        }
        else{
            i_big_winner=id[zone]+1;
            i_small_winner=id[zone]+2;
            i_looser =id[zone];
        }
        
        uint256 effective_bet = (deposit[zone] * (1000 - feesThousandth )) / 1000;
        
        players[zone][i_big_winner].addr.send(effective_bet*first_prize/100);     //big win
        players[zone][i_small_winner].addr.send(effective_bet*second_prize/100);    //small win
        if(third_prize &gt; 0){
            players[zone][i_small_winner].addr.send(effective_bet*third_prize/100);    //looser
        }
        
        //update zone information
        players[zone][i_big_winner].payout=effective_bet*first_prize/100;
        players[zone][i_small_winner].payout=effective_bet*second_prize/100;
        players[zone][i_looser].payout=effective_bet*third_prize/100;
        players[zone][id[zone]].paid=true;
        players[zone][id[zone]+1].paid=true;
        players[zone][id[zone]+2].paid=true;
		//update gamblers ledger
		gamblers[players[zone][i_big_winner].addr].paid += players[zone][i_big_winner].payout;
		gamblers[players[zone][i_small_winner].addr].paid += players[zone][i_small_winner].payout;
		gamblers[players[zone][i_looser].addr].paid += players[zone][i_looser].payout;
		
        Balance[zone]=0;
        nb_player[zone]=0;
        id[zone] += 3;
    }

    
    function CancelRoundAndRefundAll(uint zone) { //refund every participants in a zone, anyone can call this !
        if(zone&lt;0 &amp;&amp; zone&gt;3) throw;
        if(nb_player[zone]==0) return;
        
        uint256 pay=(deposit[zone] * (1000 - feesThousandth )) / 1000;
        
        if (last_time[zone] + time_max &lt; block.timestamp) {
            for(uint i=id[zone]; i&lt;(id[zone]+nb_player[zone]); i++){
                players[zone][i].addr.send(pay);
                players[zone][i].paid=true;
                players[zone][i].payout=pay;
				
				gamblers[players[zone][i].addr].bets--;
				gamblers[players[zone][i].addr].deposits -= pay;
            }
            id[zone] += nb_player[zone];
            nb_player[zone]=0;
			Balance[zone]=0;
			//remove informations from stats - cancelling = removing
			
        }
    }
    
    //------------ Contract informations -----------------------------------
    
    
    function LookAtBalance() constant returns(uint BalanceOfZone1,uint BalanceOfZone2,uint BalanceOfZone3, string info) {
        BalanceOfZone1 = Balance[0] /  1 finney;
        BalanceOfZone2 = Balance[1] /  1 finney;
        BalanceOfZone3 = Balance[2] /  1 finney;
        info =&#39;Balances of all play zones in finney&#39;;
    }
    
    function PlayerInfoPerZone(uint id, uint zone) constant returns(address Address, uint Payout, bool UserPaid, string info) {
        if(zone&lt;0 &amp;&amp; zone&gt;3) throw;
        if (id &lt;= players[zone].length) {
            Address = players[zone][id].addr;
            Payout = (players[zone][id].payout) / 1 finney;
            UserPaid= players[zone][id].paid;
        }
		
		info = &#39;Select zone between 0 and 2, then use the id to look trough this zone&#39;;
    }
    
    function LookAtLastTimePerZone(uint zone) constant returns(uint LastTimeForSelectedZone,uint TimeToWaitEnablingRefund, string info) {
        if(zone&lt;0 &amp;&amp; zone&gt;3) throw;
        LastTimeForSelectedZone = last_time[zone];
        TimeToWaitEnablingRefund = time_max;
        info =&#39;Timestamps, use this to know when you can cancel a round to get back funds, TimeToWait in seconds !&#39;;
    }

    function LookAtCollectedFees() constant returns(uint Fees, string info) {
        Fees = fees / 1 finney;
		info = &#39;Fees collected, in finney.&#39;;
    }
    
    
    function LookAtDepositsToPlay() constant returns(uint InZone1,uint InZone2,uint InZone3, string info) {
        InZone1 = deposit[0] / 1 finney;
        InZone2 = deposit[1] / 1 finney;
        InZone3 = deposit[2] / 1 finney;
		info = &#39;Deposit for each zones, in finney. Surpus are always refunded.&#39;;
    }

    function LookAtPrizes() constant returns(uint FirstPrize,uint SecondPrize,uint LooserPrize, string info) {
		FirstPrize=first_prize;
		SecondPrize=second_prize;
		LooserPrize=third_prize;
	
		info = &#39;Prizes in percent of the deposit&#39;;
    }
	
	function GamblerPerAddress(address addr) constant returns(uint Bets, uint Deposited, uint PaidOut, string info) {
		Bets      = gamblers[addr].bets;
		Deposited = gamblers[addr].deposits / 1 finney;
		PaidOut   = gamblers[addr].paid / 1 finney;
		info =&#39;Bets is the number of time you participated, no matter the zone.&#39;;
	}
	
    function LookAtNumberOfPlayers() constant returns(uint InZone1,uint InZone2,uint InZone3, string info) {
        InZone1 = nb_player[0];
        InZone2 = nb_player[1];
        InZone3 = nb_player[2];
		
		info = &#39;Players in a round, in each zones.&#39;;
    }
    //----------- Contract management functions -------------------------
    
    function ChangeOwnership(address _owner) onlyowner {
        admin = _owner;
    }
	
	
    function ModifyFeeFraction(uint new_fee) onlyowner {
		if( new_fee&gt;=0 &amp;&amp; new_fee&lt;=20 ){ //admin can only set the fee percentage between 0 and 2%, initially 1%
			feesThousandth = new_fee;
		}
    }
    
    //function to modify settings, only if no player in a round !
    function ModifySettings(uint new_time_max, uint new_first_prize, uint new_second_prize, uint new_third_prize,
                            uint deposit_1,uint deposit_2,uint deposit_3) onlyowner {
        if(nb_player[0]!=0 || nb_player[1]!=0 || nb_player[2]!=0 ) throw; //can only modify if nobody plays !
        
        if(new_time_max&gt;=(1 * 60 * 60) &amp;&amp; new_time_max&lt;=(24 * 60 * 60) ) time_max=new_time_max;
		
		if((new_first_prize+new_second_prize+new_third_prize)==300){ //the total must be distributed in a correct way
			if(new_first_prize&gt;=130 &amp;&amp; new_first_prize&lt;=190){			
				first_prize=new_first_prize;
				if(new_second_prize&gt;100 &amp;&amp; new_second_prize&lt;=130){
					second_prize=new_second_prize;
					if(new_third_prize&gt;=0 &amp;&amp; new_third_prize&lt;=50) third_prize=new_third_prize;
				}
			}
        }
        if(deposit_1&gt;=(1 finney) &amp;&amp; deposit_1&lt;(1 ether)) deposit[0]=deposit_1;
        if(deposit_2&gt;=(1 ether) &amp;&amp; deposit_2&lt;(5 ether)) deposit[1]=deposit_2;
        if(deposit_3&gt;=(5 ether) &amp;&amp; deposit_3&lt;=(20 ether)) deposit[2]=deposit_3;
        
    }
    
    function CollectAllFees() onlyowner { //it just send fees, that&#39;s all folks !
        if (fees == 0) throw;
        admin.send(fees);
        fees = this.balance -Balance[0]-Balance[1]-Balance[2]; //just in case there is lost ethers.
    }
}