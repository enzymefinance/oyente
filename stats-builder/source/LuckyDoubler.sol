// 0xf767fca8e65d03fe16d4e38810f5e5376c3372a8
// 1.1
contract LuckyDoubler {
//##########################################################
//#### LuckyDoubler: A doubler with random payout order ####
//#### Deposit 1 ETHER to participate                   ####
//##########################################################
//COPYRIGHT 2016 KATATSUKI ALL RIGHTS RESERVED
//No part of this source code may be reproduced, distributed,
//modified or transmitted in any form or by any means without
//the prior written permission of the creator.

    address private owner;
    
    //Stored variables
    uint private balance = 0;
    uint private fee = 5;
    uint private multiplier = 125;

    mapping (address =&gt; User) private users;
    Entry[] private entries;
    uint[] private unpaidEntries;
    
    //Set owner on contract creation
    function LuckyDoubler() {
        owner = msg.sender;
    }

    modifier onlyowner { if (msg.sender == owner) _ }
    
    struct User {
        address id;
        uint deposits;
        uint payoutsReceived;
    }
    
    struct Entry {
        address entryAddress;
        uint deposit;
        uint payout;
        bool paid;
    }

    //Fallback function
    function() {
        init();
    }
    
    function init() private{
        
        if (msg.value &lt; 1 ether) {
             msg.sender.send(msg.value);
            return;
        }
        
        join();
    }
    
    function join() private {
        
        //Limit deposits to 1ETH
        uint dValue = 1 ether;
        
        if (msg.value &gt; 1 ether) {
            
        	msg.sender.send(msg.value - 1 ether);	
        	dValue = 1 ether;
        }
      
        //Add new users to the users array
        if (users[msg.sender].id == address(0))
        {
            users[msg.sender].id = msg.sender;
            users[msg.sender].deposits = 0;
            users[msg.sender].payoutsReceived = 0;
        }
        
        //Add new entry to the entries array
        entries.push(Entry(msg.sender, dValue, (dValue * (multiplier) / 100), false));
        users[msg.sender].deposits++;
        unpaidEntries.push(entries.length -1);
        
        //Collect fees and update contract balance
        balance += (dValue * (100 - fee)) / 100;
        
        uint index = unpaidEntries.length &gt; 1 ? rand(unpaidEntries.length) : 0;
        Entry theEntry = entries[unpaidEntries[index]];
        
        //Pay pending entries if the new balance allows for it
        if (balance &gt; theEntry.payout) {
            
            uint payout = theEntry.payout;
            
            theEntry.entryAddress.send(payout);
            theEntry.paid = true;
            users[theEntry.entryAddress].payoutsReceived++;

            balance -= payout;
            
            if (index &lt; unpaidEntries.length - 1)
                unpaidEntries[index] = unpaidEntries[unpaidEntries.length - 1];
           
            unpaidEntries.length--;
            
        }
        
        //Collect money from fees and possible leftovers from errors (actual balance untouched)
        uint fees = this.balance - balance;
        if (fees &gt; 0)
        {
                owner.send(fees);
        }      
       
    }
    
    //Generate random number between 0 &amp; max
    uint256 constant private FACTOR =  1157920892373161954235709850086879078532699846656405640394575840079131296399;
    function rand(uint max) constant private returns (uint256 result){
        uint256 factor = FACTOR * 100 / max;
        uint256 lastBlockNumber = block.number - 1;
        uint256 hashVal = uint256(block.blockhash(lastBlockNumber));
    
        return uint256((uint256(hashVal) / factor)) % max;
    }
    
    
    //Contract management
    function changeOwner(address newOwner) onlyowner {
        owner = newOwner;
    }
    
    function changeMultiplier(uint multi) onlyowner {
        if (multi &lt; 110 || multi &gt; 150) throw;
        
        multiplier = multi;
    }
    
    function changeFee(uint newFee) onlyowner {
        if (fee &gt; 5) 
            throw;
        fee = newFee;
    }
    
    
    //JSON functions
    function multiplierFactor() constant returns (uint factor, string info) {
        factor = multiplier;
        info = &#39;The current multiplier applied to all deposits. Min 110%, max 150%.&#39;; 
    }
    
    function currentFee() constant returns (uint feePercentage, string info) {
        feePercentage = fee;
        info = &#39;The fee percentage applied to all deposits. It can change to speed payouts (max 5%).&#39;;
    }
    
    function totalEntries() constant returns (uint count, string info) {
        count = entries.length;
        info = &#39;The number of deposits.&#39;;
    }
    
    function userStats(address user) constant returns (uint deposits, uint payouts, string info)
    {
        if (users[user].id != address(0x0))
        {
            deposits = users[user].deposits;
            payouts = users[user].payoutsReceived;
            info = &#39;Users stats: total deposits, payouts received.&#39;;
        }
    }
    
    function entryDetails(uint index) constant returns (address user, uint payout, bool paid, string info)
    {
        if (index &lt; entries.length) {
            user = entries[index].entryAddress;
            payout = entries[index].payout / 1 finney;
            paid = entries[index].paid;
            info = &#39;Entry info: user address, expected payout in Finneys, payout status.&#39;;
        }
    }
    
    
}