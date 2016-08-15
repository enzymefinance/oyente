// ALPHA 0.1.0 General Purpose Profit Splitter

// INSERT ANYTHING ABOVE 1 FINNEY TO BE A CONTRIBUTOR.
// TO INSERT PROFIT, SEND 1 FINNEY TO THIS CONTRACT FIRST!
// THEN YOU HAVE TO SEND THE PROFIT DIRECTLY AFTER - IN 1 TRANSACTION - WITH THE SAME ADDRESS!

// NO COPYRIGHT, NO FEES, NO OWNER (Only an owner in beta)
// COPY THIS CODE ALL YOU WANT (not my responsibility)

// IF YOU&#39;RE INEXPERIENCED IN CODING, BUT WILLING TO LEARN. I&#39;LL TRY TO DESCRIBE EVERYTHING THE BEST I CAN!
// I&#39;M AN INEXPERIENCED CODER MYSELF.
// YOU CAN TELL, BECAUSE I HAVE NO IDEA HOW VERSION NUMBERS WORK.

contract GeneralPurposeProfitSplitter {         // Title of the contract, you have to give it a name.

    struct Contributor {                        // this will make a database of contributors, the address, contribution and profits are saved.
        address addr;                           // this is the contributors address
        uint index;                             // where does the contributor stand in the database index?
        uint contribution;                      // how much the contributor has contributed in the contract
        uint profit;                            // how much profit the contributor has made, because of the contribution
        uint total;                             // how much does this contributor have in total?
        uint lastContribution;                  // how much did the contributor contribute last time?
        uint lastProfit;                        // how much was the last profit amount?
        uint lastProfitShare;                   // how much share did the contributor have last time profit was distrebuted?
        uint lastPayout;                        // how much did the contributor pay out the last time?
        string error;                           // If there is something wrong you will know
    }
    
    Contributor[] public contributors;          // use contributors[index of contributor].addr/contribution/profit. to get data from that contributor.
    uint contributorFound = 0;                  // if a contributor is found this value turns into an index number later on
    uint contributorTotal = 0;                  // this is a contributors contribution + profits
    uint contributorShare = 0;                  // this is how much that total is in comparison with all contributions
    uint public contributorsIndex = 0;          // this counts how many contributors are in the contract.
    
    uint public totalContributorsContribution = 0;    // this counts how much contribution in total is in the contract.
    uint public totalContributorsProfit = 0;    // this counts how much profits in total is still in the contract.
    uint totalContributorsTotal = 0;            // counts up all the contribution and all the profits now in contract.
    address public beta;                        // Only ME can decide to give all the contributions and profit back to the contributors. LAST RESORT or SCHEDULED!
    address public nextInputProfit;             // IF you inserted 1 finney in the contract first, THEN that address will be saved for the next contract execution.
    
    uint i = 0;                                 // the i gets used to find a contributor for certain functions
    uint correctProfit = 0;                     // Because i take 1 finney away for recognition, I will have to add one later.
    
    function GeneralPurposeProfitSplitter() {   // without this, mist browser doesn&#39;t know how to deploy this contract, as far as I know
        beta = msg.sender;                      // I am the beta-address so I can give ether back if everything goes wrong
    }                                           // ADD two lines of code empty between functions. I don&#39;t know why, but I read it somewhere that you have to.

    
    function() {                                // this function has no name, which means that this function will get triggered when only money gets send
        if (msg.value &lt; 1 finney) {             // DON&#39;T SEND SOMETHING LESS THEN 1 FINNEY TO THIS CONTRACT
            msg.sender.send(msg.value);         // well you can, but this contract will just send it back, all the wasted gas
            throw;                              // and we will pretend it never happened
        }
        
        if (msg.value == 1 finney) {            // IF the value you send to this contract is 1 finney
            nextInputProfit = msg.sender;       // THEN the address will get saved as nextInputProfit, because the next input will be profit
            throw;                              // THEN THE OTHER CONTRACT that provides the profit HAS to send the profit to this contract WITH THE SAME ADDRESS
        }
        
        if (nextInputProfit == msg.sender) {    // IF this is the second time the smartcontract that provides profit insert ether, it checks its address to see if it matches
            nextInputProfit = 0;                // this resets the nextInputProfit to nothing. because the code is now being executed and won&#39;t be executed again, unless it sends 1 finney again.
            correctProfit = msg.value + 1 finney; // this adds the 1 finney that was taken away for code recognition.
            insertProfitHere();                 // GO TO the function that destributes profits.
        }
        else {                                  // IF you&#39;re NOT a profit providing smartcontract and have NOT inserted 1 finney first, then the contract recognizes you as contributor
            for(i; i&lt;contributors.length; i++) {// this will go through ALL contributors untill it has found a matching address (LEARN ABOUT FOR LOOPS ON GOOGLE (if it still exists))
                if (contributors[i].addr == msg.sender) {// If it has found one, it&#39;ll prevent the same contributor added twice
                    contributorFound = i;       // then the number i is the contributors index number.
                    i = contributors.length;    // this will make the for loop stop, to save gas.
                }
            }
            i = 0;                              // resets that i thingy back to zero, because... you know. 
            if (contributorFound &gt; 0) {         // if the contributorsFound is NOT 0, like in the beginning of this contract, that means this is not the first time this address contributed
                contributors[contributorFound].contribution += msg.value; // add the new contribution value to the existing contribution value
                contributors[contributorFound].total = contributorTotal; // for show in Mist Browser
                contributors[contributorFound].lastContribution = msg.value; // for show in Mist Browser
                contributorTotal = contributors[contributorFound].contribution + contributors[contributorFound].profit;   // Counts up the total amount a contributor has
            }
            else {                              // if this is the first time your address contributed here, welcome first of all, and you will be added in the database
                contributors[contributorsIndex].addr = msg.sender; // IF you&#39;re the first contributor, you will get contributorsIndex number 0.
                contributors[contributorsIndex].index = contributorsIndex; // so you know where you stand                
                contributors[contributorsIndex].contribution = msg.value; // your value will now be seen as a contribution, and you will receive profits
                contributors[contributorsIndex].total = msg.value;  // for show in Mist Browser
                contributors[contributorsIndex].lastContribution = msg.value; // for show in Mist Browser
                contributorsIndex += 1;         // add one to the contributors index, no two contributors gets the same index number
            }
            totalContributorsContribution += msg.value;   // If you want to give you&#39;re contributors the correct share of profits, the total contributors amount has to be correct all the time.
        }
    }
    
    
    function insertProfitHere() {               // so if the contract recognizes your input as profit, it executes this function. You can also use the mist browser to add profits.
        totalContributorsTotal = totalContributorsProfit + totalContributorsContribution; // count up everything to calculate shares later on
        i = contributors.length;                // I begin with the last contributor, because last added, first served.
        uint CorrectProfitCounter = correctProfit;  // I need an additional counter to NOT give out too much profit then that there is.
        uint addedProfit;                       //after calculating shares, addedProfit is the amount one contributor gets.
        uint errorBelow = 0;                    // in case there is not enought profit to share around, if it happens, something went wrong.
            for(i; i &gt;= 0; i--) {               // this gathers all the contributors one by one, starting with the last contributor
            contributorTotal = contributors[i].contribution + contributors[i].profit;   // Counts up the total amount a contributor has
            contributorShare = contributorTotal / totalContributorsTotal;  // compares it with the amount of all contribution
            addedProfit = contributorShare / correctProfit;    // the contract gives the contributor the fair share in comparison of the rest of all the contributors
            CorrectProfitCounter -= addedProfit;// I don&#39;t want the contract balance to be below zero, because of miscalculations, so I keep subtracting to check
            if (CorrectProfitCounter &gt; 0){      // if there is still enough profit to share, share it. If it doesn&#39;t, then something went wrong.
                contributors[i].profit += addedProfit;  // add the profit to the contributors database index
                totalContributorsProfit += addedProfit; // also add that same amount to the total of all contributors
                contributors[i].lastProfit = addedProfit; // Also for show in the Mist browser                
            }
            else {                              // if this code gets executes, then something went wrong and the duped ones get notified
                errorBelow = i;                 // let&#39;s hope this never happens
                i = 0;                          // this makes the for loop stop
            }
        }
        if (errorBelow &gt;= 0){                   // something went wrong, we have to tell the duped about it quick!
            for(errorBelow; errorBelow &gt; 0; errorBelow--) { // for loop to tell the ones who are duped that something went wrong
                contributors[errorBelow].error = &quot;Please cash all out and recontribute to continue getting profit&quot;; // haha quickfix
            }
        }
    }

    
    function cashOutProfit() {                  // This is the best part for contributors
        for(i; i&lt;contributors.length; i++) {    // for loop again to search you up
            if (contributors[i].addr == msg.sender) {   // see if it matches
                contributorFound = i;           // we found you
                i = contributors.length;        // stop the for loop
                msg.sender.send(contributors[contributorFound].profit); // send the profits you&#39;ve earned
                totalContributorsProfit -= contributors[contributorFound].profit;   // remove the profits from the total to correctly calculate shares in the future
                contributors[contributorFound].profit = 0;  // if you&#39;ve cashed all your profit out, you have no more profit in the contract
            }
            
        }
        i = 0;                                  // this might be unnessecary, but who cares
    }
    
    
    function cashAllOut() {                     // this is when you want to stop getting profits as well
        for(i; i&lt;contributors.length; i++) {    // for loop to search you up
            if (contributors[i].addr == msg.sender) {   // match or no?
                contributorFound = i;           // tadaaaa
                i = contributors.length;        // stop the for loop please
                contributorTotal = contributors[contributorFound].contribution + contributors[contributorFound].profit; // count all your funds up
                msg.sender.send(contributorTotal);  // and send it back to you, have fun
                totalContributorsContribution -= contributors[contributorFound].contribution;   // to correct shares later
                contributors[contributorFound].contribution = 0;    // all gone, because you cashed out
                totalContributorsProfit -= contributors[contributorFound].profit;   // to correct the shares later also
                contributors[contributorFound].profit = 0;  // no profit if you&#39;ve asked for it
            }
            
        }
        i = 0;                                  // This is the end I guess
    }
    
    
//------------------------------------------------------------------------------
//------ALPHA/BETA FUNCTIONS ONLY-----------------------------------------------
//------------------------------------------------------------------------------
    function giveAllBack() {                    // TIME TO YELL SCAM!
        if (beta == msg.sender) {               // checks if the address executing this function is also the owner, to be sure
            for(i; i&lt;contributors.length; i++) {// ow nevermind..
                contributorTotal = contributors[i].contribution + contributors[i].profit;   // count up how much the contributors have individually
                contributors[i].addr.send(contributorTotal);    // aaaand send it back
                contributors[i].contribution = 0; // reset all the balances
                totalContributorsContribution = 0;   // balance reset
                contributors[i].profit = 0; // never had a reset to serious
                totalContributorsProfit = 0;    // balance reset
            }
            i = 0;                              // search function stuff
        }
    }
    

    function giveContributionsBackProfitBugged() {  // Yeah now you can yell scam!
        if (beta == msg.sender) {               // checks if the address executing this function is also the owner, or else everyone can do this
            for(i; i&lt;contributors.length; i++) {    // get all the contributors
                contributorTotal = contributors[i].contribution;    // only give back all user contribution
                contributors[i].contribution = 0; // reset everything
                contributors[i].addr.send(contributorTotal); // Yeah so the contract now only has claimable profits left
            }
            i = 0;                              // at least I tried making this smartcontract
        }
    }


    function Fokitol() {                        // scream scam NOW!! If you don&#39;t, people will be baited and the world as we know it will end!!
        if (beta == msg.sender) {               // is it the deployer?
            beta.send(this.balance);            // send him everything, which is super lame to do if there are other people contributing as well.
        }
    }
    
}