// 0xf05782932dbabde1d657a5311fc3b78db81c60e7
// 0.0
/*
Copyright (c) 2015-2016 Oraclize srl, Thomas Bertani
*/

contract OraclizeAddrResolverI{
    function getAddress() returns (address _addr);
}


contract Oraclize {
    
    mapping (address =&gt; uint) reqc;
    
    address public cbAddress = 0x26588a9301b0428d95e6fc3a5024fce8bec12d51;
    
    byte constant proofType_NONE = 0x00;
    byte constant proofType_TLSNotary = 0x10;
    byte constant proofStorage_IPFS = 0x01;
    
    event Log1(address sender, bytes32 cid, uint timestamp, string datasource, string arg, uint gaslimit, byte proofType);
    event Log2(address sender, bytes32 cid, uint timestamp, string datasource, string arg1, string arg2, uint gaslimit, byte proofType);
    
    address owner;
    
    function(){
        msg.sender.send(msg.value);
    }
    
    function Oraclize() {
        owner = msg.sender;
    }
    
    function addDSource(string dsname, uint multiplier) {
        addDSource(dsname, 0x00, multiplier);
    }

    function addDSource(string dsname, byte proofType, uint multiplier) {
        if ((msg.sender != owner)&amp;&amp;(msg.sender != cbAddress)) throw;
        bytes32 dsname_hash = sha3(dsname, proofType);
        dsources[dsources.length++] = dsname_hash;
        price_multiplier[dsname_hash] = multiplier;
    }

    modifier costs(string datasource, uint gaslimit) {
        uint price = getPrice(datasource, gaslimit, msg.sender);
        if (msg.value &gt;= price){
            address(0xf65b3b60010d57d0bb8478aa6ced15fe720621b4).send(price);
            uint diff = msg.value - price;
            if (diff &gt; 0) msg.sender.send(diff);
            _
        } else throw;
    }

    mapping (address =&gt; byte) addr_proofType;
    uint baseprice;
    mapping (bytes32 =&gt; uint) price;
    mapping (bytes32 =&gt; uint) price_multiplier;
    bytes32[] dsources;

    mapping (bytes32 =&gt; bool) coupons;
    bytes32 coupon;
    
    function createCoupon(string _code){
        if ((msg.sender != owner)&amp;&amp;(msg.sender != cbAddress)) throw;
        coupons[sha3(_code)] = true;
    }
    
    function deleteCoupon(string _code){
        if ((msg.sender != owner)&amp;&amp;(msg.sender != cbAddress)) throw;
        coupons[sha3(_code)] = false;
    }
    
    function useCoupon(string _coupon){
        coupon = sha3(_coupon);
    }
    
    function setProofType(byte _proofType){
        addr_proofType[msg.sender] = _proofType;
    }
    
    function getPrice(string _datasource) public returns (uint _dsprice) {
        return getPrice(_datasource, msg.sender);
    }
    
    function getPrice(string _datasource, uint _gaslimit) public returns (uint _dsprice) {
        return getPrice(_datasource, _gaslimit, msg.sender);
    }
    
    function getPrice(string _datasource, address _addr) private returns (uint _dsprice) {
        return getPrice(_datasource, 200000, _addr);
    }
    
    uint gasprice  = 50000000000;
    
    function setGasPrice(uint newgasprice){
        if ((msg.sender != owner)&amp;&amp;(msg.sender != cbAddress)) throw;
        gasprice = newgasprice;
    }
    
    function getPrice(string _datasource, uint _gaslimit, address _addr) private returns (uint _dsprice) {
        if ((_gaslimit &lt;= 200000)&amp;&amp;(reqc[_addr] == 0)) return 0;
        if ((coupon != 0)&amp;&amp;(coupons[coupon] == true)) return 0;
        _dsprice = price[sha3(_datasource, addr_proofType[_addr])];
        _dsprice += _gaslimit*gasprice;
        return _dsprice;
    }
    
    function setBasePrice(uint new_baseprice){ //0.001 usd in ether
        if ((msg.sender != owner)&amp;&amp;(msg.sender != cbAddress)) throw;
        baseprice = new_baseprice;
        for (uint i=0; i&lt;dsources.length; i++) price[dsources[i]] = new_baseprice*price_multiplier[dsources[i]];
    }

    function setBasePrice(uint new_baseprice, bytes proofID){ //0.001 usd in ether
        if ((msg.sender != owner)&amp;&amp;(msg.sender != cbAddress)) throw;
        baseprice = new_baseprice;
        for (uint i=0; i&lt;dsources.length; i++) price[dsources[i]] = new_baseprice*price_multiplier[dsources[i]];
    }
    
    function query(string _datasource, string _arg) returns (bytes32 _id){
        return query1(0, _datasource, _arg, 200000);
    }
    
    function query1(string _datasource, string _arg) returns (bytes32 _id){
        return query1(0, _datasource, _arg, 200000);
    }
    
    function query2(string _datasource, string _arg1, string _arg2) returns (bytes32 _id){
        return query2(0, _datasource, _arg1, _arg2, 200000);
    }
    
    function query(uint _timestamp, string _datasource, string _arg) returns (bytes32 _id){
        return query1(_timestamp, _datasource, _arg, 200000);
    }
    
    function query1(uint _timestamp, string _datasource, string _arg) returns (bytes32 _id){
        return query1(_timestamp, _datasource, _arg, 200000);
    }
    
    function query2(uint _timestamp, string _datasource, string _arg1, string _arg2) returns (bytes32 _id){
        return query2(_timestamp, _datasource, _arg1, _arg2, 200000);
    }
    
    function query(uint _timestamp, string _datasource, string _arg, uint _gaslimit) returns (bytes32 _id){
        return query1(_timestamp, _datasource, _arg, _gaslimit);
    }
    
    function query1(uint _timestamp, string _datasource, string _arg, uint _gaslimit) costs(_datasource, _gaslimit) returns (bytes32 _id){
	if ((_timestamp &gt; now+3600*24*60)||(_gaslimit &gt; 3141592)) throw;
        _id = sha3(uint(this)+uint(msg.sender)+reqc[msg.sender]);
        reqc[msg.sender]++;
        Log1(msg.sender, _id, _timestamp, _datasource, _arg, _gaslimit, addr_proofType[msg.sender]);
        return _id;
    }
    
    function query2(uint _timestamp, string _datasource, string _arg1, string _arg2, uint _gaslimit) costs(_datasource, _gaslimit) returns (bytes32 _id){
	if ((_timestamp &gt; now+3600*24*60)||(_gaslimit &gt; 3141592)) throw;
        _id = sha3(uint(this)+uint(msg.sender)+reqc[msg.sender]);
        reqc[msg.sender]++;
        Log2(msg.sender, _id, _timestamp, _datasource, _arg1, _arg2, _gaslimit, addr_proofType[msg.sender]);
        return _id;
    }
    
    function query_withGasLimit(uint _timestamp, string _datasource, string _arg, uint _gaslimit) returns (bytes32 _id){
        return query(_timestamp, _datasource, _arg, _gaslimit);
    }
    
    function query1_withGasLimit(uint _timestamp, string _datasource, string _arg, uint _gaslimit) returns (bytes32 _id){
        return query1(_timestamp, _datasource, _arg, _gaslimit);
    }
    
    function query2_withGasLimit(uint _timestamp, string _datasource, string _arg1, string _arg2, uint _gaslimit) returns (bytes32 _id){
        return query2(_timestamp, _datasource, _arg1, _arg2, _gaslimit);
    }                      
    
}