#!/bin/bash
# Author : still mostly Loi Luu 
if (( "$#" != 2 ))
then
    echo "Usage info:..."
    echo "./run <source_file> <output>"
    echo "for example, run as: ./run foo.sol foo"
    exit 1
fi
echo "Compiling..."
solc "$1" --asm-json > "$2"
echo "Running v2..."
python v2.py "$1" "$2"
echo "Finished. Go to Neo4j to visualise"