// 0x43bbc7fafb860d974037b8f7dd06b6f6fe799b3e
// 0.473406234918
// A Ponzi scheme where old investors are payed with the funds received from new investors.
// Unlike what is out there in the market, the contract creator received no funds - if you
// don&#39;t do work, you cannot expect to be paid. People who put in the funds receive all the
// returns. Owners can particiapte themselves, there is no leaching off the top and slowing
// down payouts for the participants.
contract ZeroPonzi {
  // minimum &amp; maxium entry values
  uint public constant MIN_VALUE = 100 finney;
  uint public constant MAX_VALUE = 10 ether;

  // the return multiplier &amp; divisors, yielding 1.25 (125%) returns
  uint public constant RET_MUL = 125;
  uint public constant RET_DIV = 100;

  // entry structure, storing the address &amp; yield
  struct Payout {
    address addr;
    uint yield;
  }

  // our actual queued payouts, index of current &amp; total distributed
  Payout[] public payouts;
  uint public payoutIndex = 0;
  uint public payoutTotal = 0;

  // construtor, no additional requirements
  function ZeroPonzi() {
  }

  // single entry point, add entry &amp; pay what we can
  function() {
    // we only accept values in range
    if ((msg.value &lt; MIN_VALUE) || (msg.value &gt; MAX_VALUE)) {
      throw;
    }

    // queue the current entry as a future payout recipient
    uint entryIndex = payouts.length;
    payouts.length += 1;
    payouts[entryIndex].addr = msg.sender;
    payouts[entryIndex].yield = (msg.value * RET_MUL) / RET_DIV;

    // send payouts while we can afford to do so
    while (payouts[payoutIndex].yield &lt; this.balance) {
      payoutTotal += payouts[payoutIndex].yield;
      payouts[payoutIndex].addr.send(payouts[payoutIndex].yield);
      payoutIndex += 1;
    }
  }
}