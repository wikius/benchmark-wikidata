#!/usr/bin/python

# Expand the SCHOLIA label service templates
# This code uses matching, not parsing, and thus can break, but it should work for Scholia queries
# Assumes easy syntax

# also add prefixes and remove import
# depends on imports and label macros by themselves on a line


import sys
import re


def expand(line):
    if 'sparql_helpers' in line:
        match = re.search('".*"', line)
        variables = match.group(0) if match else None
        variables = variables.split(",")
        variables = [ v.strip().strip('"') for v in variables ]
        description = True if 'description' in line else False
        url = "<http://schema.org/description>" if description else "<http://www.w3.org/2000/01/rdf-schema#label>" 
        suffix = "Description" if description else "Label"
        expansion = []
        for v in variables:
            expansion += [f'  BIND (IF(BOUND ({v}), {v}, <http://doesntexist.example.com/nexistepas>) AS {v}{suffix}__)']
            expansion += [f'  OPTIONAL {{ {v}{suffix}__ {url} {v}{suffix}. FILTER(LANG({v}{suffix}) = "en") }}']
            expansion += [f'  OPTIONAL {{ {v}{suffix}__ {url} {v}{suffix}. FILTER(LANG({v}{suffix}) = "mul") }}']
        return '\n'.join(expansion)
    else:
        return line

with open(sys.argv[1]) as f: query = f.read()
query = query.split('\n')
if 'sparql-helpers' in query[0]:
    query = query[1:]

query = [ expand(line) for line in query ]
query = '\n'.join(query)

with open(sys.argv[1], 'w') as f:
    f.write(query)
    print("EXPANDED", sys.argv[1])

