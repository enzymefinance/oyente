// 0x3ad14db4e5a658d8d20f8836deabe9d5286f79e1
// 0.0432822634988
/*
  Become the Block King when the last digit of your payment block number
  matches the randaom number received from Oraclize.it.
  The Block King receives 50% of the incoming payments of the warriors who
  fail to push the Block King from the throne.
  Block Kings who paid  1 ether when they
  ascended to the throne get 75% of the incoming payments.
  If the Block King holds their position for more than 2000 blocks
  they receive 90% of the incoming payments.
*/


// &lt;ORACLIZE_API&gt;
/*
Copyright (c) 2015-2016 Oraclize srl, Thomas Bertani



Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the &quot;Software&quot;), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:



The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.



THE SOFTWARE IS PROVIDED &quot;AS IS&quot;, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

contract OraclizeI {
    address public cbAddress;
    function query(uint _timestamp, string _datasource, string _arg) returns (bytes32 _id);
    function query_withGasLimit(uint _timestamp, string _datasource, string _arg, uint _gaslimit) returns (bytes32 _id);
    function query2(uint _timestamp, string _datasource, string _arg1, string _arg2) returns (bytes32 _id);
    function query2_withGasLimit(uint _timestamp, string _datasource, string _arg1, string _arg2, uint _gaslimit) returns (bytes32 _id);
    function getPrice(string _datasource) returns (uint _dsprice);
    function getPrice(string _datasource, uint gaslimit) returns (uint _dsprice);
    function useCoupon(string _coupon);
    function setProofType(byte _proofType);
}
contract OraclizeAddrResolverI {
    function getAddress() returns (address _addr);
}
contract usingOraclize {
    uint constant day = 60*60*24;
    uint constant week = 60*60*24*7;
    uint constant month = 60*60*24*30;
    byte constant proofType_NONE = 0x00;
    byte constant proofType_TLSNotary = 0x10;
    byte constant proofStorage_IPFS = 0x01;
    uint8 constant networkID_mainnet = 1;
    uint8 constant networkID_testnet = 2;
    uint8 constant networkID_morden = 2;
    uint8 constant networkID_consensys = 161;
    
    OraclizeAddrResolverI OAR = OraclizeAddrResolverI(0x1d11e5eae3112dbd44f99266872ff1d07c77dce8);
    
    OraclizeI oraclize;
    modifier oraclizeAPI {
        oraclize = OraclizeI(OAR.getAddress());
        _
    }
    modifier coupon(string code){
        oraclize = OraclizeI(OAR.getAddress());
        oraclize.useCoupon(code);
        _
    }
    function oraclize_setNetwork(uint8 networkID) internal returns(bool){
        if (networkID == networkID_mainnet) OAR = OraclizeAddrResolverI(0x1d11e5eae3112dbd44f99266872ff1d07c77dce8);
        else if (networkID == networkID_testnet) OAR = OraclizeAddrResolverI(0x0ae06d5934fd75d214951eb96633fbd7f9262a7c);
        else if (networkID == networkID_consensys) OAR = OraclizeAddrResolverI(0x20e12a1f859b3feae5fb2a0a32c18f5a65555bbf);
        else return false;
        return true;
    }
    function oraclize_query(string datasource, string arg) oraclizeAPI internal returns (bytes32 id){
        uint price = oraclize.getPrice(datasource);
        if (price &gt; 1 ether + tx.gasprice*200000) return 0; // unexpectedly high price
        return oraclize.query.value(price)(0, datasource, arg);
    }
    function oraclize_query(uint timestamp, string datasource, string arg) oraclizeAPI internal returns (bytes32 id){
        uint price = oraclize.getPrice(datasource);
        if (price &gt; 1 ether + tx.gasprice*200000) return 0; // unexpectedly high price
        return oraclize.query.value(price)(timestamp, datasource, arg);
    }
    function oraclize_query(uint timestamp, string datasource, string arg, uint gaslimit) oraclizeAPI internal returns (bytes32 id){
        uint price = oraclize.getPrice(datasource, gaslimit);
        if (price &gt; 1 ether + tx.gasprice*gaslimit) return 0; // unexpectedly high price
        return oraclize.query_withGasLimit.value(price)(timestamp, datasource, arg, gaslimit);
    }
    function oraclize_query(string datasource, string arg, uint gaslimit) oraclizeAPI internal returns (bytes32 id){
        uint price = oraclize.getPrice(datasource, gaslimit);
        if (price &gt; 1 ether + tx.gasprice*gaslimit) return 0; // unexpectedly high price
        return oraclize.query_withGasLimit.value(price)(0, datasource, arg, gaslimit);
    }
    function oraclize_query(string datasource, string arg1, string arg2) oraclizeAPI internal returns (bytes32 id){
        uint price = oraclize.getPrice(datasource);
        if (price &gt; 1 ether + tx.gasprice*200000) return 0; // unexpectedly high price
        return oraclize.query2.value(price)(0, datasource, arg1, arg2);
    }
    function oraclize_query(uint timestamp, string datasource, string arg1, string arg2) oraclizeAPI internal returns (bytes32 id){
        uint price = oraclize.getPrice(datasource);
        if (price &gt; 1 ether + tx.gasprice*200000) return 0; // unexpectedly high price
        return oraclize.query2.value(price)(timestamp, datasource, arg1, arg2);
    }
    function oraclize_query(uint timestamp, string datasource, string arg1, string arg2, uint gaslimit) oraclizeAPI internal returns (bytes32 id){
        uint price = oraclize.getPrice(datasource, gaslimit);
        if (price &gt; 1 ether + tx.gasprice*gaslimit) return 0; // unexpectedly high price
        return oraclize.query2_withGasLimit.value(price)(timestamp, datasource, arg1, arg2, gaslimit);
    }
    function oraclize_query(string datasource, string arg1, string arg2, uint gaslimit) oraclizeAPI internal returns (bytes32 id){
        uint price = oraclize.getPrice(datasource, gaslimit);
        if (price &gt; 1 ether + tx.gasprice*gaslimit) return 0; // unexpectedly high price
        return oraclize.query2_withGasLimit.value(price)(0, datasource, arg1, arg2, gaslimit);
    }
    function oraclize_cbAddress() oraclizeAPI internal returns (address){
        return oraclize.cbAddress();
    }
    function oraclize_setProof(byte proofP) oraclizeAPI internal {
        return oraclize.setProofType(proofP);
    }



    function parseAddr(string _a) internal returns (address){
        bytes memory tmp = bytes(_a);
        uint160 iaddr = 0;
        uint160 b1;
        uint160 b2;
        for (uint i=2; i&lt;2+2*20; i+=2){
            iaddr *= 256;
            b1 = uint160(tmp[i]);
            b2 = uint160(tmp[i+1]);
            if ((b1 &gt;= 97)&amp;&amp;(b1 &lt;= 102)) b1 -= 87;
            else if ((b1 &gt;= 48)&amp;&amp;(b1 &lt;= 57)) b1 -= 48;
            if ((b2 &gt;= 97)&amp;&amp;(b2 &lt;= 102)) b2 -= 87;
            else if ((b2 &gt;= 48)&amp;&amp;(b2 &lt;= 57)) b2 -= 48;
            iaddr += (b1*16+b2);
        }
        return address(iaddr);
    }


    function strCompare(string _a, string _b) internal returns (int) {
        bytes memory a = bytes(_a);
        bytes memory b = bytes(_b);
        uint minLength = a.length;
        if (b.length &lt; minLength) minLength = b.length;
        for (uint i = 0; i &lt; minLength; i ++)
            if (a[i] &lt; b[i])
                return -1;
            else if (a[i] &gt; b[i])
                return 1;
        if (a.length &lt; b.length)
            return -1;
        else if (a.length &gt; b.length)
            return 1;
        else
            return 0;
   } 

    function indexOf(string _haystack, string _needle) internal returns (int)
    {
    	bytes memory h = bytes(_haystack);
    	bytes memory n = bytes(_needle);
    	if(h.length &lt; 1 || n.length &lt; 1 || (n.length &gt; h.length)) 
    		return -1;
    	else if(h.length &gt; (2**128 -1))
    		return -1;									
    	else
    	{
    		uint subindex = 0;
    		for (uint i = 0; i &lt; h.length; i ++)
    		{
    			if (h[i] == n[0])
    			{
    				subindex = 1;
    				while(subindex &lt; n.length &amp;&amp; (i + subindex) &lt; h.length &amp;&amp; h[i + subindex] == n[subindex])
    				{
    					subindex++;
    				}	
    				if(subindex == n.length)
    					return int(i);
    			}
    		}
    		return -1;
    	}	
    }

    function strConcat(string _a, string _b, string _c, string _d, string _e) internal returns (string){
        bytes memory _ba = bytes(_a);
        bytes memory _bb = bytes(_b);
        bytes memory _bc = bytes(_c);
        bytes memory _bd = bytes(_d);
        bytes memory _be = bytes(_e);
        string memory abcde = new string(_ba.length + _bb.length + _bc.length + _bd.length + _be.length);
        bytes memory babcde = bytes(abcde);
        uint k = 0;
        for (uint i = 0; i &lt; _ba.length; i++) babcde[k++] = _ba[i];
        for (i = 0; i &lt; _bb.length; i++) babcde[k++] = _bb[i];
        for (i = 0; i &lt; _bc.length; i++) babcde[k++] = _bc[i];
        for (i = 0; i &lt; _bd.length; i++) babcde[k++] = _bd[i];
        for (i = 0; i &lt; _be.length; i++) babcde[k++] = _be[i];
        return string(babcde);
    }
    
    function strConcat(string _a, string _b, string _c, string _d) internal returns (string) {
        return strConcat(_a, _b, _c, _d, &quot;&quot;);
    }

    function strConcat(string _a, string _b, string _c) internal returns (string) {
        return strConcat(_a, _b, _c, &quot;&quot;, &quot;&quot;);
    }

    function strConcat(string _a, string _b) internal returns (string) {
        return strConcat(_a, _b, &quot;&quot;, &quot;&quot;, &quot;&quot;);
    }

    // parseInt
    function parseInt(string _a) internal returns (uint) {
        return parseInt(_a, 0);
    }

    // parseInt(parseFloat*10^_b)
    function parseInt(string _a, uint _b) internal returns (uint) {
        bytes memory bresult = bytes(_a);
        uint mint = 0;
        bool decimals = false;
        for (uint i=0; i&lt;bresult.length; i++){
            if ((bresult[i] &gt;= 48)&amp;&amp;(bresult[i] &lt;= 57)){
                if (decimals){
                   if (_b == 0) break;
                    else _b--;
                }
                mint *= 10;
                mint += uint(bresult[i]) - 48;
            } else if (bresult[i] == 46) decimals = true;
        }
        return mint;
    }
    


}
// &lt;/ORACLIZE_API&gt;

contract BlockKing is usingOraclize{

  address public owner;
  address public king;
  address public warrior;
  address public contractAddress;
  uint public rewardPercent;
  uint public kingBlock;
  uint public warriorBlock;
  uint public randomNumber;
  uint public singleDigitBlock;
  uint public warriorGold;

  // this function is executed at initialization
  function BlockKing() {
    owner = msg.sender;
    king = msg.sender;
    warrior = msg.sender;
    contractAddress = this;
    rewardPercent = 50;
    kingBlock = block.number;
    warriorBlock = block.number;
    randomNumber = 0;
    singleDigitBlock = 0;
    warriorGold = 0;
  }

  // fallback function - simple transactions trigger this
  function() {
    enter();
  }
  
  function enter() {
    // 100 finney = .05 ether minimum payment otherwise refund payment and stop contract
    if (msg.value &lt; 50 finney) {
      msg.sender.send(msg.value);
      return;
    }
    warrior = msg.sender;
    warriorGold = msg.value;
    warriorBlock = block.number;
    bytes32 myid = oraclize_query(0, &quot;WolframAlpha&quot;, &quot;random number between 1 and 9&quot;);
  }

  function __callback(bytes32 myid, string result) {
    if (msg.sender != oraclize_cbAddress()) throw;
    randomNumber = uint(bytes(result)[0]) - 48;
    process_payment();
  }
  
  function process_payment() {
    // Check if there is a new Block King
    // by comparing the last digit of the block number
    // against the Oraclize.it random number.
    uint singleDigit = warriorBlock;
	while (singleDigit &gt; 1000000) {
		singleDigit -= 1000000;
	} 
	while (singleDigit &gt; 100000) {
		singleDigit -= 100000;
	} 
	while (singleDigit &gt; 10000) {
		singleDigit -= 10000;
	} 
	while (singleDigit &gt; 1000) {
		singleDigit -= 1000;
	} 
	while (singleDigit &gt; 100) {
		singleDigit -= 100;
	} 
	while (singleDigit &gt; 10) {
		singleDigit -= 10;
	} 
    // Free round for the king
	if (singleDigit == 10) {
		singleDigit = 0;
	} 
	singleDigitBlock = singleDigit;
	if (singleDigitBlock == randomNumber) {
      rewardPercent = 50;
      // If the payment was more than .999 ether then increase reward percentage
      if (warriorGold &gt; 999 finney) {
	  	rewardPercent = 75;
	  }	
      king = warrior;
      kingBlock = warriorBlock;
    }

	uint calculatedBlockDifference = kingBlock - warriorBlock;
	uint payoutPercentage = rewardPercent;
	// If the Block King has held the position for more
	// than 2000 blocks then increase the payout percentage.
	if (calculatedBlockDifference &gt; 2000) {
	  	payoutPercentage = 90;		
	}

    // pay reward to BlockKing
    uint reward = (contractAddress.balance * payoutPercentage)/100;  
    king.send(reward);
    	
    // collect fee
    owner.send(contractAddress.balance);
  }
  function kill() { if (msg.sender == owner) suicide(owner); }
}