#!/usr/bin/python
# modify Wikidata Turtle dump file to interleave with shadow entities
import random
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("file", help="Wikidata Turtle dump file")
parser.add_argument("-s", "--shadow", action='store_true', help="Write shadow entities")
args = parser.parse_args()

i = 0
with open(args.file, 'r') as file:
    for line in file:
        if line.startswith('@prefix '):
            if line.startswith('@prefix wd: '):
                if args.shadow:
                    print('@prefix wd: <http://www.wikidata.org/entityS/> .')
                    print('@prefix wdS: <http://www.wikidata.org/entity/> .')
                else:
                    print('@prefix wd: <http://www.wikidata.org/entity/> .')
                    print('@prefix wdS: <http://www.wikidata.org/entityS/> .')
            elif args.shadow:
                if line.startswith('@prefix data: '):
                    print('@prefix data: <https://www.wikidata.org/wiki/Special:EntityDataS/> .')

                    print('@prefix s: <http://www.wikidata.org/entityS/statement/> .')
                else:
                    print(line, end='')
            else:
                if line.startswith('@prefix s: '):
##?                    print('@prefix s: <http://www.wikidata.org/entityX/statement/> .')
                    pass
                else:
                    print(line, end='')
        elif random.randrange(10) < 7:
            print(line, end='')
        else:
            print(line.replace(' wd:',' wdS:'), end='')
        i += 1
