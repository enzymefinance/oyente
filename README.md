# EtherScope

## Ethereum OpCode Parser

### Dependencies

1. Install [go-ethereum](https://github.com/ethereum/go-ethereum)

2. Install [neo4j](http://neo4j.com/) and set the username and password as follows:

```bash
username: neo4j
password: neo4j
```

### How to use

* Use the disassembler on the required piece of bytecode:

```bash
cat <Input File> | disasm >> <Output File>
```

* Run core.py on the disassembler output:

```bash
python core.py <Output file from disassmbler>
```

* Open [localhost:7474](http://localhost:7474) to open the dashboard.

* Run the following command to view the results:

```
MATCH n RETURN n
```

A set of sample contracts is placed in the *contracts* folder.
