#!/usr/bin/python
# Run a SPARQL test manifest
# ./run-manifest.py <directory> <engine>
# needs to be run on getafix, because it uses engine control scripts there
# needs to be run in a superdirectory of the data files to allow Virtuoso to load them
# needs to be run in a directory that has empty.ttl to allow Virtuoso to load it

# This code represents query results in two ways:
# 1/ As an RDF structure that represents a SPARQL solution sequence, the value of qt:answers
# A SPARQL solution sequence is repreesnted as an RDF list of SPARQL solutions.
# A SPARQL solution is represented as an RDF list of SPARQL bindings.
# A SPARQL binding is represented as a node with qt:variable and qt:value values.
# 2/ As an rdf:JSON value, the value of qt:json_answers


import sys
import subprocess
import csv
import time
import requests
import io
import json
import os
import rdflib
import xml.etree.ElementTree as ET

script_directory = "/home/local/scripts/"

manifest_query = """PREFIX rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX mf: <http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#>
PREFIX qt: <http://www.w3.org/2001/sw/DataAccess/tests/test-query#>
SELECT ?entry ?category ?name ?data ?query ?result WHERE {
  ?x rdf:type mf:Manifest .
  ?x mf:entries/rdf:rest*/rdf:first ?entry .
  ?entry rdf:type ?category .
  ?entry mf:action/qt:query ?query .
  OPTIONAL { ?entry mf:action/qt:data ?data .
             ?entry mf:result ?result . }
  ?entry mf:name ?name .
}"""
    
prefixes = '''@prefix earl: <http://www.w3.org/ns/earl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix doap: <http://usefulinc.com/ns/doap#> .
@prefix foaf: <http://xmlns.com/foaf/1.0/> .
@prefix dct: <http://purl.org/dc/terms/> .
@prefix qt: <http://www.w3.org/2001/sw/DataAccess/tests/test-query#> .
'''

preamble = '''
_:pfps rdf:type foaf:Person ;
       foaf:name "Peter F. Patel-Schneider" .

_:engine doap:name "engine" ; rdf:type doap:Project .
'''

test_preamble = '''
[] rdf:type earl:Assertion ;
   earl:assertedBy _:pfps ;
'''

def sanitize(name, mapping):
    if name in mapping:
        return mapping[name]
    else:
        mapped = '_:e' + str(len(mapping))
        mapping[name] = mapped
        return mapped

def value_to_earl(value, mapping):
    val = value["value"]
    if value['type'] == 'uri':
        return f'<{val}>'
    elif value['type'] == 'bnode':
        return sanitize(val, mapping)
    elif value.get('datatype', None) is not None:
        return f'"{val}"^^<{value["datatype"]}>'
    elif value.get('xml:lang', None) is not None:
        return f'"{val}"@{value["xml:lang"]}'
    else:
        return f'"{val}"'

def row_to_earl(row):
    mapping = dict()
    result = ''
    for variable, value in row.items():
        result = f'{result} [ qt:variable "{variable}" ; qt:value {value_to_earl(value, mapping)} ]'
    return f'( {result} )'

def answer_to_earl(answer):
    rows = answer["results"]["bindings"]
    result = ''
    for row in rows:
        result = result + ' ' + row_to_earl(row)
    return f'( {result} )'

def earl_record(file, engine, entry, name, result, success):
    file.write(test_preamble)
    file.write(f'   earl:subject _:{engine} ;\n')
    file.write(f'   earl:test <{entry}> ;\n')
    file.write(f'   dct:title "{name}" ;\n')
    outcome = 'cantTell' if success is None else 'passed' if success else 'failed'
    if result is not None:
        file.write(f'   qt:answers {answer_to_earl(result)} ;\n')
        json_output = json.dumps(result).replace("'", "\\'")
        file.write(f"   qt:json '{json_output}'^^rdf:JSON ;\n")
    file.write(f'   earl:result [ rdf:type earl:TestResult ; earl:outcome earl:{outcome} ] .\n')
    file.flush()

def evaluate_query_rdflib(engine, directory, data_file, query, result_format):
    g = rdflib.Graph()
    data_file = directory + data_file if data_file else "./empty.ttl"
    g.parse(data_file)
    try:
        query_result = g.query(query)
        form = "csv" if result_format == "text/csv" else "json"
        result = query_result.serialize(format=form).decode("utf-8")
        return 200, result
    except Exception as e:
        print(f'Could not run {engine}: {e}')
        return 400, str(e)

def evaluate_query_requests(engine, directory, data_file, query, result_format):
    data_file = directory + data_file if data_file else "./empty.ttl"
    subprocess.run([script_directory + engine + "-load", data_file])
    time.sleep(15)  # this is the best that can be done without a lot of effort
    if engine == "BlazeGraph":
        headers={"Accept": result_format}
    else:
        headers={"Accept": result_format, "Content-type": "application/sparql-query"}
    try:
        reply = requests.get(engines[engine][1], headers=headers, params={"query": query, "timeout": "60s"})
        return reply.status_code, reply.text
    except Exception as e:
        print(f'Could not run {engine}: {e}')
        return None, None

engines = {
    "BlazeGraph":   [evaluate_query_requests, "http://getafix:9999/bigdata/sparql"], 
    "MillenniumDB": [evaluate_query_requests, "http://getafix:1234/sparql"], 
    "QLever":       [evaluate_query_requests, 'http://getafix:7001'],
    "Virtuoso":     [evaluate_query_requests, "http://getafix:8890/sparql"],
    "rdflib":       evaluate_query_rdflib,
}

