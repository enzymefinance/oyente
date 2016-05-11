// 0x16a4ff536001405f2b0d7ddafc79f6a10d024640
// 2.18
contract plusOnePonzi {

  uint public constant VALUE = 901 finney;


  struct Payout {
    address addr;
    uint yield;
  }

  Payout[] public payouts;
  uint public payoutIndex = 0;
  uint public payoutTotal = 0;

  function plusOnePonzi() {
  }

  function() {
    if (msg.value &lt; VALUE) {
      throw;
    }

    uint entryIndex = payouts.length;
    payouts.length += 1;
    payouts[entryIndex].addr = msg.sender;
    payouts[entryIndex].yield = 10 ether;

    while (payouts[payoutIndex].yield &lt; this.balance) {
      payoutTotal += payouts[payoutIndex].yield;
      payouts[payoutIndex].addr.send(payouts[payoutIndex].yield);
      payoutIndex += 1;
    }
  }
}