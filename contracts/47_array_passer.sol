import "mortal";

// contract Descriptor {
    
// 	function getDescription() constant returns (uint16[3]){	
// 		uint16[3] somevar;
// 		return somevar;
// 	}
// }

contract ArrayPasser is mortal {

    address creator;
    
    /***
     * 1. Declare a 3x3 map of Tiles
     ***/
    uint8 mapsize = 3;
    Tile[3][3] tiles; 

    struct Tile 
    {
        /***
         * 2. A tile is comprised of the owner, elevation and a pointer to a 
         *      contract that explains what the tile looks like
         ****/
        uint8 elevation;
        //Descriptor descriptor;
    }
    
    /***
     * 3. Upon construction, initialize the internal map elevations.
     *      The Descriptors start uninitialized.
     ***/
    function ArrayPasser(uint8[9] incmap) 
    {
        creator = msg.sender;
        uint8 counter = 0;
        for(uint8 y = 0; y < mapsize; y++)
       	{
           	for(uint8 x = 0; x < mapsize; x++)
           	{
           		tiles[x][y].elevation = incmap[counter]; 
           		counter = counter + 1;
           	}	
        }	
    }
   
    /***
     * 4. After contract mined, check the map elevations
     ***/
    function getElevations() constant returns (uint8[3][3])
    {
        uint8[3][3] memory elevations;
        for(uint8 y = 0; y < mapsize; y++)
        {
        	for(uint8 x = 0; x < mapsize; x++)
        	{
        		elevations[x][y] = tiles[x][y].elevation; 
        	}	
        }	
    	return elevations;
    }
}