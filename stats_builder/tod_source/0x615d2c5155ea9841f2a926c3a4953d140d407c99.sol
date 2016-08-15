// Welcome to * Bet On Hash *
//
// this is a round based bet game
// a round consists of 6 players
// 
// you bet on the first byte of the last (6th) players blockhash (unpredictable, 50% chance)
// 
// ** to join: send one byte data (0x01 or 0x81) with a bet amount of 0.01 ether (10 finney) to the contract address
// 
// if your data byte is less than 0x80 you bet the blockhashs first byte is &lt; 0x80
// if your data byte is greater than or equal 0x80 you bet the blockhashs first byte is &gt;= 0x80
// 
// if you lose your bet your bet amount goes to the pool for winners
// 
// if you win your bet:
// 	* you will get back 100% of your payment
// 	* you will win a proportional part of the winner pool (win amount = winner pool / winners - 1%) 
// 
// payout is triggered when a player starts the next round
// 
// additional rules:
// each address can only play once per round
// every additional payment during the same round will be paid back immediatly
// every payment below the bet value is considered as a donation for the winner pool
// every amount that is exceeding the bet value will be paid back
// if nobody wins in a round, the paid amounts will raise the winner pool for the next round
//
// ** if you pay to the contract, you agree that you may lose (50% chance!) the paid amount **


contract BetOnHashV82 {
  struct Player {
    address addr;
    byte bet;
  }
  
  Player[] public players;
  bool public active;
  uint public betAmount;
  uint public playersPerRound;
  uint public round;
  uint public winPool;
  byte public betByte;

  uint lastPlayersBlockNumber;
  address owner;
  
  modifier onlyowner { if (msg.sender == owner) _ }
  
  function BetOnHashV82() {
    owner = msg.sender;
    betAmount = 10 finney;
    round = 1;
    playersPerRound = 6;
    active = true;
    winPool = 0;
  }
  
  function finishRound() internal {
    //get block hash of last player
    bytes32 betHash = block.blockhash(lastPlayersBlockNumber);
    betByte = byte(betHash);
    byte bet;
    uint8 ix; 
    
    //check win or loss, calculate winnPool
    address[] memory winners = new address[](playersPerRound);
    uint8 numWinners=0;
    for(ix=0; ix &lt; players.length; ix++) {
      Player p = players[ix];
      if(p.bet &lt; 0x80 &amp;&amp; betByte &lt; 0x80 || p.bet &gt;= 0x80 &amp;&amp; betByte &gt;= 0x80) {
        //player won
        winners[numWinners++] = p.addr;
      } 
      else winPool += betAmount;
    }
    
    //calculate winners payouts and pay out
    if(numWinners &gt; 0) {
      uint winAmount = (winPool / numWinners) * 99 / 100;
      for(ix = 0; ix &lt; numWinners; ix++) {
        if(!winners[ix].send(betAmount + winAmount)) throw;
      }
      winPool = 0;
    }
    
    //start next round
    round++;
    delete players;
  }
  
  function reject() internal {
    msg.sender.send(msg.value);
  }
  
  function join() internal {
  
    //finish round if next players block is above last players block
    if(players.length &gt;= playersPerRound) { 
      if(block.number &gt; lastPlayersBlockNumber) finishRound(); 
      else {reject(); return;}  //too many players in one block -&gt; pay back
    }

    //payments below bet amount are considered as donation for the winner pool
    if(msg.value &lt; betAmount) {
      winPool += msg.value; 
      return;
    }
    
    //no data sent -&gt; pay back
    if(msg.data.length &lt; 1) {reject();return;}
    
    //prevent players to play more than once per round:
    for(uint8 i = 0; i &lt; players.length; i++)
      if(msg.sender == players[i].addr) {reject(); return;}
    
    //to much paid -&gt; pay back all above bet amount
    if(msg.value &gt; betAmount) {
      msg.sender.send(msg.value - betAmount);
    }
    
    //register player
    players.push( Player(msg.sender, msg.data[0]) );
    lastPlayersBlockNumber = block.number;
  }
  
  function () {
    if(active) join();
    else throw;
  }
  
  function forceFinish() onlyowner {
    if(players.length &gt; 0) finishRound();
  }
  
  function paybackLast() onlyowner returns (bool) {
    if(players.length == 0) return true;
    if (players[players.length - 1].addr.send(betAmount)) {
      players.length--;
      return true;
    }
    return false;
  }
  
  //if something goes wrong, the owner can trigger pay back
  function paybackAll() onlyowner returns (bool) {
    while(players.length &gt; 0) {if(!paybackLast()) return false;}
    return true;
  }
  
  function collectFees() onlyowner {
    uint playersEther = winPool;
    uint8 ix;
    for(ix=0; ix &lt; players.length; ix++) playersEther += betAmount;
    uint fees = this.balance - playersEther;
    if(fees &gt; 0) owner.send(fees);
  }
  
  function changeOwner(address _owner) onlyowner {
    owner = _owner;
  }
  
  function setPlayersPerRound(uint num) onlyowner {
    if(players.length &gt; 0) finishRound();
    playersPerRound = num;
  }
  
  function stop() onlyowner {
    active = false;
    paybackAll();
  }

  //contract can only be destructed if all payments where paid back  
  function kill() onlyowner {
    if(!active &amp;&amp; paybackAll()) 
      selfdestruct(owner);
  }
}