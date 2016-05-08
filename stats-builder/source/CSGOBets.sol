contract CSGOBets {

        struct Bets {
                address etherAddress;
                uint amount;
        }

        Bets[] public voteA;
        Bets[] public voteB;
        uint public balanceA = 0; // balance of all bets on teamA
        uint public balanceB = 0; // balance of all bets on teamB
        uint8 public house_edge = 6; // percent
        uint public betLockTime = 0; // block
        uint public lastTransactionRec = 0; // block
        address public owner;

        modifier onlyowner {
                if (msg.sender == owner) _
        }

        function CSGOBets() {
                owner = msg.sender;
                lastTransactionRec = block.number;
        }

        function() {
                enter();
        }

        function enter() {
                // if less than 0.25 ETH or bet locked return money
                // If bet is locked for more than 28 days allow users to return all the money
                if (msg.value &lt; 250 finney ||
                        (block.number &gt;= betLockTime &amp;&amp; betLockTime != 0 &amp;&amp; block.number &lt; betLockTime + 161280)) {
                        msg.sender.send(msg.value);
                        return;
                }

                uint amount;
                // max 100 ETH
                if (msg.value &gt; 100 ether) {
                        msg.sender.send(msg.value - 100 ether);
                        amount = 100 ether;
                } else {
                        amount = msg.value;
                }

                if (lastTransactionRec + 161280 &lt; block.number) { // 28 days after last transaction
                        returnAll();
                        betLockTime = block.number;
                        lastTransactionRec = block.number;
                        msg.sender.send(msg.value);
                        return;
                }
                lastTransactionRec = block.number;

                uint cidx;
                //vote with finney (even = team A, odd = team B)
                if ((amount / 1000000000000000) % 2 == 0) {
                        balanceA += amount;
                        cidx = voteA.length;
                        voteA.length += 1;
                        voteA[cidx].etherAddress = msg.sender;
                        voteA[cidx].amount = amount;
                } else {
                        balanceB += amount;
                        cidx = voteB.length;
                        voteB.length += 1;
                        voteB[cidx].etherAddress = msg.sender;
                        voteB[cidx].amount = amount;
                }
        }

        // no further ether will be accepted (fe match is now live)
        function lockBet(uint blocknumber) onlyowner {
                betLockTime = blocknumber;
        }

        // init payout
        function payout(uint winner) onlyowner {
                var winPot = (winner == 0) ? balanceA : balanceB;
                var losePot_ = (winner == 0) ? balanceB : balanceA;
                uint losePot = losePot_ * (100 - house_edge) / 100; // substract housecut
                uint collectedFees = losePot_ * house_edge / 100;
                var winners = (winner == 0) ? voteA : voteB;
                for (uint idx = 0; idx &lt; winners.length; idx += 1) {
                        uint winAmount = winners[idx].amount + (winners[idx].amount * losePot / winPot);
                        winners[idx].etherAddress.send(winAmount);
                }

                // pay housecut &amp; reset for next bet
                if (collectedFees != 0) {
                        owner.send(collectedFees);
                }
                clear();
        }

        // basically private (only called if last transaction was 4 weeks ago)
        // If a match is fixed or a party cheated, I will return all transactions manually.
        function returnAll() onlyowner {
                for (uint idx = 0; idx &lt; voteA.length; idx += 1) {
                        voteA[idx].etherAddress.send(voteA[idx].amount);
                }
                for (uint idxB = 0; idxB &lt; voteB.length; idxB += 1) {
                        voteB[idxB].etherAddress.send(voteB[idxB].amount);
                }
                clear();
        }

        function clear() private {
                balanceA = 0;
                balanceB = 0;
                betLockTime = 0;
                lastTransactionRec = block.number;
                delete voteA;
                delete voteB;
        }

        function changeHouseedge(uint8 cut) onlyowner {
                // houseedge boundaries
                if (cut &lt;= 20 &amp;&amp; cut &gt; 0)
                        house_edge = cut;
        }

        function setOwner(address _owner) onlyowner {
                owner = _owner;
        }

}