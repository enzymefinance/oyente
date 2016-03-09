/* 
	The following is an extremely basic example of a solidity contract. 
	It takes a string upon creation and then repeats it when greet() is called.
*/

contract Greeter         // The contract definition. A constructor of the same name will be automatically called on contract creation. 
{
    address creator;
    // At first, an empty "address"-type variable of the name "owner".
    // Will be set in the constructor.
    string greeting;
    // At first, an empty "string"-type variable of the name "greeting".
    // Will be set in constructor and can be changed.

    function Greeter(string _greeting)
    // The constructor. It accepts a string input and saves it to
    // the contract's "greeting" variable.
    {
        creator = msg.sender;
        greeting = _greeting;
    }
}

// Is public or private default?
// constant returns
// implicit arguments