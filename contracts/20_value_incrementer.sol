// This contract demonstrates a simple non-constant (transactional) function you can call from geth.
// increment() takes no parameters and merely increments the "iteration" value. 

contract Incrementer {

    address creator;
    uint iteration;

    function Incrementer() public 
    {
        creator = msg.sender; 
        iteration = 0;
    }

    function increment() 
    {
        iteration = iteration + 1;
    }
    
    function getIteration() constant returns (uint) 
    {
        return iteration;
    }
    
    /**********
     Standard kill() function to recover funds 
    **********/
    
    function kill() 
    { 
        if (msg.sender == creator)
            suicide(creator);  // kills this contract and sends remaining funds back to creator
    }
    
}