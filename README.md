# EtherScope

## Ethereum OpCode Parser

### Dependencies

1. Install [go-ethereum](https://github.com/ethereum/go-ethereum)

2. Install [neo4j](http://neo4j.com/) and set the username and password as follows:

```
username: neo4j
password: neo4j
```

### How to use

2. Use the disassembler on the required piece of bytecode:

```
cat <Input File> | disasm >> <Output File>
```

3. Run core.py on the disassembler output:

```
python core.py <Output file from disassmbler>

4. Open [localhost:7474](http://localhost:7474) to open the dashboard.

5. Run the following command to view the results:

```
MATCH n RETURN n
```


A set of sample contracts is placed in the *contracts* folder.
