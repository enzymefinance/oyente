// Example 1:
// contract TestCall {
//     bytes _tmpCalldata;
//     uint public testArg0;
//     uint public testArg1;
//     function makeTestCall2() {
//         _tmpCalldata.length=64; for(uint i=0;i<64;++i) _tmpCalldata[i]=0xff;
//         TestCall(this).callcode(bytes4(0x0f682008),_tmpCalldata); // 0x0f682008=testCall2(uint256,uint256)
//     }
//     function testCall2(uint arg0,uint arg1) { testArg0=arg0; testArg1=arg1; }
// }

//Example 2:

library Set {
  // We define a new struct datatype that will be used to
  // hold its data in the calling contract.
  struct Data { mapping(uint => bool) flags; }
  // Note that the first parameter is of type "storage
  // reference" and thus only its storage address and not
  // its contents is passed as part of the call.  This is a
  // special feature of library functions.  It is idiomatic
  // to call the first parameter 'self', if the function can
  // be seen as a method of that object.
  function insert(Data storage self, uint value)
      returns (bool)
  {
      if (self.flags[value])
          return false; // already there
      self.flags[value] = true;
      return true;
  }
  function remove(Data storage self, uint value)
      returns (bool)
  {
      if (!self.flags[value])
          return false; // not there
      self.flags[value] = false;
      return true;
  }
  function contains(Data storage self, uint value)
      returns (bool)
  {
      return self.flags[value];
  }
}
contract C {
    Set.Data knownValues;
    function register(uint value) {
        // The library functions can be called without a
        // specific instance of the library, since the
        // "instance" will be the current contract.
        if (!Set.insert(knownValues, value))
            throw;
    }
    // In this contract, we can also directly access knownValues.flags, if we want.
}