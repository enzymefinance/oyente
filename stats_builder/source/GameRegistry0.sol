// 0xc1ce17303ef35c128b499ed091f39008b3a57389
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
    mapping(address =&gt; Record) records;

    // Keeps the total numbers of records in this Registry.
    uint public numRecords;

    // Keeps a list of all keys to interate the recoreds.
    address[] private keys;

    // The owner of this registry.
    address owner;

    uint public REGISTRATION_COST = 100 finney;
    uint public TRANSFER_COST = 10 finney;
    uint public VALUE_DISTRIBUTION_KEY_OWNERS = 50;

    // Constructor
    function GameRegistry() {
        owner = msg.sender;
    }

    function distributeValue() {
        if (msg.value == 0) {
            return;
        }
        uint ownerPercentage = 100 - VALUE_DISTRIBUTION_KEY_OWNERS;
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
    function register(address key, string description, string url) {
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

    // Updates the values of the given record.
    function update(address key, string description, string url) {
        // Only the owner can update his record.
        if (records[key].owner == msg.sender) {
            records[key].description = description;
            records[key].url = url;
        }
    }

    // Unregister a given record
    function unregister(address key) {
        if (records[key].owner == msg.sender) {
            uint keysIndex = records[key].keysIndex;
            delete records[key];
            numRecords--;
            keys[keysIndex] = keys[keys.length - 1];
            records[keys[keysIndex]].keysIndex = keysIndex;
            keys.length--;
        }
    }

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

    // Tells whether a given key is registered.
    function isRegistered(address key) returns(bool) {
        return records[key].time != 0;
    }

    function getRecordAtIndex(uint rindex) returns(address key, address owner, uint time, string description, string url) {
        Record record = records[keys[rindex]];
        key = keys[rindex];
        owner = record.owner;
        time = record.time;
        description = record.description;
        url = record.url;
    }

    function getRecord(address key) returns(address owner, uint time, string description, string url) {
        Record record = records[key];
        owner = record.owner;
        time = record.time;
        description = record.description;
        url = record.url;
    }

    // Returns the owner of the given record. The owner could also be get
    // by using the function getRecord but in that case all record attributes 
    // are returned.
    function getOwner(address key) returns(address) {
        return records[key].owner;
    }

    // Returns the registration time of the given record. The time could also
    // be get by using the function getRecord but in that case all record attributes
    // are returned.
    function getTime(address key) returns(uint) {
        return records[key].time;
    }

    // Returns the total number of records in this registry.
    function getTotalRecords() returns(uint) {
        return numRecords;
    }

    // This function is used by subcontracts when an error is detected and
    // the value needs to be returned to the transaction originator.
    function returnValue() internal {
        if (msg.value &gt; 0) {
            msg.sender.send(msg.value);
        }
    }

    // Registry owner can use this function to withdraw any value owned by
    // the registry.
    function withdraw(uint value) {
        if (msg.sender == owner) {
            msg.sender.send(value);
        }
    }

}