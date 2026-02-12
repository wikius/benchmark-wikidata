#!/usr/bin/python
# Compare results of several different versions of a (counted) benchmark
# the first version is considered the reference and others are compared to it
# ./compare.py results-2020-oct/ results-2024-oct-single/ results-2025-oct-single/
# Options:  -o compare ontology benchmarks,
#	-s compare Scholia benchmarks,
#	-u compare unlimited WDbench benchmarks,
#	no option means compare existing benchmarks
# For other options see below
# Output fields:
# the part of the benchmark
# Count: the number of queries in the part - the number of lines in the reference results
# for the reference version
# Fail: the number of failures
# Time: the total time taken, in seconds
# Results: the total number of results
# for the other versions
# Fail: the ADDITIONAL failures
# Time/: the ratio of time taken on queries that did not fail in the reference, with failures for the other penalized
# Time: the total time taken for the other 
# Results: the total number of results fof the other
# Results/: the ratio of results on queries that did not fail in either

import sys
import re
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("dirs", nargs="+", help="Directories containing query results, with engine following comma")
parser.add_argument("-e", "--engine", default='QLever', help="Engine to use, if not in argument")
parser.add_argument("-b", "--benchmarks", action='append', help="Benchmark to use")
parser.add_argument("-d", "--detail", action='store_true', default=False, help="Show detailed information")
parser.add_argument("-r", "--ratio", type=int, default=1, help="Expected results ratio between first run and other runs")
parser.add_argument("-S", "--SCHOLIA", help="Scholia prefix")
parser.add_argument("-p", "--penalty", type=float, default=5.0, help="Penalty for failure; 0 is ignore")
type = parser.add_mutually_exclusive_group()
type.add_argument("-n", "--normal", action='store_true', help="Use normal, not counted runs")
type.add_argument("-N", "--nodups", action='store_true', help="Use noduplicates, not counted runs")
group = parser.add_mutually_exclusive_group()
group.add_argument("-s", "--scholia", action='store_true', default=False, help="Show Scholia results")
group.add_argument("-o", "--ontology", action='store_true', default=False, help="Show onology results")
group.add_argument("-u", "--unlimited", action='store_true', default=False, help="Use unlimited versions of benchmarks")
args = parser.parse_args()
if args.SCHOLIA is None:
    args.SCHOLIA = "SCHOLIA"

referencedir = args.dirs[0]
otherdirs = args.dirs[1:]

benchmarks = args.benchmarks
if args.benchmarks is None:
    benchmarks = [ 'wgpb', 'wdqs', 'single_bgps', 'multiple_bgps', 'opts', 'paths', 'c2rpqs' ]
    if args.unlimited:
        benchmarks = [ 'usingle_bgps', 'umultiple_bgps', 'uopts', 'upaths', 'uc2rpqs' ]
    if args.scholia:
        benchmarks = [ 'index', 'author', 'award', 'catalogue', 'chemical', 'chemical-class', 'chemical-element', 'clinical-trial', 'complex',
                       'country', 'dataset', 'disease', 'event', 'event-series', 'gene', 'ontology', 'organization', 'pathway',
                       'podcast', 'podcast-episode', 'podcast-season', 'project', 'property', 'protein', 'publisher',
	               'series', 'software', 'sponsor', 'taxon', 'topic', 'use', 'venue', 'wikiproject', 'work' ]
    if args.ontology:
        benchmarks = [ 'ontology-parameter', 'ontology-order' ]

def file(engine, benchmark, base):
    base = base.split(",")
    engine = base[1] if len(base)>1 else engine
    base = base[0]
    try:
        if args.scholia:
            return open(f"{base}/{args.SCHOLIA}-{benchmark}-{engine}.tsv")
        else:
            return open(f"{base}/{benchmark}-{"norm" if args.normal else "nodups" if args.nodups else "counted"}-{engine}.tsv")
    except FileNotFoundError:
        return None

tline = 0 # total number of queries
ttcount = 0 # total number of results for first benchmark
tttime = 0 # total time for first benchmark
tsuccess = 0 # total number of successful queries for first benchmark
ttcounts = {} # total number of results for other benchmarks
ttxcounts = {} # total number of results for first benchmark when other benchmark succeeds
tttimes = {} # total time for other benchmarks
tsuccesses = {} # total number of successful queries for other benchmarks
for otherdir in otherdirs:
    ttcounts[otherdir] = 0
    ttxcounts[otherdir] = 0
    tttimes[otherdir] = 0
    tsuccesses[otherdir] = 0


