// 0x56705bc85a98853ee2df3834d2b3079cdfed87d8
// 0.0
contract ConsultingHalf {
    /*
     *  This contract accepts payment from clients, and payout to engineer and manager.
     */
    address public engineer;
    address public manager;
    uint public createdTime;
    uint public updatedTime;

    function ConsultingHalf(address _engineer, address _manager) {
        engineer = _engineer;
        manager = _manager;
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