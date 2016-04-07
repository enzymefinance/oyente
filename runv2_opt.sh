#!/bin/bash
# Author : still mostly Loi Luu 

if (( "$#" != 2 ))
then
    echo "Usage info:..."
    echo "./run <directory> <opt|unopt>"
    echo "for example, run as: ./run contracts unopt"
    exit 1
fi

for file in "$1"/*
do
    if [ ${file: -4} == ".sol" ] 
    then
        if [ $2 == "unopt" ]
        then
            echo "Compiling $file unoptimized"
            solc "$file" --asm-json > "$file""_out.json"
            echo "Running v2..."
            python v2.py "$file" "$file""_out.json" "bench_unopt.txt"
        else
            echo "Compiling $file optimized"
            solc "$file" --optimize --asm-json > "$file""_out.json"
            echo "Running v2..."
            python v2.py "$file" "$file""_out.json" "bench_opt.txt"
        fi    
    fi
done

rm "$1"/*.json