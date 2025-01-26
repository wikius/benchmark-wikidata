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

def generic_eval(query, output, url):
    headers={"Accept": "text/tab-separated-values", "Content-type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.get(url,
                         headers=headers,
                         params={"query": prefixes + query})
    with open(output, "w") as file:
        file.write(reply.text)
        
def blazegraph_eval(query, output, url):
    headers={"Accept": "text/tab-separated-values", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.get(url,
                         headers=headers,
                         params={"query": prefixes + query})
    with open(output, "w") as file:
        file.write(reply.text)
        

engines = [
    [ "QLocal", generic_eval, 'http://getafix:7001', True],
    [ "VLocal", generic_eval, "http://getafix:8890/sparql", False],
    [ "MLocal", generic_eval, "http://getafix:1234/sparql", False], 
    [ "BLocal", blazegraph_eval, "http://getafix:9999/bigdata/sparql", True], 
]

offset = int(sys.argv[1])
filename = sys.argv[2]

with open(filename, 'r') as qfile:
    lines = qfile.readlines()
query = lines[offset-1]
print(f"QUERY {query}")
        
for engine, function, url, _ in engines:
    print(f"ENGINE {engine} {url}")
    function(query, engine+'.result', url)

    
