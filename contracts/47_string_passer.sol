/***
 *     _    _  ___  ______ _   _ _____ _   _ _____ 
 *    | |  | |/ _ \ | ___ \ \ | |_   _| \ | |  __ \
 *    | |  | / /_\ \| |_/ /  \| | | | |  \| | |  \/
 *    | |/\| |  _  ||    /| . ` | | | | . ` | | __ 
 *    \  /\  / | | || |\ \| |\  |_| |_| |\  | |_\ \
 *     \/  \/\_| |_/\_| \_\_| \_/\___/\_| \_/\____/
 *                                                 
 *   This contract DOES NOT WORK. Dynamically sized types cannot be returned (incl. "string" and "bytes").                                      
 */

contract Descriptor {
    
	function getDescription() constant returns (string){	
		string somevar;
		somevar = "tencharsme"; 
		return somevar;
	}
}

contract StringPasser {

    address creator;
    
    /***
     * 1. Declare a 9x9 map of Tiles
     ***/
    uint8 mapsize = 9;
    Tile[9][9] tiles; 

    struct Tile 
    {
        /***
         * 2. A tile is comprised of the owner, elevation and a pointer to a 
         *      contract that explains what the tile looks like
         ****/
        address owner;
        uint8 elevation;
        Descriptor descriptor;
    }
    
    /***
     * 3. Upon construction, initialize the internal map elevations.
     *      The Descriptors start uninitialized.
     ***/
    function StringPasser(uint8[] incmap) 
    {
        creator = msg.sender;
        uint counter = 0;
        Descriptor nothing;
        for(uint8 y = 0; y < mapsize; y++)
       	{
           	for(uint8 x = 0; x < mapsize; x++)
           	{
           	    tiles[x][y].descriptor = nothing;
           		tiles[x][y].elevation = incmap[counter]; 
           	}	
        }	
    }
    
   /*** 
    * 4. get Description of a tile at x,y
    ***/ 
    function getTileDescription(uint8 x, uint8 y)
    {
    	Descriptor desc = tiles[x][y].descriptor;       // get the descriptor for this tile
    	string anothervar = desc.getDescription();  // get the description from the descriptor
    	
    	// TODO validate the description
    	// TODO convert it to JSON
    	// save it to a variable for constant retrieval elsewhere
    	
    	return; 
    }
    
    /**********
     Standard kill() function to recover funds 
     **********/
    function kill()
    { 
        if (msg.sender == creator)
        {
            suicide(creator);  // kills this contract and sends remaining funds back to creator
        }
    }
}