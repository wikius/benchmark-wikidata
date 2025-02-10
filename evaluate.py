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

def generic_eval(query, output, url):
    headers={"Accept": "text/tab-separated-values", "Content-type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
#    headers={"Accept": "application/sparql-results+json", "Content-type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.get(url,
                         headers=headers,
                         params={"query": prefixes + query})
#    inspect(reply)
    reply.encoding = 'utf-8'
    if engine == "QLever" and "http://schema.org/name" in reply.text:
        print(">>>NAME TRIPLES FOUND")
    print("RESULT", reply.text)
    with open(output, "w") as file:
        file.write(reply.text)
        
def blazegraph_eval(query, output, url):
    headers={"Accept": "text/tab-separated-values", "user-agent": "pfps-benchmark/0.0.1"}
#    headers={"Accept": "application/sparql-results+json", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.get(url,
                         headers=headers,
                         params={"query": prefixes + query})
#    inspect(reply)
    print("RESULT", reply.text)
    with open(output, "w") as file:
        file.write(reply.text)

def mdb_eval(query, output, url):
    headers={"Content-Type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
#    headers={"Accept": "text/tab-separated-values", "Content-Type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.post(url, headers=headers, data=query)

#    inspect(reply)
    reply.encoding = 'utf-8'

    with open(output, "w") as file:
        print("RESULT", output)
        file.write(reply.text)

engines = [
    [ "QLever", generic_eval, 'https://qlever.cs.uni-freiburg.de/api/wikidata/', True],
    [ "QLocal", generic_eval, 'http://getafix:7001', True],
    [ "Blazegraph", blazegraph_eval, 'https://query.wikidata.org/sparql', True],
    [ "BLocal", blazegraph_eval, "http://getafix:9999/bigdata/sparql", True], 
#    [ "Virtuoso", generic_eval, "https://wikidata.demo.openlinksw.com/sparql", False],
    [ "MilleniumDB", mdb_eval, "https://wikidata.imfd.cl/wikidata/sparql", False],
    [ "MLocal", generic_eval, "http://getafix:1234/sparql", False], 
]

offset = int(sys.argv[2])
filename = sys.argv[1]

with open(filename, 'r') as qfile:
    lines = qfile.readlines()
query = lines[offset-1]
print(f"QUERY {query}")
        
for engine, function, url, _ in engines:
    print(f"{engine} {url}")
    function(query, engine+'.result', url)

    
