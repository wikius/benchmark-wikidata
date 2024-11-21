#!/bin/python
# Control program to run benchmarks.
# Benchmarks are files in a directory (default queries).
# Reads lines from control file (queries.tsv) in the directory with fields separated by tabs.
#   Each line contains the name of a file in the directory (without trailing .sparql) and a description.
#   Lines can also have paired extra fields containing a 
#   Lines with less than two fields and lines starting with # are just printed and otherwise ignored.
# Evaluates the query on one or more engines.
# Current engines are:
#  QLever - QLever Wikidata public query service at https://qlever.cs.uni-freiburg.de/api/wikidata/
#  QLTest - QLever Wikidata test query service at https://qlever.cs.uni-freiburg.de/api/wikidata-test/
#  QLocal - Local QLever Wikidata query service at http://getafix:7001
#  WDQS - Blazegraph public Wikidata Query Service at https://query.wikidata.org/sparql
#  ORB - Blazegraph public Wikidata Query Service at https://query-direct.orbopengraph.com/bigdata/namespace/wdq/sparql
# local Blazegraph
#  VOS - Virtuoso public Wikidata Query Service at ttps://wikidata.demo.openlinksw.com/sparql
#  VLocal - Local Virtuoso query service at http://getafix:8890/sparql
#  MDB - MilleniumDB public Wikidata Query Service at https://wikidata.imfd.cl/wikidata/sparql
# local MilleniumDB
# Positional arguments are a filename and description, which means to only run that query.
# Option: -d --directory <directory name> use this directory
# Option: -e --engine <engine> ...  only use these engines
# Option: -c --clear-cache clear the cache for each query (only for QLever currently)

# TODO: convert to control file to yaml?

# This benchmark harness was converted from a benchmark harness used to investigate class order in Wikidata.
# This benchmark harness is still under development

# See also QLever API at https://github.com/ad-freiburg/qlever/wiki/QLever-API-documentation
# Some ideas here were taken from there

import requests
import random
import sys
import json
import subprocess
import argparse
import time
import subprocess
import re
import json
import csv

prefixes = '''PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
'''

queries_directory = 'queries'
queries_file = None

def qlever_clear_cache(url):
    reply = requests.get(url, params={"cmd": "clear-cache"})
    if reply.status_code != 200:
        print("Clear Cache Status Code", reply.status_code)

def results_qlever(reply):
    replyj = reply.json()
    count = replyj["resultsize"]
    if count == 1:
        result = re.findall(r'[Q0-9]+',replyj["res"][0][0])
        if result:
            count = f"Result={result[0]:4}"
        else:
            count = f"Result={replyj["res"][0][0]:4}"
    else:
        count = f"Count={count:4}"
    time = replyj["time"]
    exception = replyj.get("exception", "")
    if exception:
        result_count = None
    return f"{count} Time={time} {exception}"

def qlever_eval(query, url, no_caching=True):
    if no_caching:
        qlever_clear_cache(url)
    reply = requests.get(url,
                         headers={"Content-type": "sparql-query",
                                  "Accept": "application/qlever-results+json",
                                  },
                         params={"query": prefixes + query})
    if reply.status_code >= 500:
#        print("ERROR", reply.text)
#        print(json.dumps(reply.json(), indent=4))
        return f"ERROR Status Code {reply.status_code} {reply.json()['exception']}"
    else:
        return results_qlever(reply)


def results_csv(text):
    count = text.count("\n")-1
    if count == 1:
        result = text.split('\n')[1].strip().split(',')[0]
        return f"Result={result:4}"
    else:
        return f"Count={count:4}"


def wdqs_eval(query, url, no_caching=True):
    # use the explain parameter to get timing information
    headers={"Accept": "text/csv", "user-agent": "pfps-benchmark/0.0.1"}
    if no_caching:
# doesn't work        headers["cache-control"] = "no-cache"
        query = "#" + str(random.randint(1,1000000000)) + "\n" + query
    try:
        reply = requests.get(url,
                             headers=headers,
                             params={"query": query, 
#                                     "explain": "", # "explain": "details",
                                     },
                         )
    except Exception:
        return f"Count=???? Exception reading response"
    if reply.status_code >= 500:
        exception = " UNKNOWN PROBLEM"
        for line in reply.text.split('\n'):
            if "Exception" in line:
                exception = "EXCEPTION " + line
                break
        return exception
    if reply.status_code == 429:
        print("RETRY AFTER", reply.headers["retry-after"])
        sys.exit()
    timeout = re.search("java.util.concurrent.TimeoutException", reply.text)
    if timeout:
        return f"{results_csv(reply.text)} TIMEOUT DURING RESULT GENERATION"
    return f"{results_csv(reply.text)}"


