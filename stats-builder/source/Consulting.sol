contract Consulting {
    /*
     *  This contract accepts payment from clients, and payout to engineer and manager.
     */
    address public engineer;
    address public manager;
    uint public createdTime;
    uint public updatedTime;

    function Consulting(address _engineer, address _manager) {
        engineer = 0x2207bD0174840f4C728c0B07DE9bDD643Ee2E7d6;
        manager = 0xddd31eb39d56d51b50172884bd2b88e1f6264f95;
        createdTime = block.timestamp;
        updatedTime = block.timestamp;
    }

    /* Contract payout hald */
    function payout() returns (bool _success) {
        if(msg.sender == engineer || msg.sender == manager) {
             engineer.send(this.balance / 2);
             manager.send(this.balance);
             updatedTime = block.timestamp;
             _success = true;
        }else{
            _success = false;
        }
    }
}