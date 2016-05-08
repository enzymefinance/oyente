contract IOU {
    address owner;

/* Public variables of the token */
    string public name;
    string public symbol;
    uint8 public decimals;
    
/* This creates an array with all balances */
    mapping (address => uint256) public balanceOf;

/* This generates a public event on the blockchain that will notify clients */
event Transfer(address indexed from, address indexed to, uint256 value);

    function IOU(string tokenName, string tokenSymbol, uint8 decimalUnits) {
        owner = msg.sender;                                 // sets main RipplePay contract as owner
        name = tokenName;                                       // Set the name for display purposes     
        symbol = tokenSymbol;                                     // Set the symbol for display purposes    
        decimals = decimalUnits;                                       // Amount of decimals for display purposes        
    
    }
    
    /* update balances so they display in ethereum-wallet */
    function transfer(address _from, address _to, uint256 _value) {
        if(msg.sender != owner) throw;                       // can only be invoked by main RipplePay contract
        balanceOf[_from] -= _value;                     // Subtract from the sender
        balanceOf[_to] += _value;                            // Add the same to the recipient
        Transfer(msg.sender, _to, _value);                   // Notify anyone listening that this transfer took place
    }
    
}



contract RipplePayMain {

mapping(string => address) currencies;

function newCurrency(string currencyName, string currencySymbol, uint8 decimalUnits){
currencies[currencySymbol] = new IOU(currencyName, currencySymbol, decimalUnits);
}

function issueIOU(string _currency, uint256 _amount, address _to){
    // update creditLines in main contract, then update balances in IOU contract to display in ethereum-wallet
    IOU(currencies[_currency]).transfer(msg.sender, _to, _amount);

}

}