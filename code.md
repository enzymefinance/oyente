# Code Structure

*oyente.py*

This is the main entry point to the program. Oyente is able to analyze smart contracts via the following inputs 
- solidity program
- evm bytecode
- remote contracts

Other configuration options include getting the input state, setting timeouts for z3, etc. (Check ```python oyente.py --help``` or ```global_params.py```  for the full list of configuration options available). 
These options are collated and set in the *global_params* module which will be used during the rest of the execution. 

The contracts are then disassembled into opcodes using the ```evm disasm``` command. 

After this, the symexec module is called with the disassembled file which carries out the analyses of the contracts for various vulnerabilities (TOD, timestamp-dependence, mishandled exceptions). 

*symexec.py*

The analysis starts off with the ```build_cfg_and_analyze``` function. We break up the disasm file created by oyente.py into tokens using the native tokenize python module. 

The *collect_vertices* and *construct_bb* functions identify the basic blocks in the program and we store them as vertices. Basic blocks are identified by using opcodes like ```JUMPDEST```, ```STOP```, ```RETURN```, ```SUICIDE```, ```JUMP``` and ```JUMPI``` as separators. Each basic block is backed by an instance of BasicBlock class defined in basicblock.py

After the basic blocks are created, we start to symbolically execute each basic block with the full_sym_exec function. We get the instructions stored in each basic block and execute each of them symbolically via the sym_exec_ins function. In this function, we model each opcode as closely as possible to the behaviour described in the ethereum yellow paper. After this, add this basic block to the list of already visited blocks and follow it to the next basic block. We also maintain the necessary path conditions required to get to the block in the ```path_conditions_and_vars``` variable. In case of instructions like JUMP, there is only one basic block to follow the program execution to. In other cases like ```JUMPI```, we first check if the branch expression is provably True or False using z3. If not, we explore both the branches by adding the branch expression and the negated branch expression to the ```path_conditions_and_vars``` variable. 

- Callstack attack
Checking for the callstack attack is done by the *check_callstack_attack* function. If a ```CALL``` or a ```CALLCODE``` instruction is found without a ```ISZERO``` opcode following it, we flag it as being vulnerable to the callstack attack. 

- Timestamp dependence attack
We find out if the ```path_conditions``` variable contains the symbolic variable corresponding to the block timestamp. If so, the program can be concluded to take a path in the program which makes use of the block timestamp, making it vulnerable to the Timestamp dependence attack. 

- Reentrancy bug


- Concurrency bug

*vargenerator.py*

This is a utility class to provide unqiue symbolic variables required for analysis

*analysis.py*
