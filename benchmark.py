#!/bin/python
# Control program to run benchmarks.

# TODO handle different versions of strings being output  <string> vs "<string>@lt"

# ./benchmark.py [<filename>] --description --engine --directory --caching --count

# Content output lines contain tab-separated fields
#  RESULT or numeric index
#  engine
#  options
#  elapsed time in ms
#  total time in ms from engine, if available
#  result, either Count= <number of results> or Result=<first value of single result> or None
#  HTTP result code, anything other than 200 is some sort of problem
#  error message, either from engine or from this program
#  diagnostic information from engine, if available (e.g., timing from QLever), only in verbose mode

# There are three options for benchmarks:
# 1/ Benchmarks are files in a directory (default queries).
#  Read lines from control file (queries.tsv) in the directory with fields separated by tabs.
#   Each line contains the name of a file in the directory (without trailing .sparql) and a description.
#   Lines can also have paired extra fields containing a ???
#   Lines with less than two fields and lines starting with # are just printed and otherwise ignored.
# 2/ Benchmarks are lines in a file
#  Read lines from the file in the directory and evaluate each query

# Evaluates the query on one or more engines.  Note that local engines are not started.
# Current engines are:
#  QLever - QLever Wikidata public query service at https://qlever.cs.uni-freiburg.de/api/wikidata/
#  QLTest - QLever Wikidata test query service at https://qlever.cs.uni-freiburg.de/api/wikidata-test/
#  QLocal - Local QLever Wikidata query service at http://getafix:7001
#  WDQS - Blazegraph public Wikidata Query Service at https://query.wikidata.org/sparql
#  ORB - Blazegraph public Wikidata Query Service at https://query-direct.orbopengraph.com/bigdata/namespace/wdq/sparql
#  Blocal - local Blazegraph query service at http://getafix:9999/bigdata/sparql
#  VOS - Virtuoso public Wikidata Query Service at ttps://wikidata.demo.openlinksw.com/sparql
#  VLocal - Local Virtuoso query service at http://getafix:8890/sparql
#  MDB - MilleniumDB public Wikidata Query Service at https://wikidata.imfd.cl/wikidata/sparql
#  MLjson - local MilleniumDB at http://getafix:1234/sparql with JSON output
#  MLocal - local MilleniumDB at http://getafix:1234/sparql with TSV output

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
import subprocess
import argparse
import time
import re
import json
import csv

prefixes = '''PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
'''
queries_directory = 'queries'
queries_file = None

max_time = 600000

def qlever_clear_cache(url):
    reply = requests.get(url, params={"cmd": "clear-cache"})
    if reply.status_code != 200:
        print("Clear Cache Status Code", reply.status_code)

def unbox(field):
    if len(field) == 0:
        return " "
    elif field[0] == '<':   # IRI
        match = re.search(r'^<.*/([^/]+)>$', field)
        return match.group(1) if match and len(match.groups()) >= 1 else field
    elif field[0] == '"':  # literal
        match = re.search(r'^"(.*)"(@[^"]*)?$', field)
        if match:
            return match.group(1) if match and len(match.groups()) >= 1 else field
        else:
            match = re.search(r'^"(.*)"..<[^"]+>$', field)
            if match:
                return match.group(1) if match and len(match.groups()) >= 1 else field
    return field

def results_qlever(reply):
    try:
        replyj = reply.json()
    except Exception:
        return None, reply.status_code, "ERROR CANNOT DECIPHER JSON OUTPUT", "", ""
    count = replyj["resultsize"]
    if count == 1:
        if len(replyj["res"][0]) > 0:
            result = unbox(replyj["res"][0][0])
        else:
            result = " "
        count = f"Result={result}"
    else:
        count = f"Count= {count}"
    exception = replyj.get("exception", "")
    if exception:
        count = None
    time = replyj["time"]
    stime = time["total"][0:-2] if isinstance(time["total"],str) else time["total"]
    return count, reply.status_code, exception, stime, time

