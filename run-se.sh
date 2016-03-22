#!/bin/bash

if (( "$#" != 1 ))
then
    echo "Usage info:..."
    echo "./run-se.sh <bytecode>"
    echo "for example, run as: ./run-se.sh SE-tests/puzzle.evm"
	exit 1
fi

python symExec.py "$1"
