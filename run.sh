#!/bin/bash
# Author : Loi Luu
if (( "$#" != 2 ))
then
    echo "Usage info:..."
    echo "./run <input_file> <contract_name>"
    echo "for example, run as: ./run foo.sol foo"
	exit 1
fi
echo "Compiling (using the --bin-runtime flag)..."
solc --optimize --bin-runtime "$1" -o ./tmp
echo "Calling the counter..."
echo '' >> ./tmp/"$2".bin-runtime;
echo "Disambling the bytecode";
cat ./tmp/"$2".bin-runtime | disasm > ./tmp/"$2".evm
python symExec.py ./tmp/"$2".evm