def qlever_eval(query, url, no_caching=True):
    if no_caching:
        qlever_clear_cache(url)
    reply = requests.get(url,
                         headers={"Content-type": "sparql-query",
                                  "Accept": "application/qlever-results+json",
                                  },
                         params={"query": prefixes + query})
    return results_qlever(reply)


def results_csv(text, separator=','):
    count = text.count("\n")-1
    if count == 1:
        result = text.split('\n')[1].strip().split(separator)[0]
        if separator == "\t":
            return f"Result={unbox(result)}"
        else:
            match = re.search("([^/]+)$", result)
            return f"Result={(match.group(1) if match is not None else result)}"
    else:
        return f"Count= {count}"


def wdqs_eval(query, url, no_caching=True):
    headers={"Accept": "text/csv", "user-agent": "pfps-benchmark/0.0.1"}
    if no_caching:
        query = "#" + str(random.randint(1,1000000000)) + "\n" + query
    try:
        reply = requests.get(url,
                             headers=headers,
                             params={"query": query, "timeout": "600"},
                         )
    except Exception:
        return None, None, "ERROR Exception reading response", "", ""
    if reply.status_code == 429:
        print("RETRY AFTER", reply.headers["retry-after"])
        sys.exit()
    if reply.status_code >= 400:
        count = None
        exception = "ERROR UNKNOWN PROBLEM"
        for line in reply.text.split('\n'):
            if "Exception" in line:
                exception = "ERROR " + line
                break
    else:
        exception = ""
        timeout = re.search("java.util.concurrent.TimeoutException", reply.text)
        if timeout:
            exception = "ERROR TIMEOUT DURING RESULT GENERATION"
        count = results_csv(reply.text)
    return count, reply.status_code, exception, "", ""


def generic_eval(query, url=None, no_caching=True):
    headers={"Accept": "text/tab-separated-values", "Content-type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.get(url,
                         headers=headers,
                         params={"query": prefixes + query})
    if reply.status_code < 400:
        if reply.text:
            return results_csv(reply.text, separator='	'), reply.status_code, "", "", ""
        else:
            return None, reply.status_code, "ERROR EMPTY OUTPUT", "", ""
    else:
        return None, reply.status_code, reply.text, "", ""


def virtuoso_eval(query, url, no_caching=True):
    count, code, text, _, _ = generic_eval(query, url=url, no_caching=no_caching)
    if code == 200:
        return count, code, "", "", ""
    else:
        err = re.search('Virtuoso \\d+ Error .*\n', text)
        return count, code, err.group(0).strip() if err else "", "", ""

def results_json(jtext):
    if isinstance(jtext,str):
        count = len(re.findall(',{"', jtext))
        return f"Count = {count:4}", "DEDUCED FROM UNPARSABLE JSON"
    else:
        count = len(jtext["results"]["bindings"])
        if count == 1:
            if jtext["head"]["vars"]:
                row = jtext["results"]["bindings"][0]
                result = row[jtext["head"]["vars"][0]]["value"]
            else:
                result = " "
            iden = re.search("([^/]+)$", result)
            return f"Result={iden.group(1) if iden is not None else result:4}", ""
        else:
            return f"Count= {count}", ""

def mdb_eval(query, url, no_caching=True):
    headers={"Content-Type": "application/sparql-query", "user-agent": "pfps-benchmark/0.0.1"}
    reply = requests.post(url, headers=headers, data=query)
    if reply.status_code < 400:
        if reply.text:
            try:
                result, excptn = results_json(reply.json())
            except Exception:
                result = None
                excptn = f"ERROR UNABLE TO DECIPHER OUTPUT {reply.text[0:200].split('\n')[0]}"
        else:
            result = None
            excptn = "ERROR EMPTY OUTPUT"
    else:
        result = None
        # 404 error message somehow causes problems
        excptn = reply.text.split('\n')[0] if reply.status_code != 404 else "NOT FOUND"
    return result, reply.status_code, excptn, "", ""


