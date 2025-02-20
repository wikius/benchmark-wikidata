#!/usr/bin/python

# Instantiate and run a scholia template against a SPARQL engine

import sys
import time
import requests


def basic_eval(query, url, result_format="text/tab-separated-values"):
    headers={"Accept": result_format, "Content-type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
    start_time = time.time()
    reply = requests.get(url,
                         headers=headers,
                         params={"query": query})
    end_time = time.time()
    etime = int((end_time - start_time) * 1000)
    reply.encoding = 'utf-8'
    return reply, etime


engines = [
    [ "WDQS", basic_eval, 'https://query.wikidata.org/sparql'], 
    [ "MDB", basic_eval, "https://wikidata.imfd.cl/wikidata/sparql"],
    [ "QWDS",  basic_eval, 'https://qlever.cs.uni-freiburg.de/api/wikidata/'],
    [ "VOS", basic_eval, "https://wikidata.demo.openlinksw.com/sparql"],
]

template = sys.argv[1]
replaced = sys.argv[2]
replacement = sys.argv[3]

with open(sys.argv[1]) as f: query = f.read()

query = query.replace(replaced, replacement)
print("QUERY")
print(query)
for engine, function, url in engines:
    print("ENGINE", engine)
    reply, etime = function(query, url)
    print(engine, etime, len(reply.text.split('\n')))
    print(reply.text)
