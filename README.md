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

Simply run

```
./run.sh <input_file> <contract_name>
```

in which `<input_file>` is a solidity file and `<contract_name>` is the name of the smart contract you are going to analyse. Each solidty file may contain several contracts.

#### V2

V2 implements streamlining operations along with source code tagging. To execute, just run

```bash
./runv2.sh <input_file> <output_file>
```

#### Bash script in detail
* Compile using the `--bin-runtime` flag

```bash
solc -o [Dest] --optimize --bin-runtime [Sourcefile]
```

* Append a new line

```
echo '' >> File
```

* Use the disassembler on the required piece of bytecode:

```bash
cat [Input File] | disasm > [Output File]
```

* Run core.py on the disassembler output:

```bash
python buildCFG.py [Output file from disassmbler]
```

#### Visualize the graph with neo4j
* Open [localhost:7474](http://localhost:7474) to open the dashboard.

* Run the following command to view the results:

```
MATCH n RETURN n
```

* To remove graph database (please copy and paste)

```
MATCH (n)
OPTIONAL MATCH (n)-[r]-()
DELETE n,r
```

A set of sample contracts is placed in the *contracts* folder.


#### Symbolic Execution (SE)

Get Z3 distribution from https://github.com/Z3Prover/z3/releases

Extract, then include the path to the bin directory to your $PYTHONPATH environment variable

To perform SE, run

```
python symExec.py <bytecode file>
```

Currently, SE already captures some money flows. At the end,
the program will output them for investigation. Please refine.


#### TESTING, using evm command from go-ethereum

```
evm --code [runtime-binary] --gas 10000 --price 0 --dump --debug
```


We can also specify the input data.