engines = [
    [ "QLever",  qlever_eval, 'https://qlever.cs.uni-freiburg.de/api/wikidata/', True],
    [ "QLTest", qlever_eval,  'https://qlever.cs.uni-freiburg.de/api/wikidata-test/', True],
    [ "QLocal", qlever_eval, 'http://getafix:7001', True],
    [ "VOS", virtuoso_eval, "https://wikidata.demo.openlinksw.com/sparql", False],
    [ "VLocal", virtuoso_eval, "http://getafix:8890/sparql", False],
    [ "MDB", mdb_eval, "https://wikidata.imfd.cl/wikidata/sparql", False],
    [ "MLjson", mdb_eval, "http://getafix:1234/sparql", False], 
    [ "MLocal", generic_eval, "http://getafix:1234/sparql", False], 
    [ "WDQS", wdqs_eval, 'https://query.wikidata.org/sparql', True],
    [ "ORB", wdqs_eval, 'https://query-direct.orbopengraph.com/bigdata/namespace/wdq/sparql', True],
    [ "BLocal", wdqs_eval, "http://getafix:9999/bigdata/sparql", True], 
]

def options(no_caching, nocachable, counting, distinct):
    options = []
    if no_caching and nocachable:
        options.append("NOCACHE")
    if counting:
        options.append("COUNTED")
    if distinct:
        options.append("NODUPS")
    return ','.join(options)

def modify_query(query, count, replace):
    if args.nodups and not re.search(r"distinct", query, flags=re.IGNORECASE):
        query = re.sub(r"select", "SELECT DISTINCT", query, count=1, flags=re.IGNORECASE)
    if count:
        query = re.sub(r"select", "SELECT (COUNT (*) AS ?benchmark_count) WHERE { SELECT", query, count=1, flags=re.IGNORECASE) + " }"
    if replace:
        query = query.replace("REPLACE", replace)
    return query


def print_result(index, engine, opts, etime, itime, count, code, err, message):
    print(f"{index+1}	{engine}	{opts}	{etime:>7}	{itime:>6}	{count} 	{code}	{err}	{message if args.verbose else ''}", flush=True)

def process_query(index, query, no_caching=True, counting=False, replace=None, description=""):
    if args.verbose and description:
        print("QUERY", description)
    query = modify_query(query, counting, replace)
    for [engine, function, url, nocachable] in engines:
        opts = options(no_caching, nocachable, counting, args.nodups)
        if query:
            start_time = time.time()
            count, code, err, itime, dtime = function(query, url, no_caching=no_caching)
            end_time = time.time()
        else:
            print_result(index, engine, opts, max_time, "", None, 500, "SKIPPED - CAUSES CRASH", "")
            return
        etime = int((end_time - start_time) * 1000)
        print_result(index, engine, opts, etime, itime, count, code, err, dtime)

def process(directory, query_file_name, description, alternatives=None, no_caching=True, counting=False, replace=None, index=None):
    alternatives = alternatives if alternatives is not None else {}
    if args.verbose:
        print("QUERY", query_file_name, description.strip())
    with open(directory + '/' + query_file_name + '.sparql', 'r') as query_file:
        query = modify_query(query_file.read(), counting, replace)

    for [engine, function, url, nocachable] in engines:
        if engine in alternatives:
            with open(queries_directory + '/' + alternatives[engine] + '.sparql', 'r') as query_file:
                query_for_engine = modify_query(query_file.read(), counting, replace)
            start_time = time.time()
            count, code, errr, itime, dtime = function(query_for_engine, url, no_caching=no_caching)
            end_time =time.time()
        else:
            start_time = time.time()
            try:
                count, code, errr, itime, dtime = function(query, url, no_caching=no_caching)
            except Exception as e:
                result = f"EXCEPTION {e}"
            end_time =time.time()
        etime = int((end_time - start_time) * 1000)
        opts = options(no_caching, nocachable, counting, args.distinct)
        print_result(index, engine, opts, etime, itime, count, code, err, query_file_name)

    if args.verbose:
        print()

