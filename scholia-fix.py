#!/usr/bin/python

# Translate a Scholia Blazegraph SPARQL template to a standard SPARQL template
# This code uses matching, not parsing, and thus can break, but it should work for Scholia queries
# Assumes easy syntax

# Phase 1: expand INCLUDE %xxxx with the WITH { ... } AS %xxxx
# First create a map for the WITH sections
# Second replace INCLUDE %xxxx by the appropriate WITH

# Phase 2: replace label service
# First find all the ?xxxLabel variables
# Second replace label serice call with OPTIONAL { ... } for all of the label variables

# Phase 3: remove hints

# Note: fails on event-series_timeline.sparql need to add extra } in two places


import sys
import re


prefixes = """PREFIX bd: <http://www.bigdata.com/rdf#>
PREFIX cc: <http://creativecommons.org/ns#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX ontolex: <http://www.w3.org/ns/lemon/ontolex#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
PREFIX pqn: <http://www.wikidata.org/prop/qualifier/value-normalized/>
PREFIX pqv: <http://www.wikidata.org/prop/qualifier/value/>
PREFIX pr: <http://www.wikidata.org/prop/reference/>
PREFIX prn: <http://www.wikidata.org/prop/reference/value-normalized/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX prv: <http://www.wikidata.org/prop/reference/value/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX psn: <http://www.wikidata.org/prop/statement/value-normalized/>
PREFIX psv: <http://www.wikidata.org/prop/statement/value/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdata: <http://www.wikidata.org/wiki/Special:EntityData/>
PREFIX wdno: <http://www.wikidata.org/prop/novalue/>
PREFIX wdref: <http://www.wikidata.org/reference/>
PREFIX wds: <http://www.wikidata.org/entity/statement/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wdtn: <http://www.wikidata.org/prop/direct-normalized/>
PREFIX wdv: <http://www.wikidata.org/value/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""

# find first balanced bracketed part of string
def balanced(string, offset, left, right):
    start = end = None
    level = 1
    current = offset
#    print("BALANCED", offset)
    while current < len(string):
        current = current + 1
        if string[current-1] == left:
            start = current-1
            break
#    print("START", start, current, string[start])
    while current < len(string):
#        print("CURRENT", current, string[current], string[current] == left, string[current] == right),
        if string[current] == left:
            level = level + 1
#            print("LEFT", current, level)
        if string[current] == right:
            level = level - 1
#            print("RIGHT", current, level)
            if level == 0:
                end = current
                break
        current = current + 1
#    print("BALANCED", start, end)
    return start, end

def expand(query):
    map = dict()
    while True:
        start = query.find("WITH")
        if start < 0:
            break
        estart, eend = balanced(query, start, '{', '}')
        if eend is None:
            print(f"CAN'T FIND BALANCED EXPANSION AFTER {start}")
            exit()
        expand = query[estart: eend+1]
        pattern = re.compile("AS +(%[a-zA-Z0-9_]+)[ \t\n]")
        match = pattern.search(query, eend)
        if not match:
            print(f"NO MATCH {start} {estart} {eend} {query.replace('\n', ' ')}")
            exit()
        token = match.group(1)
        query = query[:start] + query[match.end():]
        map[token] = expand
#        print("EXPAND", token, expand.replace('\n', ' '))
#    print("EXPANSIONS", map.keys())
    while True:
        pattern = re.compile("INCLUDE +(%[a-zA-Z0-9_]+)[ \t\n]")
        include = pattern.search(query)
        if not include:
            break
#        print("INCLUDE", include.start(), include.end(), include.group(1))
        ## look for # in line
        c = include.start()
        while c >= 0 and query[c] != '\n' and query[c] != '#':
            c = c - 1
        if query[c] == '#':  # comment line, splice out INCLUDE
            query = query[:include.start()] + query[include.end(1):]
            continue
#        print("EXPANDING", include.group(1), map[include.group(1)].replace('\n', ' '))
        if include.group(1) not in map:
            print(f"{include.group(1)} NOT IN MAP")
            exit()
        query = query[:include.start()] + map[include.group(1)] + query[include.end()+1:]
    return query

def label(variable):
    var = variable[:-5]
    return f"OPTIONAL {{ {var} rdfs:label {variable} .  FILTER ( lang({variable}) = 'en' ) }}"

def service(query):
    lvar = re.compile("[?][a-zA-Z0-9_]+Label")
    lvars = set(lvar.findall(query))
#    print("label variables", lvars)
    serv = re.compile("SERVICE *wikibase:label", re.I)
    match = serv.search(query)
    if not match:
        return query
    lstart, lend = balanced(query, match.start(), '{', '}')
    if lend is None:
        print(f"CAN'T FIND BALANCED EXPANSION AFTER {start}")
        exit()
#    print("SERVICE", match.start(), lstart, lend, query[match.start():lend+1])
    query = query[:match.start()] + '\n  '.join([label(v) for v in lvars]) + query[lend+1:]
    return query

def hint(query):
    hint = re.compile("hint:[^\n]+\n")
    return re.sub(hint, '\n', query)

with open(sys.argv[1]) as f: query = f.read()
query = expand(query)
query = service(query)
query = hint(query)

with open(sys.argv[1].replace('sparql', 'template'), 'w') as f:
    f.write(prefixes)
    f.write(query)
    print(sys.argv[1].replace('sparql', 'template'))
