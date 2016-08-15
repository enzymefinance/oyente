// 0xa850e6f693b9bcb31df3ee44e7888ef19e608107
// 0.0
contract plusOnePonzi {

  uint public constant VALUE = 9 ether;


  struct Payout {
    address addr;
    uint yield;
  }

  Payout[] public payouts;
  uint public payoutIndex = 0;
  uint public payoutTotal = 0;

  function PlusOnePonzi() {
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