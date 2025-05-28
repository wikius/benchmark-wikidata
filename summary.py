#!/bin/python
# read a file with multiple statistical outputs and generate a summary

import sys
import argparse
import subprocess
import math

engines = [ 'Blazegraph', 'MilleniumDB', 'QLever', 'Virtuoso' ]
stats = { engine: dict(rank=0, speed=0, slow=0, errs=0, tos=0, divs=0) for engine in engines }

print("                 ", end='')
for engine in engines:
    print(f"               {engine:16}    ", end='')
print()
print("                  ", end='')
for engine in engines:
    print(f"   Speed Rank  Slow Log Err  TO Div", end='')
print()

def ranking(count, speeds, errs, tos, divs, category):
    best = min(speeds.values())
    ranks = [k for (k,v) in sorted(speeds.items(), key=lambda item: item[1])]
    print(f" {category[:17]:18}", end='')
    for engine in engines:
        if engine in ranks:
            rank = ranks.index(engine)+1
            speed = speeds[engine]
#            slow = ( count * (speed - best) ) // 1000
            slow = ( (speed - best) )
            ratio = speeds[engine] / best
            print(f"{speed:7} {rank:2} {slow:7} {math.log(ratio,10):3.1f} {errs[engine]:3} {tos[engine]:3} {divs[engine]:3}", end=' ')
            stats[engine]["rank"] += rank
            stats[engine]["speed"] += speed
            stats[engine]["slow"] += slow
            stats[engine]["errs"] += errs[engine]
            stats[engine]["tos"] += tos[engine]
            stats[engine]["divs"] += divs[engine]
        else:
            print(f"                                ", end='   ')
    print()

parser = argparse.ArgumentParser()
parser.add_argument("file", help="Name of file containing query statistics")
parser.add_argument("-f", "--field", default=None, help="Field to use")
parser.add_argument("-t", "--total_times", action='store_true', help="Use total time, not mean")
args = parser.parse_args()

category = ''
with open(args.file, 'r') as file:
    line = file.readline()
    while line:
        fields = line.split()
        if len(fields) > 1 and fields[0] == "CATEGORY":
            category = fields[1]
        if line and fields and fields[0].split('/')[0] in engines:
            speeds = dict()
            errs = dict()
            tos = dict()
            divs = dict()
            while line and fields and fields[0].split('/')[0] in engines:
                count = int(fields[1])
                speeds[fields[0].split('/')[0]] = int(fields[int(args.field)])
                if args.total_times:
                    speeds[fields[0].split('/')[0]] *= int(fields[int(1)]) 
                errs[fields[0].split('/')[0]] = int(fields[10])
                tos[fields[0].split('/')[0]] = int(fields[9])
                divs[fields[0].split('/')[0]] = int(fields[11])
                line = file.readline()
                fields = line.split()
#            print("SPEEDS", speeds)
            ranking(count, speeds, errs, tos, divs, category)
        line = file.readline()

print(" TOTALS           ", end='')
for engine in engines:
    print(f" {(stats[engine]['speed']):7} {stats[engine]['rank']:2} {(stats[engine]['slow']):7} --- {(stats[engine]['errs']):3} {(stats[engine]['tos']):3} {(stats[engine]['divs']):3}", end="")
print()
