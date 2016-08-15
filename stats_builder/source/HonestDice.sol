// 0xd79b4c6791784184e2755b2fc1659eaab0f80456
// 78.9445707436
contract HonestDice {
	
	event Bet(address indexed user, uint blocknum, uint256 amount, uint chance);
	event Won(address indexed user, uint256 amount, uint chance);
	
	struct Roll {
		uint256 value;
		uint chance;
		uint blocknum;
		bytes32 secretHash;
		bytes32 serverSeed;
	}
	
	uint betsLocked;
	address owner;
	address feed;				   
	uint256 minimumBet = 1 * 1000000000000000000; // 1 Ether
	uint256 constant maxPayout = 5; // 5% of bankroll
	uint constant seedCost = 100000000000000000; // This is the cost of supplyin the server seed, deduct it;
	mapping (address =&gt; Roll) rolls;
	uint constant timeout = 20; // 5 Minutes
	
	function HonestDice() {
		owner = msg.sender;
		feed = msg.sender;
	}
	
	function roll(uint chance, bytes32 secretHash) {
		if (chance &lt; 1 || chance &gt; 255 || msg.value &lt; minimumBet || calcWinnings(msg.value, chance) &gt; getMaxPayout() || betsLocked != 0) { 
			msg.sender.send(msg.value); // Refund
			return;
		}
		rolls[msg.sender] = Roll(msg.value, chance, block.number, secretHash, 0);
		Bet(msg.sender, block.number, msg.value, chance);
	}
	
	function serverSeed(address user, bytes32 seed) {
		// The server calls this with a random seed
		if (msg.sender != feed) return;
		if (rolls[user].serverSeed != 0) return;
		rolls[user].serverSeed = seed;
	}
	
	function hashTo256(bytes32 hash) constant returns (uint _r) {
		// Returns a number between 0 - 255 from a hash
		return uint(hash) &amp; 0xff;
	}
	
	function hash(bytes32 input) constant returns (uint _r) {
		// Simple sha3 hash. Not to be called via the blockchain
		return uint(sha3(input));
	}
	
	function isReady() constant returns (bool _r) {
		return isReadyFor(msg.sender);
	}
	
	function isReadyFor(address _user) constant returns (bool _r) {
		Roll r = rolls[_user];
		if (r.serverSeed == 0) return false;
		return true;
	}
	
	function getResult(bytes32 secret) constant returns (uint _r) {
		// Get the result number of the roll
		Roll r = rolls[msg.sender];
		if (r.serverSeed == 0) return;
		if (sha3(secret) != r.secretHash) return;
		return hashTo256(sha3(secret, r.serverSeed));
	}
	
	function didWin(bytes32 secret) constant returns (bool _r) {
		// Returns if the player won or not
		Roll r = rolls[msg.sender];
		if (r.serverSeed == 0) return;
		if (sha3(secret) != r.secretHash) return;
		if (hashTo256(sha3(secret, r.serverSeed)) &lt; r.chance) { // Winner
			return true;
		}
		return false;
	}
	
	function calcWinnings(uint256 value, uint chance) constant returns (uint256 _r) {
		// 1% house edge
		return (value * 99 / 100) * 256 / chance;
	}
	
	function getMaxPayout() constant returns (uint256 _r) {
		return this.balance * maxPayout / 100;
	}
	
	function claim(bytes32 secret) {
		Roll r = rolls[msg.sender];
		if (r.serverSeed == 0) return;
		if (sha3(secret) != r.secretHash) return;
		if (hashTo256(sha3(secret, r.serverSeed)) &lt; r.chance) { // Winner
			msg.sender.send(calcWinnings(r.value, r.chance) - seedCost);
			Won(msg.sender, r.value, r.chance);
		}
		
		delete rolls[msg.sender];
	}
	
	function canClaimTimeout() constant returns (bool _r) {
		Roll r = rolls[msg.sender];
		if (r.serverSeed != 0) return false;
		if (r.value &lt;= 0) return false;
		if (block.number &lt; r.blocknum + timeout) return false;
		return true;
	}
	
	function claimTimeout() {
		// Get your monies back if the server isn&#39;t responding with a seed
		if (!canClaimTimeout()) return;
		Roll r = rolls[msg.sender];
		msg.sender.send(r.value);
		delete rolls[msg.sender];
	}
	
	function getMinimumBet() constant returns (uint _r) {
		return minimumBet;
	}
	
	function getBankroll() constant returns (uint256 _r) {
		return this.balance;
	}
	
	function getBetsLocked() constant returns (uint _r) {
		return betsLocked;
	}
	
	function setFeed(address newFeed) {
		if (msg.sender != owner) return;
		feed = newFeed;
	}
	
	function lockBetsForWithdraw() {
		if (msg.sender != owner) return;
		uint betsLocked = block.number;
	}
	
	function unlockBets() {
		if (msg.sender != owner) return;
		uint betsLocked = 0;
	}
	
	function withdraw(uint amount) {
		if (msg.sender != owner) return;
		if (betsLocked == 0 || block.number &lt; betsLocked + 5760) return;
		owner.send(amount);
	}
}