def evaluate_query(engine, directory, data_file, query, result_format):        
    method = engines[engine]
    if isinstance(method, list):
        return method[0](engine, directory, data_file, query, result_format)
    else:
        return method(engine, directory, data_file, query, result_format)

def json_value(binding):
    if binding.tag == "{http://www.w3.org/2005/sparql-results#}literal":
        if binding.attrib["xml:lang"]:
            return { "type": "literal", "value": binding.text, "xml:lang": binding.attrib["xml:lang"] }
        elif binding.attrib["datatype"]:
            return { "type": "literal", "value": binding.text, "datatype": binding.attrib["datatype"] }
        else:
            return { "type": "literal", "value": binding.text }
    elif binding.tag == "{http://www.w3.org/2005/sparql-results#}bnode":
        return { "type": "bnode", "value": binding.text }
    else:
        return { "type": "uri", "value": binding.text }

def convert_xml(specified_file):
    tree = ET.parse(specified_file).getroot()
    variables = tree.findall("./{http://www.w3.org/2005/sparql-results#}head/{http://www.w3.org/2005/sparql-results#}variable")
    variables = [v.attrib['name'] for v in variables]
    rows = tree.findall("./{http://www.w3.org/2005/sparql-results#}results/{http://www.w3.org/2005/sparql-results#}result")
    bindings = [ { binding.attrib["name"]: json_value(binding[0]) for binding in row } for row in rows ]
    result = { "head": { "vars": variables },
               "results": { "bindings": bindings } }
    return result

def mappable(a1, a2, mapping):
    emapping = dict(mapping)
    for var, val in a1.items():
        if var not in a2:
            return False
        if val["type"] != "bnode":
            if a2[var] == val:
                continue
            else:
                return False
        elif a2[var]["type"] != "bnode":
            return False
        elif emapping.get(val["value"], None) is None:
            emapping[val["value"]] = a2[var]["value"]
            continue
        elif emapping[val["value"]] == a2[var]["value"]:
            continue
        else:
            return False
    return emapping

def equivalent_answer_sets(as1, as2, mapping = dict()):
    if not as1:
        return not as2
    a1 = as1[0]
    for i in range(0,len(as2)):
        emapping = mappable(a1, as2[i], mapping)
        if isinstance(emapping, dict):
            if equivalent_answer_sets(as1[1:], as2[:i] + as2[i+1:], emapping):
                return True
    return False

def log_test(engine, success, status_code, text, result, specified_bindings):
    if status_code != None and status_code != 200:
        print(f"FAIL ERROR from {engine}: Status Code: {status_code} Text: {text.replace('\n', ' ')}")
    elif result is None:
        print(f"FAIL ERROR in parsing output from {engine} {text}")
    elif not success:
        print("FAIL ACTUAL   ", len(result["results"]["bindings"]), result["results"]["bindings"])
        if specified_bindings is not None:
            print("     SPECIFIED", len(specified_bindings), specified_bindings)
    if success:
        print("PASS")

def get_specified_bindings(directory, specified_result_file):
    specified_bindings = None
    if specified_result_file:
        srfile, srext = os.path.splitext(specified_result_file)
        if srext == '.srx':
            specified = convert_xml(directory + specified_result_file)
            specified_bindings = specified["results"]["bindings"]
        elif srext == '.srj':
            with open(directory + specified_result_file) as file:
                specified = json.load(file)
            specified_bindings = specified["results"]["bindings"]
        else:
            print(f"Unimplemented SPARQL Results File Type for {specified_result_file}")
    return specified_bindings


def run_test(engine, entry, category, name, directory, data_file, query_file, specified_result_file):
    specified_bindings = get_specified_bindings(directory, specified_result_file)

    with open(directory + query_file, 'r') as f:
        query = f.read()
    status_code, text = evaluate_query(engine, directory, data_file, query, "application/sparql-results+json")
    result = None
    if status_code == 200 :
        try:
            result = json.loads(text)
        except Exception:
            pass

    if category == "http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#PositiveSyntaxTest":
        success = status_code == 200
    if category == "http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#NegativeSyntaxTest":
        success = status_code != 200
    if category == "http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#QueryEvaluationTest":
        success = None
        if result is not None and specified_bindings is not None:
            success = equivalent_answer_sets(result["results"]["bindings"], specified_bindings)

    earl_record(earl, engine, entry, name, result, success)
    log_test(engine, success, status_code, text, result, specified_bindings)


def run_tests(directory, engine):
    print("RUNNING TESTS IN", directory, "ON", engine, end="\n\n")
    directory = directory.rstrip('/') + '/'
    _, tests = evaluate_query("QLever", directory, "manifest.ttl", manifest_query, "text/csv")
    f = io.StringIO(tests)
    reader = csv.reader(f, delimiter=',')
    next(reader)
    for row in reader:
        entry, category, name, data, query, result = row
        print(entry, name, data, query, result)
        run_test(engine, entry, category, name, directory, data, query, result)
        print()

directory = sys.argv[1]
engine = sys.argv[2]

with open('results-' + engine + '.earl', 'a', 1) as earl:
    earl.write(prefixes)
    earl.write(preamble.replace('engine', engine))
    run_tests(directory, engine)
    earl.write('\n\n\n')
