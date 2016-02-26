/***
 *     _    _  ___  ______ _   _ _____ _   _ _____ 
 *    | |  | |/ _ \ | ___ \ \ | |_   _| \ | |  __ \
 *    | |  | / /_\ \| |_/ /  \| | | | |  \| | |  \/
 *    | |/\| |  _  ||    /| . ` | | | | . ` | | __ 
 *    \  /\  / | | || |\ \| |\  |_| |_| |\  | |_\ \
 *     \/  \/\_| |_/\_| \_\_| \_/\___/\_| \_/\____/
 *                                                 
 *   This contract DOES NOT WORK. It was/is an experiment
 *   to try and manually convert a fixed byte array (e.g. byte4)
 *   into byte[4] using hard maths. A strange thing happened: 
 *   Filling the byte[4] array doesn't work. See below. 9/20/2015
 *                                
 */

contract Bytes4ToByteArrayWithLength4 {

    address creator;

    function Bytes4ToByteArrayWithLength4() {
        creator = msg.sender;
    }
    
    uint digit = 0;
    byte b0 = 0;
    byte b1 = 0;
    byte b2 = 0;
    byte b3 = 0;
    byte[4] finalbytes;

    function convertBytes4ToArray(bytes4 _a) public {
        uint buint = uint(_a);
        uint x = 0;
        uint prevhead = 0;
        uint tail = 0;
        uint powervar = 0;
        uint buintminusphat = 0; // phat = prevhead and tail
        uint numbytes = 4;
        while(x < numbytes)
        {
            powervar= (16 ** ((numbytes*2) - 2 - (x*2)));
            tail = buint % powervar;
            buintminusphat = ((buint - prevhead) - tail);
            digit = buintminusphat / powervar;
            prevhead = buint - tail;
            finalbytes[x] = byte(digit); // this fills first value, but not the last 3
            
            // To prove what digit is for all 4 iterations...
            if(x == 0)
                b0 = byte(digit);
            else if(x == 1)
                b1 = byte(digit);
            else if(x == 2)
                b2 = byte(digit);
            else
                b3 = byte(digit);
                
            x++;
        }
    }
    
    function getDigit() public constant returns (uint) {
        return digit;
    }
    
    function getFinalBytes() public constant returns (byte[4]) {
        return finalbytes;
    }
    
    // retrieve digit manually for all 4 iterations
    function getB0() public constant returns (byte) {
        return b0;
    }
     
    function getB1() public constant returns (byte) {
        return b1;
    }
     
    function getB2() public constant returns (byte) {
        return b2;
    }
     
    function getB3() public constant returns (byte) {
        return b3;
    }
    
    /**********
     Standard kill() function to recover funds 
     **********/

    function kill() {
        if (msg.sender == creator) {
            suicide(creator); // kills this contract and sends remaining funds back to creator
        }
    }
}

/*
> bytes4tobytearraywithlength4.convertBytes4ToArray.sendTransaction(0xcf684dfb, {from:eth.coinbase,gas:3000000});
"0xe87fa6010badff0694c50aedc108f6c6b90c254a66b133f2726f82cd5840c0b0"
> bytes4tobytearraywithlength4.getB0();
"0xcf"
> bytes4tobytearraywithlength4.getB1();
"0x68"
> bytes4tobytearraywithlength4.getB2();
"0x4d"
> bytes4tobytearraywithlength4.getB3();
"0xfb"
> bytes4tobytearraywithlength4.getFinalBytes();
["0xcf", "0x00", "0x00", "0x00"]
*/