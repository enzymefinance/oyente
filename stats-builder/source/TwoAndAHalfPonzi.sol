// 0x89c2352cb600df56fe4bfb5882caadef3e96213f
// 0.503
contract TwoAndAHalfPonzi {

  uint public constant VALUE = 1001 finney;
  uint public constant VALUEBACK = 2500 finney;

  struct Payout {
    address addr;
    uint yield;
  }

  Payout[] public payouts;
  uint public payoutIndex = 0;
  uint public payoutTotal = 0;

  function TwoAndAHalfPonzi() {
  }

  function() {
    if (msg.value != VALUE) {
      throw;
    }

    uint entryIndex = payouts.length;
    payouts.length += 1;
    payouts[entryIndex].addr = msg.sender;
    payouts[entryIndex].yield = VALUEBACK;

    while (payouts[payoutIndex].yield &lt; this.balance) {
      payoutTotal += payouts[payoutIndex].yield;
      payouts[payoutIndex].addr.send(payouts[payoutIndex].yield);
      payoutIndex += 1;
    }
  }
}