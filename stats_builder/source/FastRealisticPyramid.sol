// 0x19a6067538c90973ef5dc31ded5fa567f3d09059
// 0.0
contract FastRealisticPyramid {

        struct Person {
                address etherAddress;
                uint amount;
        }

        Person[] public person;

        uint public payoutIdx = 0;
        uint public collectedFees;
        uint public balance = 0;

        address public owner;

        modifier onlyowner {
                if (msg.sender == owner) _
        }


        function FastRealisticPyramid() {
                owner = msg.sender;
        }


        function() {
                enter();
        }

        function enter() {
                if (msg.value &lt; 1/100 ether || msg.value &gt; 50) {
                        msg.sender.send(msg.value);
                        return;
                }


                uint idx = person.length;
                person.length += 1;
                person[idx].etherAddress = msg.sender;
                person[idx].amount = msg.value;


                if (idx != 0) {
                        collectedFees += msg.value / 10;
                        balance += msg.value;
                } else {

                        collectedFees += msg.value;
                }


                if (balance &gt; person[payoutIdx].amount * 7/5) {
                        uint transactionAmount = 7/5 * (person[payoutIdx].amount - person[payoutIdx].amount / 10);
                        person[payoutIdx].etherAddress.send(transactionAmount);

                        balance -= person[payoutIdx].amount * 7/5;
                        payoutIdx += 1;
                }
        }

        function collectFees() onlyowner {
                if (collectedFees == 0) return;

                owner.send(collectedFees);
                collectedFees = 0;
        }

        function setOwner(address _owner) onlyowner {
                owner = _owner;
        }
}