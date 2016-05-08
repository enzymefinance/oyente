// Last is me! Lottery paying the last player
//
// git: https://github.com/lastisme/lastisme.github.io/
// url: http://lastis.me

contract owned {
  address public owner;

  function owned() {
    owner = msg.sender;
  }
  modifier onlyOwner() {
    if (msg.sender != owner) throw;
    _
  }
  function transferOwnership(address newOwner) onlyOwner {
    owner = newOwner;
  }
}

contract LastIsMe is owned {
  event TicketBought(address _from);
  event WinnerPayedTicketBought(address _winner, address _from);

  //constant once constructed
  uint public blocks;
  uint public price;
  ///////////////////////////

  //semi-constant, tweakable with limits after creation
  uint public houseFee;      // THOUSANDTHS
  uint public houseFeeVal;   // houseFee/1000 * price
  uint public refFeeVal;     // half of the house fee val

  uint public lotteryFee;    // THOUSANDTHS
  uint public lotteryFeeVal; // lotteryFee/1000 * price

  address public leftLottery;
  address public rightLottery;
  //////////////////////////////////////////////////

  uint constant MAX_HOUSE_FEE_THOUSANDTHS   = 20;
  uint constant MAX_LOTTERY_FEE_THOUSANDTHS = 40;

  address public lastPlayer;
  uint    public lastBlock;
  uint    public totalWinnings;
  uint    public jackpot;
  uint    public startedAt;

  struct Winners {
    address winner;
    uint jackpot;
    uint timestamp;
  }
  Winners[] public winners;



  function LastIsMe(uint _priceParam, uint _blocksParam) {
    if(_priceParam==0 || _blocksParam==0) throw;
    price  = _priceParam;
    blocks = _blocksParam;
    setHouseFee(10);
    setLotteryFee(40);
    totalWinnings = 0;
    jackpot = 0;
  }

  function buyTicket(address _ref) {
    if( msg.value &gt;= price ) { //ticket bought

      if( msg.value &gt; price ) {
        msg.sender.send(msg.value-price);  //payed more than required =&gt; refund
      }

      if( remaining() == 0 &amp;&amp; lastPlayer != 0x0 ) {  //last player was the winner!
        WinnerPayedTicketBought(lastPlayer,msg.sender);
        winners[winners.length++] = Winners(lastPlayer, jackpot, block.timestamp);
        lastPlayer.send(jackpot);
        totalWinnings=totalWinnings+jackpot;
        startedAt  = block.timestamp;
        lastPlayer = msg.sender;
        lastBlock  = block.number;
        jackpot    = this.balance;
        //I am not paying fee and other lotteries fee if I am the lottery re-starter
      } else {
        TicketBought(msg.sender);
        if(lastPlayer==0x0)   //very first ticket
          startedAt = block.timestamp;

        lastPlayer = msg.sender;
        lastBlock  = block.number;

        if(houseFeeVal&gt;0) {  //house fee could be zero
          if(_ref==0x0) {
            owner.send(houseFeeVal);
          } else {
            owner.send(refFeeVal);
            _ref.send(refFeeVal);
          }
        }

        if(leftLottery!=0x0 &amp;&amp; lotteryFeeVal&gt;0)
          leftLottery.send(lotteryFeeVal);
        if(rightLottery!=0x0 &amp;&amp; lotteryFeeVal&gt;0)
          rightLottery.send(lotteryFeeVal);

        jackpot = this.balance;
      }
    }
  }

  function () {
    buyTicket(0x0);
  }

  function finance() {
  }

  function allData() constant returns (uint _balance, address _lastPlayer, uint _lastBlock, uint _blockNumber, uint _totalWinners, uint _jackpot, uint _price, uint _blocks, uint _houseFee, uint _lotteryFee, address _leftLottery, address _rightLottery, uint _totalWinnings, uint _startedAt) {
    return (this.balance, lastPlayer, lastBlock, block.number, winners.length, jackpot, price, blocks, houseFee, lotteryFee, leftLottery, rightLottery, totalWinnings, startedAt);
  }

  function baseData() constant returns (uint _balance, address _lastPlayer, uint _lastBlock, uint _blockNumber, uint _totalWinners, uint _jackpot, uint _price, uint _blocks, uint _totalWinnings, uint _startedAt) {
    return (this.balance, lastPlayer, lastBlock, block.number, winners.length, jackpot, price, blocks, totalWinnings, startedAt);
  }

  function elapsed() constant returns (uint) {
    return block.number - lastBlock;  //&gt;=0
  }

  function remaining() constant returns (uint) {
    var e=elapsed();
    if(blocks&gt;e)
      return blocks - elapsed() ;
    else
      return 0;
  }

  function totalWinners() constant returns (uint) {
    return winners.length;
  }

  function updateLeftLottery( address _newValue) onlyOwner {
    leftLottery=_newValue;
  }

  function updateRightLottery( address _newValue) onlyOwner {
    rightLottery=_newValue;
  }

  function setLotteryFee(uint _newValue) onlyOwner {
    if( _newValue &gt; MAX_LOTTERY_FEE_THOUSANDTHS ) throw;
    lotteryFee    = _newValue;
    var aThousand = price/1000;
    lotteryFeeVal = aThousand*lotteryFee;
  }

  function setHouseFee(uint _newValue) onlyOwner {
    if( _newValue &gt; MAX_HOUSE_FEE_THOUSANDTHS ) throw;
    houseFee      = _newValue;
    var aThousand = price/1000;
    houseFeeVal   = aThousand*houseFee;
    refFeeVal     = houseFeeVal / 2;
  }
}