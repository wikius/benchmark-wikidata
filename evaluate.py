#!/bin/python

import sys
import requests

prefixes = '''PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
'''

def qlever_eval(query, url, no_caching=True):
    if no_caching:
        qlever_clear_cache(url)
    reply = requests.get(url,
                         headers={"Content-type": "sparql-query",
                                  "Accept": "application/qlever-results+json",
                                  },
                         params={"query": prefixes + query})
    return results_qlever(reply)

def inspect(reply):
    print("CONTENT TYPE", reply.headers['content-type'], "ENCODING", reply.encoding)
    
    for line in reply.text.split('\n'):
        if '@mt' in line and 'description' in line:
            field = line.split('\t')[1]
            print('  '.join(field))
            print(".".join(hex(ord(c))[2:] for c in field))

def generic_eval(query, output, url, verbose):
    headers={"Accept": "text/tab-separated-values", "Content-type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
#    headers={"Accept": "application/sparql-results+json", "Content-type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.get(url,
                         headers=headers,
                         params={"query": query})
#    inspect(reply)
    reply.encoding = 'utf-8'
    if engine == "QLever" and "http://schema.org/name" in reply.text:
        print(">>>NAME TRIPLES FOUND")
    if verbose:
        print("RESULT\n", reply.text)
    with open(output, "w") as file:
        file.write(reply.text)
        
def blazegraph_eval(query, output, url, verbose):
    headers={"Accept": "text/tab-separated-values", "user-agent": "pfps-benchmark/0.0.1"}
#    headers={"Accept": "application/sparql-results+json", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.get(url,
                         headers=headers,
                         params={"query": query})
#    inspect(reply)
    if verbose:
        print("RESULT\n", reply.text)
    with open(output, "w") as file:
        file.write(reply.text)

def mdb_eval(query, output, url, verbose):
    headers={"Content-Type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
#    headers={"Accept": "text/tab-separated-values", "Content-Type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.post(url, headers=headers, data=query)

#    inspect(reply)
    reply.encoding = 'utf-8'

    if verbose:
        print("RESULT\n", reply.text)
    with open(output, "w") as file:
        file.write(reply.text)

engines = [
    [ "QWDS", generic_eval, 'https://qlever.cs.uni-freiburg.de/api/wikidata/', True],
    [ "QLever", generic_eval, 'http://getafix:7001', True],
    [ "WDQS", blazegraph_eval, 'https://query.wikidata.org/sparql', True],
    [ "Blazegraph", blazegraph_eval, "http://getafix:9999/bigdata/sparql", True], 
#    [ "VOS", generic_eval, "https://wikidata.demo.openlinksw.com/sparql", False],
#    [ "Virtuoso", generic_eval, "http://getafix:8890/sparql", True],
#    [ "MDB", mdb_eval, "https://wikidata.imfd.cl/wikidata/sparql", False],
    [ "MilleniumDB", generic_eval, "http://getafix:1234/sparql", False], 
]

filename = sys.argv[1]
offset = int(sys.argv[2]) if len(sys.argv) > 2 else 0
enginearg = sys.argv[3] if len(sys.argv) > 3 else None
replace = sys.argv[4] if len(sys.argv) > 4 else None
replacement = sys.argv[5] if len(sys.argv) > 5 else ""

if offset:
    with open(filename, 'r') as qfile:
        lines = qfile.readlines()
    query = lines[offset-1]
else:
    with open(filename, 'r') as qfile:
        query = qfile.read()
if replace: query = query.replace(replace, replacement)
if 'wdt:' not in query: query = prefixes + query
print(f"QUERY:\n{query}")
        
for engine, function, url, _ in engines:
    if not enginearg or engine == enginearg:
        print(f"{engine} {url}")
        function(query, engine+'.result', url, enginearg is not None)
