// 0x2ef76694fbfd691141d83f921a5ba710525de9b0
// 0.01
// LooneyLottery that pays out the full pool once a day
//
// git: https://github.com/thelooneyfarm/contracts/tree/master/src/lottery
// url: http://the.looney.farm/game/lottery
contract LooneyLottery {
  // modifier for the owner protected functions
  modifier owneronly {
    // yeap, you need to own this contract to action it
    if (msg.sender != owner) {
      throw;
    }

    // function execution inserted here
    _
  }

  // constants for the Lehmer RNG
  uint constant private LEHMER_MOD = 4294967291;
  uint constant private LEHMER_MUL = 279470273;
  uint constant private LEHMER_SDA = 1299709;
  uint constant private LEHMER_SDB = 7919;

  // various game-related constants, also available in the interface
  uint constant public CONFIG_DURATION = 24 hours;
  uint constant public CONFIG_MIN_PLAYERS  = 5;
  uint constant public CONFIG_MAX_PLAYERS  = 222;
  uint constant public CONFIG_MAX_TICKETS = 100;
  uint constant public CONFIG_PRICE = 10 finney;
  uint constant public CONFIG_FEES = 50 szabo;
  uint constant public CONFIG_RETURN = CONFIG_PRICE - CONFIG_FEES;
  uint constant public CONFIG_MIN_VALUE = CONFIG_PRICE;
  uint constant public CONFIG_MAX_VALUE = CONFIG_PRICE * CONFIG_MAX_TICKETS;

  // our owner, stored for owner-related functions
  address private owner = msg.sender;

  // basic initialisation for the RNG
  uint private random = uint(sha3(block.coinbase, block.blockhash(block.number - 1), now));
  uint private seeda = LEHMER_SDA;
  uint private seedb = LEHMER_SDB;

  // we allow 222 * 100 max tickets, allocate a bit more and store the mapping of entry =&gt; address
  uint8[22500] private tickets;
  mapping (uint =&gt; address) private players;

  // public game-related values
  uint public round = 1;
  uint public numplayers = 0;
  uint public numtickets = 0;
  uint public start = now;
  uint public end = start + CONFIG_DURATION;

  // lifetime stats
  uint public txs = 0;
  uint public tktotal = 0;
  uint public turnover = 0;

  // nothing much to do in the constructor, we have the owner set &amp; init done
  function LooneyLottery() {
  }

  // owner withdrawal of fees
  function ownerWithdraw() owneronly public {
    // calculate the fees collected previously (excluding current round)
    uint fees = this.balance - (numtickets * CONFIG_PRICE);

    // return it if we have someting
    if (fees &gt; 0) {
      owner.call.value(fees)();
    }
  }

  // calculate the next random number with a two-phase Lehmer
  function randomize() private {
    // calculate the next seed for the first phase
    seeda = (seeda * LEHMER_MUL) % LEHMER_MOD;

    // adjust the random accordingly, getting extra info from the blockchain together with the seeds
    random ^= uint(sha3(block.coinbase, block.blockhash(block.number - 1), seeda, seedb));

    // adjust the second phase seed for the next iteration
    seedb = (seedb * LEHMER_MUL) % LEHMER_MOD;
  }

  // pick a random winner when the time is right
  function pickWinner() private {
    // do we have &gt;222 players or &gt;= 5 tickets and an expired timer
    if ((numplayers &gt;= CONFIG_MAX_PLAYERS ) || ((numplayers &gt;= CONFIG_MIN_PLAYERS ) &amp;&amp; (now &gt; end))) {
      // get the winner based on the number of tickets (each player has multiple tickets)
      uint winidx = tickets[random % numtickets];
      uint output = numtickets * CONFIG_RETURN;

      // send the winnings to the winner and let the world know
      players[winidx].call.value(output)();
      notifyWinner(players[winidx], output);

      // reset the round, and start a new one
      numplayers = 0;
      numtickets = 0;
      start = now;
      end = start + CONFIG_DURATION;
      round++;
    }
  }

  // allocate tickets to the entry based on the value of the transaction
  function allocateTickets(uint number) private {
    // the last index of the ticket we will be adding to the pool
    uint ticketmax = numtickets + number;

    // loop through and allocate a ticket based on the number bought
    for (uint idx = numtickets; idx &lt; ticketmax; idx++) {
      tickets[idx] = uint8(numplayers);
    }

    // our new value of total tickets (for this round) is the same as max, store it
    numtickets = ticketmax;

    // store the actual player info so we can reference it from the tickets
    players[numplayers] = msg.sender;
    numplayers++;

    // let the world know that we have yet another player
    notifyPlayer(number);
  }

  // we only have a default function, send an amount and it gets allocated, no ABI needed
  function() public {
    // oops, we need at least 10 finney to play :(
    if (msg.value &lt; CONFIG_MIN_VALUE) {
      throw;
    }

    // adjust the random value based on the pseudo rndom inputs
    randomize();

    // pick a winner at the end of a round
    pickWinner();

    // here we store the number of tickets in this transaction
    uint number = 0;

    // get either a max number based on the over-the-top entry or calculate based on inputs
    if (msg.value &gt;= CONFIG_MAX_VALUE) {
      number = CONFIG_MAX_TICKETS;
    } else {
      number = msg.value / CONFIG_PRICE;
    }

    // overflow is the value to be returned, &gt;max or not a multiple of min
    uint input = number * CONFIG_PRICE;
    uint overflow = msg.value - input;

    // store the actual turnover, transaction increment and total tickets
    turnover += input;
    tktotal += number;
    txs += 1;

    // allocate the actual tickets now
    allocateTickets(number);

    // send back the overflow where applicable
    if (overflow &gt; 0) {
      msg.sender.call.value(overflow)();
    }
  }

  // log events
  event Player(address addr, uint32 at, uint32 round, uint32 tickets, uint32 numtickets, uint tktotal, uint turnover);
  event Winner(address addr, uint32 at, uint32 round, uint32 numtickets, uint output);

  // notify that a new player has entered the fray
  function notifyPlayer(uint number) private {
    Player(msg.sender, uint32(now), uint32(round), uint32(number), uint32(numtickets), tktotal, turnover);
  }

  // create the Winner event and send it
  function notifyWinner(address addr, uint output) private {
    Winner(addr, uint32(now), uint32(round), uint32(numtickets), output);
  }
}