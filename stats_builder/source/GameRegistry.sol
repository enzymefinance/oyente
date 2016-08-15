// 0xad87e48d553c2308dccab428537f6d0809593ba4
// 0.0
contract GameRegistry {

    // This struct keeps all data for a Record.
    struct Record {
        // Keeps the address of this record creator.
        address owner;
        // Keeps the time when this record was created.
        uint time;
        // Keeps the index of the keys array for fast lookup
        uint keysIndex;
        string description;
        string url;
    }

    // This mapping keeps the records of this Registry.
    mapping(address =&gt; Record) private records;

    // Keeps the total numbers of records in this Registry.
    uint private numRecords;

    // Keeps a list of all keys to interate the recoreds.
    address[] private keys;

    // The owner of this registry.
    address private owner;

    uint private KEY_HOLDER_SHARE  = 50;
    uint private REGISTRATION_COST = 500 finney;
    uint private TRANSFER_COST     = 0;

    // Constructor
    function GameRegistry() {
        owner = msg.sender;
    }
    
    // public interface to the directory of games
    function theGames(uint rindex) constant returns(address contractAddress, string description, string url, address submittedBy, uint time) {
        Record record = records[keys[rindex]];
        contractAddress = keys[rindex];
        description = record.description;
        url = record.url;
        submittedBy = record.owner;
        time = record.time;
    }

    function settings() constant public returns(uint registrationCost, uint percentSharedWithKeyHolders) {
        registrationCost            = REGISTRATION_COST / 1 finney;
        percentSharedWithKeyHolders = KEY_HOLDER_SHARE;
    }

    function distributeValue() private {
        if (msg.value == 0) {
            return;
        }
        // share value with all key holders
        uint ownerPercentage  = 100 - KEY_HOLDER_SHARE;
        uint valueForRegOwner = (ownerPercentage * msg.value) / 100;
        owner.send(valueForRegOwner);
        uint valueForEachOwner = (msg.value - valueForRegOwner) / numRecords;
        if (valueForEachOwner &lt;= 0) {
            return;
        }
        for (uint k = 0; k &lt; numRecords; k++) {
            records[keys[k]].owner.send(valueForEachOwner);
        }
    }

    // This is the function that actually inserts a record. 
    function addGame(address key, string description, string url) {
        // Only allow registration if received value &gt;= REGISTRATION_COST
        if (msg.value &lt; REGISTRATION_COST) {
            // Return value back to sender.
            if (msg.value &gt; 0) {
                msg.sender.send(msg.value);
            }
            return;
        }
        distributeValue();
        if (records[key].time == 0) {
            records[key].time = now;
            records[key].owner = msg.sender;
            records[key].keysIndex = keys.length;
            keys.length++;
            keys[keys.length - 1] = key;
            records[key].description = description;
            records[key].url = url;

            numRecords++;
        }
    }

    function () { distributeValue(); }

    // Updates the values of the given record.
    function update(address key, string description, string url) {
        // Only the owner can update his record.
        if (records[key].owner == msg.sender) {
            records[key].description = description;
            records[key].url = url;
        }
    }

/*
    // Transfer ownership of a given record.
    function transfer(address key, address newOwner) {
        // Only allow transfer if received value &gt;= TRANSFER_COST
        if (msg.value &lt; TRANSFER_COST) {
            // Return value back to sender
            if (msg.value &gt; 0) {
                msg.sender.send(msg.value);
            }
            return;
        }
        distributeValue();
        if (records[key].owner == msg.sender) {
            records[key].owner = newOwner;
        }
    }
*/

    // Tells whether a given key is registered.
    function isRegistered(address key) private constant returns(bool) {
        return records[key].time != 0;
    }

    function getRecord(address key) private constant returns(address owner, uint time, string description, string url) {
        Record record = records[key];
        owner = record.owner;
        time = record.time;
        description = record.description;
        url = record.url;
    }

    // Returns the owner of the given record. The owner could also be get
    // by using the function getRecord but in that case all record attributes 
    // are returned.
    function getOwner(address key) private constant returns(address) {
        return records[key].owner;
    }

    // Returns the registration time of the given record. The time could also
    // be get by using the function getRecord but in that case all record attributes
    // are returned.
    function getTime(address key) private constant returns(uint) {
        return records[key].time;
    }

    // Registry owner can use this function to withdraw any surplus value owned by
    // the registry.
    function maintain(uint value, uint cost) {
        if (msg.sender == owner) {
            msg.sender.send(value);
            REGISTRATION_COST = cost;
        }
    }

    // Returns the total number of records in this registry.
    function getTotalRecords() private constant returns(uint) {
        return numRecords;
    }

    // This function is used by subcontracts when an error is detected and
    // the value needs to be returned to the transaction originator.
    function returnValue() internal {
        if (msg.value &gt; 0) {
            msg.sender.send(msg.value);
        }
    }

}