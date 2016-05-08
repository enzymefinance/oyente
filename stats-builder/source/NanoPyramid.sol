contract NanoPyramid {
    
    uint private pyramidMultiplier = 140;
    uint private minAmount = 1 finney;
    uint private maxAmount = 1 ether;
    uint private fee = 2;
    uint private collectedFees = 0;
    uint private minFeePayout = 100 finney;
    
    address private owner;
    
    
    function NanoPyramid() {
        owner = msg.sender;
    }
    
    modifier onlyowner { if (msg.sender == owner) _ }
    
    
    struct Participant {
        address etherAddress;
        uint payout;
    }
    
    Participant[] public participants;
    
    
    uint public payoutOrder = 0;
    uint public balance = 0;
    
    
    function() {
        enter();
    }
    
    function enter() {
        // Check if amount is too small
        if (msg.value &lt; minAmount) {
            // Amount is too small, no need to think about refund
            collectedFees += msg.value;
            return;
        }
        
        // Check if amount is too high
        uint amount;
        if (msg.value &gt; maxAmount) {
            uint amountToRefund =  msg.value - maxAmount;
            if (amountToRefund &gt;= minAmount) {
            	if (!msg.sender.send(amountToRefund)) {
            	    throw;
            	}
        	}
            amount = maxAmount;
        }
        else {
        	amount = msg.value;
        }
        
        //Adds new address to the participant array
        participants.push(Participant(
            msg.sender, 
            amount * pyramidMultiplier / 100
        ));
            
        // Update fees and contract balance
        balance += (amount * (100 - fee)) / 100;
        collectedFees += (amount * fee) / 100;
        
        //Pays earlier participiants if balance sufficient
        while (balance &gt; participants[payoutOrder].payout) {
            uint payoutToSend = participants[payoutOrder].payout;
            participants[payoutOrder].etherAddress.send(payoutToSend);
            balance -= payoutToSend;
            payoutOrder += 1;
        }
        
        // Collect fees
        if (collectedFees &gt;= minFeePayout) {
            if (!owner.send(collectedFees)) {
                // Potentially sending money to a contract that
                // has a fallback function.  So instead, try
                // tranferring the funds with the call api.
                if (owner.call.gas(msg.gas).value(collectedFees)()) {
                    collectedFees = 0;
                }
            } else {
                collectedFees = 0;
            }
        }
    }
    
    
    function totalParticipants() constant returns (uint count) {
        count = participants.length;
    }

    function awaitingParticipants() constant returns (uint count) {
        count = participants.length - payoutOrder;
    }

    function outstandingBalance() constant returns (uint amount) {
        uint payout = 0;
        uint idx;
        for (idx = payoutOrder; idx &lt; participants.length; idx++) {
            payout += participants[idx].payout;
        }
        amount = payout - balance;
    }


    function setOwner(address _owner) onlyowner {
        owner = _owner;
    }
}