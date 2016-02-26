// Just testing to see if you can have multiple constructors. Nope!

contract MultipleConstructorTest {

    address creator;
    bool first = false;
    bool second = false;

    function MultipleConstructorTest() 
    {
        creator = msg.sender; 								
        first = true;
    }
  
// Having two constructors with same number of arguments (zero, in this case) doesn't work. Won't compile.    
//    function MultipleConstructorTest() private 
//    {
//        second = true; 								
//    }  
  
// Merely setting the second to private doesn't work. Won't compile.    
//    function MultipleConstructorTest() private 
//    {
//        second = true; 								
//    }
	
// Returning a value won't do it, either. Won't compile.	
//    function MultipleConstructorTest() returns (bool) 
//    {
//        second = true;
//    }	

// Adding a parameter doesn't work. Won't compile.
//    function MultipleConstructorTest(bool irrelevantvalue) 
//    {
//        second = true;
//    }
	
	function getFirst() constant returns (bool)
	{
		return first;
	}
	
	function getSecond() constant returns (bool)
	{
		return second;
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
