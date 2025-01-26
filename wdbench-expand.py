#!/bin/python

# wdbench-expand.py <filename>.txt

# Expand query cores from WDBench benchmark to full SPARQL queries
# Wraps the core in SELECT * WHERE { ... }
# May want to add LIMIT nnn at some point

# Reads the query core file, writes a file with the .text extension
# For each line in the file extracts a core, writes the core as a full query

import csv
import sys

if len(sys.argv) >= 2:
    filename = sys.argv[1]
else:
    print("Usage: wdbench-expand.py <filename>.txt <limit>")
    sys.exit()
limit = None
if len(sys.argv) >= 3:
    limit = sys.argv[2]

ofilename = filename.replace('.txt', '.text')
if ofilename == filename:
    print("Input filename cannot end in .text")

print(f"Expanding {filename} with limit {limit}")

with open(ofilename, 'w') as ofile:
    with open(filename, 'r') as corefile:
        filereader = csv.reader(corefile)
        for row in filereader:
            if limit is not None:
                ofile.write(f"SELECT * WHERE {{ {row[1]} }} LIMIT {limit}\n")
            else:
                ofile.write(f"SELECT * WHERE {{ {row[1]} }}\n")
