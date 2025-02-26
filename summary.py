#!/bin/python
# read a file with multiple statistical outputs

import sys
import argparse
import subprocess
import math

engines = [ 'Blazegraph', 'MilleniumDB', 'QLever', 'Virtuoso' ]
stats = { engine: dict(rank=0, speed=0, slow=0, errs=0) for engine in engines }

print("                 ", end='')
for engine in engines:
    print(f"           {engine:16}", end='')
print()
print("                  ", end='')
for engine in engines:
    print(f"   Speed Rank  Slow Err Log", end='')
print()

def ranking(count, speeds, errs, category):
    best = min(speeds.values())
    ranks = [k for (k,v) in sorted(speeds.items(), key=lambda item: item[1])]
    print(f" {category[:17]:17}", end=' ')
    for engine in engines:
        if engine in ranks:
            rank = ranks.index(engine)+1
            speed = speeds[engine]
#            slow = ( count * (speed - best) ) // 1000
            slow = ( (speed - best) )
            ratio = speeds[engine] / best
            print(f"{speed:7} {rank:2} {slow:7} {errs[engine]:3} {math.log(ratio,10):3.1f}", end=' ')
            stats[engine]["rank"] += rank
            stats[engine]["speed"] += speed
            stats[engine]["slow"] += slow
            stats[engine]["errs"] += errs[engine]
        else:
            print(f"                        ", end='   ')
    print()

parser = argparse.ArgumentParser()
parser.add_argument("file", help="Name of file containing query statistics")
parser.add_argument("-f", "--field", default=None, help="Field to use")
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
            while line and fields and fields[0].split('/')[0] in engines:
                count = int(fields[1])
                speeds[fields[0].split('/')[0]] = int(fields[int(args.field)])
                errs[fields[0].split('/')[0]] = int(fields[10])
                line = file.readline()
                fields = line.split()
#            print("SPEEDS", speeds)
            ranking(count, speeds, errs, category)
        line = file.readline()

print(" TOTALS         ", end='')
for engine in engines:
    print(f"  {(stats[engine]['speed']):7} {stats[engine]['rank']:3} {(stats[engine]['slow']):7} {(stats[engine]['errs']):3}", end="  ")
print()
