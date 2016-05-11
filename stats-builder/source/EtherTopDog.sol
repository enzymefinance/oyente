// 0xf4cae4aec9b4d7682f8cee4d9a273ba063e71366
// 5.82
contract EtherTopDog {

	// fund for bailing out underdogs when they are pushed out
	uint private bailoutBalance = 0;


	// === Underdog Payin Distribution: ===
	
	// percent of underdog deposit amount to go in bailout fund
	uint constant private bailoutFundPercent = 70;

	// percent of underdog deposit that goes to the top dog&#39;s dividend
	uint constant private topDogDividend = 15;

	// percent of underdog deposit sent chip away top dog&#39;s strength
	uint constant private topDogDecayPercent = 10;

	// percent of underdog deposiot that goes to lucky dog&#39;s dividend
	uint constant private luckyDogDividend = 3;

	// vision dog takes a small fee from each underdog deposit
	uint constant private visionDogFeePercent = 2;

	// === === === === === === === === ===

	
	// percentage markup from payin for calculating new mininum TopDog price threshold
	uint constant private topDogMinMarkup = 125;

	// minimum required deposit to become the next Top Dog
	// (aka Top Dog strength / lowest possible takeover threshold)
	// starts at 125% of Top Dog&#39;s deposit, slowly declines as underdogs join
	uint private topDogMinPrice = 1;

	// range above the topdog strength (aka topDogMinPrice) within which
	// the randomly generated required takeover threhold is set
	uint constant private topDogBuyoutRange = 150;

	// percentage of topdog buyout fee gets paid to creator
	uint constant private visionDogBuyPercent = 5;



	// underdog payout markup, as a percentage of their deposits
	// gets reset to 150% after each round when the top dog gets replaced
	// gradually decays to mininum of 120% as underdogs chip away at top dog&#39;s strength
	uint private underDogMarkup = 150;

	// as top dog price declines, these keep track of the range
	// so underDopMarkup can slowly go from 150% to 120% return
	// as the Top Dog mininum price starts at the price ceiling,
	// and declines until it reaches the floor (or lower)
	uint private topDogPriceCeiling = 0;
	uint private topDogPriceFloor = 0;

	// total collected fees from underdogs, paid out whenever Top Dog is bought out
	uint private visionFees = 0;

	// current top dog
	address private topDog = 0x0;

	// underdog entries
	struct Underdog {
		address addr;
		uint deposit;
		uint payout;
		uint bailouts;
	}
	Underdog[] private Underdogs;

	// player names for fun
	mapping (address =&gt; string) dogNames;

	// current lucky dog (if exists) will receive 3% of underdog payins
	// specified as index in Underdogs array
	// 0 = nobody (the very first underdog to join the game is precluded from becoming the Lucky Dog)
	uint private luckyDog = 0;

	// index of next underdog to be paid 
	uint private payoutIndex = 0;

	// count payouts made by underdogs currently in the game
	// so we can have a baseline for dividing the scraps
	uint private payoutCount = 0;

	// address of the creator
	address private visionDog;

	function EtherTopDog() {
		visionDog = msg.sender;
	}


	// ==== Game Info Display ABI functions: ====
	function underdogPayoutFund() public constant returns (uint balance) {
		balance = bailoutBalance;
	}

	function nextUnderdogPayout() public constant returns (uint) {
		if (Underdogs.length - payoutIndex &gt;= 1) {
			return Underdogs[payoutIndex].payout;
		}
	}
	

	function underdogPayoutMarkup() public constant returns (uint) {
		return underDogMarkup;
	}

	function topDogInfo() public constant returns (string name, uint strength) {
		if (topDog != address(0x0)) {
			name = getDogName(topDog);
		} else {
			name = &quot;[not set]&quot;;
		}
		strength = topDogMinPrice;
	}
	function luckyDogInfo() public constant returns (string name) {
		if (luckyDog &gt; 0) {
			name = getDogName(Underdogs[luckyDog].addr);
		} else {
			name = &quot;[nobody]&quot;;
		}
	}

	function underdogCount() constant returns (uint) {
		return Underdogs.length - payoutIndex;
	} 

	function underdogInfo(uint linePosition) constant returns (string name, address dogAddress, uint deposit, uint payout, uint scrapBonus) {
		if (linePosition &gt; 0 &amp;&amp; linePosition &lt;= Underdogs.length - payoutIndex) {

			Underdog thedog = Underdogs[payoutIndex + (linePosition - 1)];
			name = getDogName(thedog.addr);
			dogAddress = thedog.addr;
			deposit = thedog.deposit;
			payout= thedog.payout;
			scrapBonus = thedog.bailouts;
		}
	}

	// ==== End ABI Functions ====



	// ==== Public transaction functions: ====

	// default fallback : play a round
	function() {
		dogFight();
	}
	
	// sets name, optionally plays a round if Ether was sent
	function setName(string DogName) {
		if (bytes(DogName).length &gt;= 2 &amp;&amp; bytes(DogName).length &lt;= 16)
			dogNames[msg.sender] = DogName;

		// if a deposit was sent, play it!
		if (msg.value &gt; 0) {
			dogFight();
		}
		
	}

	function dogFight() public {
		// minimum 1 ETH required to play
		if (msg.value &lt; 1 ether) {
			msg.sender.send(msg.value);
			return;
		}

		// does a topdog exist ?
		if (topDog != address(0x0)) {

			// the actual amount required to knock out the top dig is random within the buyout range
			uint topDogPrice = topDogMinPrice + randInt( (topDogMinPrice * topDogBuyoutRange / 100) - topDogMinPrice, 4321);

			// Calculate the top dog price
			if (msg.value &gt;= topDogPrice) {
				// They bought out the top dog!
				buyTopDog(topDogPrice, msg.value - topDogPrice);
			} else {
				// didn&#39;t buy the top dog, this participant becomes an underdog!
				addUnderDog(msg.value);
			}
		} else {
			// no top dog exists yet, the game must be just getting started
			// put the first deposit in the bailout fund, initialize the game

			// set first topDog 
			topDog = msg.sender;

			topDogPriceFloor = topDogMinPrice;

			bailoutBalance += msg.value;
			topDogMinPrice = msg.value * topDogMinMarkup / 100;

			topDogPriceCeiling = topDogMinPrice;

		}
	}

	// ==== End Public Functions ====



	// ==== Private Functions: ====
	function addUnderDog(uint buyin) private {

		uint bailcount = 0;

		// amount this depositor will be paid when the fund allows
		uint payoutval = buyin * underDogMarkup / 100;

		// add portion of deposit to bailout fund 
		bailoutBalance += buyin * bailoutFundPercent / 100;

		// top dog / lucky dog dividends
		uint topdividend = buyin * topDogDividend / 100;
		uint luckydividend = buyin * luckyDogDividend / 100;

		// is there a lucky dog?
		if (luckyDog != 0 &amp;&amp; luckyDog &gt;= payoutIndex) {
			// pay lucky dog dividends
			Underdogs[luckyDog].addr.send(luckydividend);
		} else {
			// no lucky dog exists, all dividends go to top dog
			topdividend += luckydividend;
		}

		// pay top dog dividends
		topDog.send(topdividend);


		// chip away at the top dog&#39;s strength
		uint topdecay = (buyin * topDogDecayPercent / 100);
		topDogMinPrice -= topdecay;

		// update underdog markup % for next round

		// specified as n/100000 to avoid floating point math
		uint decayfactor = 0;

		// calculate the payout markup for next underdog
		if (topDogMinPrice &gt; topDogPriceFloor) {
			uint decayrange = (topDogPriceCeiling - topDogPriceFloor);
			decayfactor = 100000 * (topDogPriceCeiling - topDogMinPrice) / decayrange;
		} else {
			decayfactor = 100000;
		}
		// markup will be between 120-150% corresponding to current top dog price decline (150% - 30% = 120%)
		underDogMarkup = 150 - (decayfactor * 30 / 100000);



		// creator takes a slice
		visionFees += (buyin * visionDogFeePercent / 100);
		

		// payout as many previous underdogs as the fund can afford
		while (payoutIndex &lt; Underdogs.length &amp;&amp; bailoutBalance &gt;= Underdogs[payoutIndex].payout ) {
			payoutCount -= Underdogs[payoutIndex].bailouts;
			bailoutBalance -= Underdogs[payoutIndex].payout;
			Underdogs[payoutIndex].addr.send(Underdogs[payoutIndex].payout);


			// if the lucky dog was bailed out, the user who did it now becomes the lucky dog
			if (payoutIndex == luckyDog &amp;&amp; luckyDog != 0)
				luckyDog = Underdogs.length;

			payoutIndex++;
			bailcount++;
			payoutCount++;
		}

		
		// add the new underdog to the queue
		Underdogs.push(Underdog(msg.sender, buyin, payoutval, bailcount));

	}

	function buyTopDog(uint buyprice, uint surplus) private {

		// take out vizionDog fee
		uint vfee = buyprice * visionDogBuyPercent / 100;

		uint dogpayoff = (buyprice - vfee);

		// payout previous top dog
		topDog.send(dogpayoff);

		visionFees += vfee;

		// send buy fee (plus previous collected underdog fees) to visionDog
		visionDog.send(visionFees);
		visionFees = 0;

		// record a price floor for underdog markup decay calculation during the next round:
		// the mininum purchase price before buyout
		topDogPriceFloor = topDogMinPrice;

		// set the initial minimum buy price for the next top dog
		topDogMinPrice = msg.value * topDogMinMarkup / 100;

		// the price ceiling for calculating the underdog markup decay is the new minimum price
		topDogPriceCeiling = topDogMinPrice;


		// check for eligible lucky dog...
//		if (Underdogs.length - payoutIndex &gt; 0) {
			// lucky dog is most recent underdog to make an entry
//			luckyDog = Underdogs.length - 1;
//		} else {
			// no dogs waiting in line?  all dividends will go to top dog this round
//			luckyDog = 0;
//		}
		

		// reset underdog markup for next round
		underDogMarkup = 150;

		// how many dogs are waiting?
		uint linelength = Underdogs.length - payoutIndex;

		// surplus goes to pay scraps to random underdogs
		// calculate and pay scraps


		// are there underdogs around to receive the scraps?
		if (surplus &gt; 0 &amp;&amp; linelength &gt; 0 ) {
			throwScraps(surplus);
		}


		// if there are any underdogs in line, the lucky dog will be picked from among them	
		if (linelength &gt; 0) {

			// randomly pick a new lucky dog, with luck weighted toward more recent entries

			// weighting works like this:
			// 	For example, if the line length is 6, the most recent entry will
			//	be 6 times more likely than the oldest (6/21 odds),
			//	the second most recent will be 5 times more likely than the oldest (5/21 odds)
			//	the third most recent will be 4 times as likely as the oldest (4/21 odds),
			//	etc...

			//	of course, the player that has been in line longest is
			//	least likely to be lucky (1/21 odds in this example)
			//	and will be getting sent out of the game soonest anyway

			uint luckypickline = (linelength % 2 == 1) ?
				( linelength / 2 + 1 ) + (linelength + 1) * (linelength / 2) :  // odd
				( (linelength + 1) * (linelength / 2)  ); // even

			uint luckypick = randInt(luckypickline, 69);
	
			uint pickpos = luckypickline - linelength;
			uint linepos = 1;

			while (pickpos &gt;= luckypick &amp;&amp; linepos &lt; linelength) {
				pickpos -= (linelength - linepos);
				linepos++;
			}

			luckyDog = Underdogs.length - linepos;
		} else {
			// no underdogs in line?  no lucky dog this round.
			// (should only possibly happen when game starts)
			luckyDog = 0;
		}
		

		// the new top dog is crowned!
		topDog = msg.sender;
	}

	function throwScraps(uint totalscrapvalue) private {

		// how many dogs are waiting?
		uint linelength = Underdogs.length - payoutIndex;

		// to keep from having too many transactions, make sure we never have more than 7 scraps.
		// the more dogs in line, the more we jump over when scraps get scattered
		uint skipstep = (linelength / 7) + 1;

		// how many pieces to divide (roughly, randomization might make it more or less)
		uint pieces = linelength / skipstep;

		// how far from the end of the queue to start throwing the first scrap (semi-random)
		uint startoffset = randInt(skipstep, 42) - 1;

		// base size for scraps...  
		uint scrapbasesize = totalscrapvalue / (pieces + payoutCount);

		// minimum base scrap size of 0.5 eth
		if (scrapbasesize &lt; 500 finney) {
			scrapbasesize = 500 finney;
		}

		uint scrapsize;
		uint sptr = Underdogs.length - 1 - startoffset;

		uint scrapvalueleft = totalscrapvalue;

		while (pieces &gt; 0 &amp;&amp; scrapvalueleft &gt; 0 &amp;&amp; sptr &gt;= payoutIndex) {
			// those who bailed out other dogs get bigger scraps
			// size of the scrap is multiplied by # of other dogs the user bailed out
			scrapsize = scrapbasesize * (Underdogs[sptr].bailouts + 1);


			// scraps can never be more than what&#39;s in the pile
			if (scrapsize &lt; scrapvalueleft) {
				scrapvalueleft -= scrapsize;
			} else {
				scrapsize = scrapvalueleft;
				scrapvalueleft = 0;
			}

			// pay it
			Underdogs[sptr].addr.send(scrapsize);
			pieces--;
			sptr -= skipstep;
		}

		// any scraps left uncaught? put them in the bailout fund for the underdogs
		if (scrapvalueleft &gt; 0) {
			bailoutBalance += scrapvalueleft;
		}
	}

	function getDogName(address adr) private constant returns (string thename) {
		if (bytes(dogNames[adr]).length &gt; 0)
			thename = dogNames[adr];
		else
			thename = &#39;Unnamed Mutt&#39;;
	}
	
	// Generate pseudo semi-random number between 1 - max 
	function randInt(uint max, uint seedswitch) private constant returns (uint randomNumber) {
		return( uint(sha3(block.blockhash(block.number-1), block.timestamp + seedswitch) ) % max + 1 );
	}
}