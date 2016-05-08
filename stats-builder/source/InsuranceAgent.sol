contract InsuranceAgent {
    address public owner;
    event CoinTransfer(address sender, address receiver, uint amount);

    struct Client {
        address addr;
    }

    struct Payment {
        uint amount;
        uint date; // timestamp
    }

    struct Payout {
        bytes32 proof;
        uint amount;
        uint date; // timestamp
        uint veto; // clientId
    }

    mapping (uint =&gt; Payout) public payouts; // clientId -&gt; requested payout
    mapping (uint =&gt; Payment[]) public payments; // clientId -&gt; list of his Payments
    mapping (uint =&gt; Client) public clients; // clientId -&gt; info about Client

    modifier costs(uint _amount) {
        if (msg.value &lt; _amount)
            throw;
        _
    }

    modifier onlyBy(address _account) {
        if (msg.sender != _account)
            throw;
        _
    }

    function InsuranceAgent() {
        owner = msg.sender;
    }

    function newClient(uint clientId, address clientAddr) onlyBy(owner) {
        clients[clientId] = Client({
            addr: clientAddr
        });
    }

    function newPayment(uint clientId, uint timestamp) costs(5000000000000000) {
        payments[clientId].push(Payment({
            amount: msg.value,
            date: timestamp
        }));
    }

    function requestPayout(uint clientId, uint amount, bytes32 proof, uint date, uint veto) onlyBy(owner) {
        // only one payout at the same time for the same client available
        // amount should be in wei
        payouts[clientId] = Payout({
            proof: proof,
            amount: amount,
            date: date,
            veto: veto
        });
    }

    function vetoPayout(uint clientId, uint proverId) onlyBy(owner) {
        payouts[clientId].veto = proverId;
    }

    function payRequstedSum(uint clientId, uint date) onlyBy(owner) {
        if (payouts[clientId].veto != 0) { throw; }
        if (date - payouts[clientId].date &lt; 60 * 60 * 24 * 3) { throw; }
        clients[clientId].addr.send(payouts[clientId].amount);
        delete payouts[clientId];
    }

    function getStatusOfPayout(uint clientId) constant returns (uint, uint, uint, bytes32) {
        return (payouts[clientId].amount, payouts[clientId].date,
                payouts[clientId].veto, payouts[clientId].proof);
    }

    function getNumberOfPayments(uint clientId) constant returns (uint) {
        return payments[clientId].length;
    }

    function getPayment(uint clientId, uint paymentId) constant returns (uint, uint) {
        return (payments[clientId][paymentId].amount, payments[clientId][paymentId].date);
    }

    function getClient(uint clientId) constant returns (address) {
        return clients[clientId].addr;
    }

    function () {
        // This function gets executed if a
        // transaction with invalid data is sent to
        // the contract or just ether without data.
        // We revert the send so that no-one
        // accidentally loses money when using the
        // contract.
        throw;
    }

}