def print_summary(benchmark, lines, ttime, tcount, success, others, ttimes, tcounts, txcounts, successes):
    print(f"{benchmark:20} {lines:4} {lines-success:4} {ttime//1000:6,} {tcount:17,}  ", end='')
    for other in others:
        if successes[other]:
            print(f"|{success-successes[other]:5} {ttimes[other]/ttime:6.2f} {int(ttimes[other]//1000):6,} {tcounts[other]:17,} {tcounts[other]/txcounts[other] if txcounts[other] else 999.99:6.2f}", end='   ')
        else:
            print("|                                             ", end='  ')
    print()

# process a line in a results file
def process(ln, line):
    fields = line.strip().split('\t')
    if len(fields) < 6 or fields[5].strip() == "None" or len(fields) > 6 and int(fields[6]) >= 400:
        count = None
    else:
        count = re.findall(r'Count= (\d+)', fields[5].strip())
        count = int(count[0]) if len(count)>0 else None
        if count is None:
            count = re.findall(r'Result=(\d+)$', fields[5].strip())
            count = int(count[0]) if len(count)>0 else 1
    time = int(fields[3]) if count is not None else None
    note = fields[8] if len(fields) > 8 else ""
    return count, time, note

## ALSO KEEP TRACK of total successes on first benchmark only for successes on other benchmark
def compare_benchmark(benchmark):
    global tline, ttcount, tttime, tsuccess, ttcounts, txcounts, tttimes, tsuccesses
    reference = file(args.engine,benchmark,referencedir)
    if reference is None:
        return
    others = {} 
    tcount = 0 # total count for first benchmark
    ttime = 0  # total time for first benchmark
    success = 0 # total successes for first benchmark
    tcounts = {} # counts for other benchmarks
    txcounts = {} # counts for first benchmark when other benchmark succeeds
    ttimes = {} # total time for other benchmarks
    successes = {} # total successes for other benchmarks
    for otherdir in otherdirs:
        tcounts[otherdir] = txcounts[otherdir] = ttimes[otherdir] = successes[otherdir] = 0
        other = file(args.engine,benchmark,otherdir)
        others[otherdir] = other if other else None
    line = reference.readline()
    ln = 1
    while ( line ):
        count, time, note = process(ln, line)
        if args.detail:
            print(f"                      {ln:3}    {time:8} {count:17,} " if count is not None else f"                      {ln:3}        NONE              NONE ", end=' ')
        ttime += time if count is not None else 0
        tcount += count if count is not None else 0
        success += 1 if count is not None else 0

        for other in others:
            l = others[other].readline() if others[other] else ''
            fields = l.strip().split('\t')
            if len(fields) > 5:
                t = int(fields[3])
                if fields[5].strip() == "None" or int(fields[6]) >= 400:
                    c = None
                else:
                    c = re.findall(r'Count= (\d+)', fields[5].strip())
                    c = int(c[0]) if len(c)>0 else None
                    if c is None:
                        c = re.findall(r'Result=(\d+)$', fields[5].strip())
                        c = int(c[0]) if len(c)>0 else 1
            else:
                c = None
                t = 0
            if count is not None:
                ttimes[other] += t if c is not None else ( time if time is not None else 0 ) if args.penalty == 0.0  \
                    else min(600000, max(t, time * args.penalty)) # strong penalty
                tcounts[other] += c if c is not None else 0
                txcounts[other] += count if c is not None else 0
            if c is not None:
                successes[other] += 1
                if count is not None:
                    if args.detail:
                        print(f"    {t/time if time else 0:8.2f} {t:6}  {c - count*args.ratio:16,} {c/count if count and c/count < 1000 else 999.99 :6.2f}", end='   ')
                else:
                    if args.detail:
                        print(f"           {t:8} {c:17,}*      ", end='   ')
            else:
                if args.detail:
                    print(f"              NONE              NONE       ", end='   ')
        if args.detail:
            print(f"  {note}")
        line = reference.readline()
        ln += 1

    tline += ln - 1
    ttcount += tcount
    tttime += ttime
    tsuccess += success

    print_summary(benchmark, ln-1, ttime, tcount, success, others, ttimes, tcounts, txcounts, successes)

    for other in others:
        ttcounts[other] += tcounts[other]
        ttxcounts[other] += txcounts[other]
        tttimes[other] += ttimes[other]
        tsuccesses[other] += successes[other]


print(f"Benchmark            Count    {referencedir:28}", end=' ')
for dir in otherdirs:
    print(f"| - - {dir:30} - - |  ", end='   ')
print()
print(f"                           Fail  Time        Results", end='      ')
for dir in otherdirs:
    print(f" dFail Time/  Time        Results   Results/", end='   ')
print()

for benchmark in benchmarks:
    br = compare_benchmark(benchmark)
print_summary("TOTAL", tline, tttime, ttcount, tsuccess, otherdirs, tttimes, ttcounts, ttxcounts, tsuccesses)
