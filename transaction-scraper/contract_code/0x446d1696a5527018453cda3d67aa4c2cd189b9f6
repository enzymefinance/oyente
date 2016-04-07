contract GreedPit {
    
    address private owner;
    
    //Stored variables
    uint private balance = 0;
    uint private uniqueUsers = 0;
    uint private usersProfits = 0;
    uint private rescues = 0;
    uint private collectedFees = 0;
    uint private jumpFee = 10;
    uint private baseMultiplier = 110;
    uint private maxMultiplier = 200;
    uint private payoutOrder = 0;
    uint private rescueRecord = 0;
    uint timeOfLastDeposit = now;
    address private hero = 0x0;
    
    mapping (address =&gt; User) private users;
    Entry[] private entries;
    
    event Jump(address who, uint deposit, uint payout);
    event Rescue(address who, address saviour, uint payout);
    event NewHero(address who);
    
    //Set owner on contract creation
    function GreedPit() {
        owner = msg.sender;
    }

    modifier onlyowner { if (msg.sender == owner) _ }
    
    struct User {
        uint id;
        address addr;
        string nickname;
        uint rescueCount;
        uint rescueTokens;
    }
    
    struct Entry {
        address entryAddress;
        uint deposit;
        uint payout;
        uint tokens;
    }

    //Fallback function
    function() {
        init();
    }
    
    function init() private{
        //Only deposits &gt;0.1ETH are allowed to join
        if (msg.value &lt; 100 finney) {
            return;
        }
        
        jumpIn();
        
        //Prevent cheap trolls from reviving the pit if it dies (death = ~3months without deposits)
        if (msg.value &gt; 5)
            timeOfLastDeposit = now;
    }
    
    //Join the pit
    function jumpIn() private {
        
        //Limit deposits to 50ETH
		uint dValue = 100 finney;
		if (msg.value &gt; 50 ether) {
		    //Make sure we receied the money before refunding the surplus
		    if (this.balance &gt;= balance + collectedFees + msg.value)
			    msg.sender.send(msg.value - 50 ether);	
			dValue = 50 ether;
		}
		else { dValue = msg.value; }

        //Add new users to the users array if he&#39;s a new player
        addNewUser(msg.sender);
        
        //Make sure that only up to 5 rescue tokens are spent at a time
        uint tokensToUse = users[msg.sender].rescueTokens &gt;= 5 ? 5 : users[msg.sender].rescueTokens;
        uint tokensUsed = 0;
        
        //Enforce lower payouts if too many people stuck in the pit
        uint randMultiplier = rand(50);
        uint currentEntries = entries.length - payoutOrder;
        randMultiplier = currentEntries &gt; 15 ? (randMultiplier / 2) : randMultiplier;
        randMultiplier = currentEntries &gt; 25 ? 0 : randMultiplier;
        //Incentive to join if the pit is nearly empty (+50% random multiplier)
        randMultiplier = currentEntries &lt;= 5 &amp;&amp; dValue &lt;= 20 ? randMultiplier * 3 / 2 : randMultiplier;
        
        //Calculate the optimal amount of rescue tokens to spend
        while (tokensToUse &gt; 0 &amp;&amp; (baseMultiplier + randMultiplier + tokensUsed*10) &lt; maxMultiplier)
        {
            tokensToUse--;
            tokensUsed++;
        }
        
        uint finalMultiplier = (baseMultiplier + randMultiplier + tokensUsed*10);
        
        if (finalMultiplier &gt; maxMultiplier)
            finalMultiplier = maxMultiplier;
            
        //Add new entry to the entries array    
        if (msg.value &lt; 50 ether)
            entries.push(Entry(msg.sender, msg.value, (msg.value * (finalMultiplier) / 100), tokensUsed));
        else
            entries.push(Entry(msg.sender, 50 ether,((50 ether) * (finalMultiplier) / 100), tokensUsed));

        //Trigger jump event
        if (msg.value &lt; 50 ether)
            Jump(msg.sender, msg.value, (msg.value * (finalMultiplier) / 100));
        else
            Jump(msg.sender, 50 ether, ((50 ether) * (finalMultiplier) / 100));

        users[msg.sender].rescueTokens -= tokensUsed;
        
        //Collect fees and update contract balance
        balance += (dValue * (100 - jumpFee)) / 100;
        collectedFees += (dValue * jumpFee) / 100;
        
        bool saviour = false;
        
        //Pay pending entries if the new balance allows for it
        while (balance &gt; entries[payoutOrder].payout) {
            
            saviour = false;
            
            uint entryPayout = entries[payoutOrder].payout;
            uint entryDeposit = entries[payoutOrder].deposit;
            uint profit = entryPayout - entryDeposit;
            uint saviourShare = 0;
            
            //Give credit &amp; reward for the rescue if the user saved someone else
            if (users[msg.sender].addr != entries[payoutOrder].entryAddress)
            {
                users[msg.sender].rescueCount++;
                //Double or triple token bonus if the user is taking a moderate/high risk to help those trapped
                if (entryDeposit &gt;= 1 ether) {
                    users[msg.sender].rescueTokens += dValue &lt; 20 || currentEntries &lt; 15 ? 1 : 2;
                    users[msg.sender].rescueTokens += dValue &lt; 40 || currentEntries &lt; 25 ? 0 : 1;
                }
                saviour = true;
            }
            
            bool isHero = false;
            
            isHero = entries[payoutOrder].entryAddress == hero;
            
            //Share profit with saviour if the gain is substantial enough and the saviour invested enough (hero exempt)
            if (saviour &amp;&amp; !isHero &amp;&amp; profit &gt; 20 * entryDeposit / 100 &amp;&amp; profit &gt; 100 finney &amp;&amp; dValue &gt;= 5 ether)
            {
                if (dValue &lt; 10 ether)
                   saviourShare = 3 + rand(5);
                else if (dValue &gt;= 10 ether &amp;&amp; dValue &lt; 25 ether)
                  saviourShare = 7 + rand(8);
                else if (dValue &gt;= 25 ether &amp;&amp; dValue &lt; 40 ether)
                   saviourShare = 12 + rand(13);
                else if (dValue &gt;= 40 ether)
                   saviourShare = rand(50);
                   
                saviourShare *= profit / 100;
                   
                msg.sender.send(saviourShare);
            }
            
            uint payout = entryPayout - saviourShare;
            entries[payoutOrder].entryAddress.send(payout);
            
            //Trigger rescue event
            Rescue(entries[payoutOrder].entryAddress, msg.sender, payout);

            balance -= entryPayout;
            usersProfits += entryPayout;
            
            rescues++;
            payoutOrder++;
        }
        
        //Check for new Hero of the Pit
        if (saviour &amp;&amp; users[msg.sender].rescueCount &gt; rescueRecord)
        {
            rescueRecord = users[msg.sender].rescueCount;
            hero = msg.sender;
            //Trigger new hero event
            NewHero(msg.sender);
        }
    }
    
    //Generate random number between 1 &amp; max
    uint256 constant private FACTOR =  1157920892373161954235709850086879078532699846656405640394575840079131296399;
    function rand(uint max) constant private returns (uint256 result){
        uint256 factor = FACTOR * 100 / max;
        uint256 lastBlockNumber = block.number - 1;
        uint256 hashVal = uint256(block.blockhash(lastBlockNumber));
    
        return uint256((uint256(hashVal) / factor)) % max + 1;
    }
    
    function addNewUser(address Address) private
    {
        if (users[Address].addr == address(0))
        {
            users[Address].id = ++uniqueUsers;
            users[Address].addr = Address;
            users[Address].nickname = &#39;UnnamedPlayer&#39;;
            users[Address].rescueCount = 0;
            users[Address].rescueTokens = 0;
        }
    }
    
    //Transfer earnings from fees to the owner
    function collectFees() onlyowner {
        if (collectedFees == 0) throw;

        owner.send(collectedFees);
        collectedFees = 0;
    }

    //Contract management
    function changeOwner(address newOwner) onlyowner {
        owner = newOwner;
    }
    
    function changeBaseMultiplier(uint multi) onlyowner {
        if (multi &lt; 110 || multi &gt; 150) throw;
        
        baseMultiplier = multi;
    }
    
    function changeMaxMultiplier(uint multi) onlyowner {
        if (multi &lt; 200 || multi &gt; 300) throw;
        
        maxMultiplier = multi;
    }
    
    function changeFee(uint fee) onlyowner {
        if (fee &lt; 0 || fee &gt; 10) throw;
        
        jumpFee = fee;
    }
    
    
    //JSON functions
    function setNickname(string name) {
        addNewUser(msg.sender);
        
        if (bytes(name).length &gt;= 2 &amp;&amp; bytes(name).length &lt;= 16)
            users[msg.sender].nickname = name;
    }
    
    function currentBalance() constant returns (uint pitBalance, string info) {
        pitBalance = balance / 1 finney;
        info = &#39;The balance of the pit in Finneys (contract balance minus fees).&#39;;
    }
    
    function heroOfThePit() constant returns (address theHero, string nickname, uint peopleSaved, string info) {
        theHero = hero;  
        nickname = users[theHero].nickname;
        peopleSaved = rescueRecord;
        info = &#39;The current rescue record holder. All hail!&#39;;
    }
    
    function userName(address Address) constant returns (string nickname) {
        nickname = users[Address].nickname;
    }
    
    function totalRescues() constant returns (uint rescueCount, string info) {
        rescueCount = rescues;
        info = &#39;The number of times that people have been rescued from the pit (aka the number of times people made a profit).&#39;;
    }
    
    function multipliers() constant returns (uint BaseMultiplier, uint MaxMultiplier, string info) {
        BaseMultiplier = baseMultiplier;
        MaxMultiplier = maxMultiplier;
        info = &#39;The multipliers applied to all deposits: the final multiplier is a random number between the multpliers shown divided by 100. By default x1.1~x1.5 (up to x2 if rescue tokens are used, granting +0.1 per token). It determines the amount of money you will get when rescued (a saviour share might be deducted).&#39;;
    }
    
    function pitFee() constant returns (uint feePercentage, string info) {
        feePercentage = jumpFee;
        info = &#39;The fee percentage applied to all deposits. It can change to speed payouts (max 10%).&#39;;
    }
    
    function nextPayoutGoal() constant returns (uint finneys, string info) {
        finneys = (entries[payoutOrder].payout - balance) / 1 finney;
        info = &#39;The amount of Finneys (Ethers * 1000) that need to be deposited for the next payout to be executed.&#39;;
    }
    
    function unclaimedFees() constant returns (uint ethers, string info) {
        ethers = collectedFees / 1 ether;
        info = &#39;The amount of Ethers obtained through fees that have not yet been collected by the owner.&#39;;
    }
    
    function totalEntries() constant returns (uint count, string info) {
        count = entries.length;
        info = &#39;The number of times that people have jumped into the pit.&#39;;
    }
    
    function totalUsers() constant returns (uint users, string info) {
        users = uniqueUsers;
        info = &#39;The number of unique users that have joined the pit.&#39;;
    }
    
    function awaitingPayout() constant returns (uint count, string info) {
        count = entries.length - payoutOrder;
        info = &#39;The number of people waiting to be saved.&#39;;
    }
    
    function entryDetails(uint index) constant returns (address user, string nickName, uint deposit, uint payout, uint tokensUsed, string info)
    {
        if (index &lt;= entries.length) {
            user = entries[index].entryAddress;
            nickName = users[entries[index].entryAddress].nickname;
            deposit = entries[index].deposit / 1 finney;
            payout = entries[index].payout / 1 finney;
            tokensUsed = entries[index].tokens;
            info = &#39;Entry info: user address, name, expected payout in Finneys (approximate), rescue tokens used.&#39;;
        }
    }
    
    function userId(address user) constant returns (uint id, string info) {
        id = users[user].id;
        info = &#39;The id of the user, represents the order in which he first joined the pit.&#39;;
    }
    
    function userTokens(address user) constant returns (uint tokens, string info) {
        tokens = users[user].addr != address(0x0) ? users[user].rescueTokens : 0;
        info = &#39;The number of Rescue Tokens the user has. Tokens are awarded when your deposits save people, and used automatically on your next deposit. They provide a 0.1 multiplier increase per token. (+0.5 max)&#39;;
    }
    
    function userRescues(address user) constant returns(uint rescueCount, string info) {
        rescueCount = users[user].addr != address(0x0) ? users[user].rescueCount : 0;
        info = &#39;The number of times the user has rescued someone from the pit.&#39;;
    }
    
    function userProfits() constant returns(uint profits, string info) {
        profits = usersProfits / 1 finney;
        info = &#39;The combined earnings of all users in Finney.&#39;;
    }
    
    //Destroy the contract after ~3 months of inactivity at the owner&#39;s discretion
    function recycle() onlyowner
    {
        if (now &gt;= timeOfLastDeposit + 10 weeks) 
        { 
            //Refund the current balance
            if (balance &gt; 0) 
            {
                entries[0].entryAddress.send(balance);
            }
            
            //Destroy the contract
            selfdestruct(owner);
        }
    }
}