def parameterized(parameter, query_file_name, description, alternatives, no_caching, counting):
    print("PARAMETERIZED", parameter)
    with open(queries_directory + '/' + parameter + '.sparql', 'r') as parameter_file:
        parameter = parameter_file.read()
    result, code, text, _, _ = generic_eval(parameter, 'http://getafix:7001')  ## pfps ????
    rows = result[1].splitlines()
    for index,row in enumerate(rows[1:]):
        replace = row.split('\t')[0]
        rdesc = description.replace("REPLACE", replace)
        process(query_file_name, rdesc, alternatives=alternatives, no_caching=no_caching, counting=counting, replace=replace, index=idx)

def process_queries_file(filename, description, no_caching, counting, skip=0):
    if args.verbose and description:
        print(description)
    with open(filename, 'r') as file:
        for index,line in enumerate(file):
            if index < skip:
                continue
            line = line.split('\t')
            query = line[-1].strip()
            qdescription = line[0] if len(line) >= 2 else ""
            process_query(index, query, no_caching, counting, description=qdescription)

def process_control_file(control_file, skip=0):
    index = -1
    for line in enumerate(control_file):
        fields = line.rstrip().split('\t')
        if len(fields) < 2 or line.startswith("#"):
            if args.verbose:
                print(line)
            continue
        index += 1
        if index < skip:
            continue
        query_file_name = fields[0]
        description = fields[1]
        alternatives = {fields[i]: fields[i + 1] for i in range(2, len(fields), 2)}
        if "PARAMETER" in alternatives:
            parameter = alternatives["PARAMETER"]
            del alternatives["PARAMETER"]
            parameterized(parameter, query_file_name, description, alternatives, no_caching=args.nocache, counting=args.count)
        else:
            process(filename, query_file_name, description, alternatives, no_caching=args.nocache, counting=args.count)


parser = argparse.ArgumentParser()
parser.add_argument("filename", nargs="?", default=None, help="Name of file or directory containing queries")
parser.add_argument("-D", "--description", action='store', default="", help="Description")
parser.add_argument("-e", "--engine", action='append', type=str, choices=[engine[0] for engine in engines],
                    help="System to use (can be repeated)")
parser.add_argument("-d", "--directory", action='store', type=str, help="Directory with queries")
parser.add_argument("-C", "--nocache", action='store_true', help="Overcome caching (only changes QLever and Blazegraph)")
parser.add_argument("-c", "--count", action='store_true', help="Add enclosing SELECT to count results")
parser.add_argument("-v", "--verbose", action='store_true', help="Verbose output")
parser.add_argument("-P", "--nodups", action='store_true', help="Add DISTINCT to query to eliminate duplicates")
parser.add_argument("-s", "--skip", action='store', type=int, help="Skip first n queries")
args = parser.parse_args()

if args.engine:
    engines = [ engine for engine in engines if engine[0] in args.engine ]
skip = 0
if args.skip:
    skip = args.skip
    print(f"SKIPPING {skip} queries")

filename = "."
if args.filename:
    filename = args.filename.rstrip('/')
try:
    control_file = open(filename + '/queries.tsv', 'r')
except Exception:
    control_file = None

if control_file is not None:
    if args.verbose: 
        print(f"Evaluating queries from {queries_directory}{', counted,' if args.count else ''}")
        print(f"with caching {'allowed' if not args.nocache else 'disabled for QLever and Blazegraph'}\n")
        print(args.description)
    process_control_file(control_file, skip=skip)
else:
    if args.verbose: 
        print(f"Evaluating queries in {queries_directory}{', counted,' if args.count else ''}")
        print(f"with caching {'allowed' if not args.nocache else 'disabled for QLever and Blazegraph'}\n")
    process_queries_file(filename, args.description, no_caching=args.nocache, counting=args.count, skip=skip)




