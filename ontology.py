#!/bin/python
# construct full RDF dumps of statements based on results of subclass of and instance of queries
# needs QLever running on Wikidata

import os
import io
import re
import subprocess
import sys
import time
import csv
import requests

prefixes = '''PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
'''

output_prefixes = '''@prefix wds: <http://www.wikidata.org/entity2/> .
@prefix wd: <http://www.wikidata.org/entity/> .
@prefix wdt: <http://www.wikidata.org/prop/direct/> .
@prefix p: <http://www.wikidata.org/prop/> .
@prefix s: <http://www.wikidata.org/entity/statement/> .
@prefix ps: <http://www.wikidata.org/prop/statement/> .
@prefix wikibase: <http://wikiba.se/ontology#> .

'''

file_prefix = sys.argv[1] if len(sys.argv) > 1 else "wikidata-"

# send a query to a local QLever process
def query_wikidata(query):
##    commandQ = ['/usr/bin/curl', 'https://qlever.cs.uni-freiburg.de/api/wikidata', '-s', '-H', 'Accept: text/csv', '-H', 'Content-type: application/sparql-query', '--data', query]
    headers={"Accept": "text/csv", "Content-type": "application/sparql-query", "user-agent": "wikidata-benchmark/0.0.1"}
    reply = requests.get('http://getafix:7001',
                         headers=headers,
                         params={"query": prefixes + query})
    return reply.text

def write_statement(file, sprefix, subject, predicate, oprefix, object, full=True):
    if full:
        file.write(f"""{sprefix}:{subject} wdt:{predicate} {oprefix}:{object} ;
	p:{predicate} s:s_{sprefix}-{subject}-{predicate}-{oprefix}-{object} .
s:s_{sprefix}-{subject}-{predicate}-{oprefix}-{object} a wikibase:Statement,
		wikibase:BestRank ;
	wikibase:rank wikibase:NormalRank ;
	ps:{predicate} {oprefix}:{object} .
""")
    else:
        file.write(f"""{sprefix}:{subject} wdt:{predicate} {oprefix}:{object} .""")

def subclass_shadow_original():
    i = 0
    with open(file_prefix + 'subclass-shadow-original.ttl','w') as out:
        out.write(output_prefixes)
        with io.StringIO(subclass1) as subclasscsv:
            subclassreader = csv.reader(subclasscsv, delimiter=',')
            next(subclassreader)
            for sub, in subclassreader:
                if '/' in sub:
                    i += 1
                    write_statement(out, "wds", sub.split('/')[-1], "P279", "wd", sub.split('/')[-1])
    return i

def subclass_original_shadow_parent():
    i = 0
    with open(file_prefix + 'subclass-original-shadow-parent.ttl','w') as out:
        out.write(output_prefixes)
        with io.StringIO(subclass2) as subclasscsv:
            subclassreader = csv.reader(subclasscsv, delimiter=',')
            next(subclassreader)
            for sub, super in subclassreader:
                if '/' in sub and '/' in super:
                    i += 1
                    write_statement(out, "wd", sub.split('/')[-1], "P279", "wds", super.split('/')[-1])
    return i

def instance_shadow_original():
    i = 0
    with open(file_prefix + 'instance-shadow-original-parent.ttl','w') as out:
        out.write(output_prefixes)
        with io.StringIO(instance) as instancecsv:
            instancereader = csv.reader(instancecsv, delimiter=',')
            next(instancereader)
            for ind, clss in instancereader:
                if '/' in ind and '/' in clss:
                    i += 1
                    write_statement(out, "wds", ind.split('/')[-1], "P31", "wd", clss.split('/')[-1])
    return i

print("# SUBCLASS 1")
subclass1 = query_wikidata("SELECT DISTINCT ?s WHERE { { SELECT DISTINCT ?s WHERE { ?s wdt:P279 ?c . } } UNION { SELECT DISTINCT ?s WHERE { ?c wdt:P279 ?s } } UNION { SELECT DISTINCT ?s WHERE { ?i wdt:P31 ?s } } }")
print(f"# {subclass_shadow_original():,} subclasses")

print("# SUBCLASS 2")
subclass2 = query_wikidata("SELECT DISTINCT ?s ?c WHERE { ?s wdt:P279 ?c . }")
print(f"# {subclass_original_shadow_parent():,} subclass links")

print("# INSTANCE")
instance = query_wikidata("SELECT DISTINCT ?i ?c WHERE { ?i wdt:P31 ?c . }")
print(f"# {instance_shadow_original():,} instance links")