def generic_eval(query, url=None, no_caching=True):
    headers={"Accept": "text/tab-separated-values", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.get(url,
                         headers=headers,
                         params={"query": prefixes + query})
    return f"{results_csv(reply.text)}", reply.text

def vos_eval(query, url, no_caching=True):
    count, text = generic_eval(query, url=url, no_caching=no_caching)
    err = re.search('Virtuoso \\d+ Error .*\n', text)
    if err:
        return "ERROR " + err.group(0).strip()
    else:
        return count

def results_json(jtext):
    count = len(jtext["results"]["bindings"])
    if count == 1:
        result = jtext["results"]["bindings"][0][jtext["head"]["vars"][0]]["value"]
        return f"Result={result:4}"
    else:
        return f"Count={count:4}"

def mdb_eval(query, url, no_caching=True):
    headers={"Content-Type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.post(url,
                         headers=headers,
                         data=query)
    if reply.status_code == 200:
        if reply.text:
            try:
                result = results_json(reply.json())
            except Exception:
                return f"ERROR UNABLE TO DECIPHER OUTPUT {reply.text}"
            return result
        else:
            return "ERROR EMPTY OUTPUT"
    else:
        return f"ERROR Status Code {reply.status_code} {reply.text}"

engines = [
    [ "QLocal", qlever_eval, 'http://getafix:7001'],
    [ "QLever",  qlever_eval, 'https://qlever.cs.uni-freiburg.de/api/wikidata/'],
    [ "QLTest", qlever_eval,  'https://qlever.cs.uni-freiburg.de/api/wikidata-test/'],
    [ "WDQS", wdqs_eval, 'https://query.wikidata.org/sparql'],
    [ "ORB", wdqs_eval, 'https://query-direct.orbopengraph.com/bigdata/namespace/wdq/sparql'],
    [ "VOS", vos_eval, "https://wikidata.demo.openlinksw.com/sparql" ],
    [ "VLocal", vos_eval, "http://getafix:8890/sparql" ],
    [ "MDB", mdb_eval, "https://wikidata.imfd.cl/wikidata/sparql"],
    [ "MLocal", mdb_eval, "http://getafix:1234/sparql"], 
]

def modify_query(query, count, replace):
    if count:
        query = f"SELECT (COUNT (*) AS ?count) WHERE {{\n{query}}}\n"
    if replace:
        query = query.replace("REPLACE", replace)
    return query

def process(query_file_name, description, alternatives=None, no_caching=True, counting=False, replace=None):
    alternatives = alternatives if alternatives is not None else {}
    print("QUERY:", query_file_name, description.strip())
    with open(queries_directory + '/' + query_file_name + '.sparql', 'r') as query_file:
        query = modify_query(query_file.read(), counting, replace)

    for [engine, function, url] in engines:
        if engine in alternatives:
            with open(queries_directory + '/' + alternatives[engine] + '.sparql', 'r') as query_file:
                query_for_engine = modify_query(query_file.read(), counting, replace)
            start_time = time.time()
            result = function(query_for_engine, url, no_caching=no_caching)
            end_time =time.time()
        else:
            start_time = time.time()
            try:
                result = function(query, url, no_caching=no_caching)
            except Exception as e:
                result = f"EXCEPTION {e}"
            end_time =time.time()
        print(f"{engine:6} Elapsed={int((end_time - start_time) * 1000):5}ms {result}")

    print()

def parameterized(parameter, query_file_name, description, alternatives, no_caching, counting):
    with open(queries_directory + '/' + parameter + '.sparql', 'r') as parameter_file:
        parameter = parameter_file.read()
    result = generic_eval(parameter, 'http://getafix:7001')
    rows = result[1].splitlines()
    for row in rows[1:]:
        replace = row.split('\t')[0]
        rdesc = description.replace("REPLACE", replace)
        process(query_file_name, rdesc, alternatives=alternatives, no_caching=no_caching, counting=counting, replace=replace)



parser = argparse.ArgumentParser()
parser.add_argument("filename", nargs="?", default=None, help="Name of file containing query")
parser.add_argument("description", nargs="?", default="", help="Description of the query")
parser.add_argument("-e", "--engine", action='append', type=str, choices=[engine[0] for engine in engines],
                    help="System to use (can be repeated)")
parser.add_argument("-d", "--directory", action='store', type=str, help="Directory with queries")
parser.add_argument("-C", "--caching", action='store_true', help="Permit caching (only changes QLever and Blazegraph)")
parser.add_argument("-c", "--count", action='store_true', help="Add enclosing SELECT to count results")
args = parser.parse_args()

if args.directory:
    queries_directory = args.directory.rstrip('/')
if args.engine:
    engines = [ engine for engine in engines if engine[0] in args.engine ]

if args.filename:
    process(args.filename, args.description, no_caching=not args.caching, counting=args.count)
else:
    print(f"Evaluating queries from {queries_directory}{', counted,' if args.count else ''}")
    print(f"with caching {'allowed' if args.caching else 'disabled for QLever and Blazegraph'}\n")
    queries_file = open(queries_directory + '/queries.tsv', 'r')
    for line in queries_file:
        fields = line.rstrip().split('\t')
        if len(fields) < 2 or line.startswith("#"):
            print(line)
            continue
        query_file_name = fields[0]
        description = fields[1]
        alternatives = {fields[i]: fields[i + 1] for i in range(2, len(fields), 2)}
        if "PARAMETER" in alternatives:
            parameter = alternatives["PARAMETER"]
            del alternatives["PARAMETER"]
            parameterized(parameter, query_file_name, description, alternatives, no_caching=not args.caching, counting=args.count)
        else:
            process(query_file_name, description, alternatives, no_caching=not args.caching, counting=args.count)

