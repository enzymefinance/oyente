contract Token {
    event Transfer(address indexed from, address indexed to, uint256 value);
    function transfer(address _to, uint256 _value);
    function balanceOf(address) returns (uint256);
}

contract owned {
    address public owner;

    function owned() {
        owner = msg.sender;
    }

    modifier onlyOwner {
        if (msg.sender != owner) throw;
        _
    }

    function transferOwnership(address newOwner) onlyOwner {
        owner = newOwner;
    }
}

contract TokenSale is owned {

	address public asset;
	uint256 public price;

	function TokenSale()
	{
	      asset =  0xE0B7927c4aF23765Cb51314A0E0521A9645F0E2A; // DGX
	      price = 750000000; // 0.75 ETH
	}


	function transfer_token(address _token, address _to, uint256 _value)
	onlyOwner()
	{
		Token(_token).transfer(_to,_value);
	}

	function transfer_eth(address _to, uint256 _value)
	onlyOwner()
	{
		if(this.balance &gt;= _value) {
                    _to.send(_value);
                }
	}

   	function () {

		uint order   = msg.value / price;

		if(order == 0) throw;
		
		uint256 balance = Token(asset).balanceOf(address(this));

		if(balance == 0) throw;

		if(order &gt; balance )
		{
		    order = balance;
		    uint256 change = msg.value - order * price;
		    msg.sender.send(change);
		}

		Token(asset).transfer(msg.sender,order);
    	}
}