#!/usr/bin/python
# extract scholarly publication items from Wikidata dump
# - looks for truthy instance of values from a list of clases or truthy value for P13046
# - this is slightly more resrictive than the actual split, but the difference should be ver minor
# makes several assumptions about the dump format
# - all the information about an item is together
# - the first line of an item ends with " a schema:Dataset ;"
# - all instance of truthy values are together
# - the first instance of line has 'wdt:P31 '
# - instance of values are one per line
# - the last instance of line ends with ';'
# See https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/WDQS_graph_split/Rules


import sys
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument("file", help="Wikidata Turtle dump file")
args = parser.parse_args()

scholarly_classes = [
    "wd:Q13442814",
    "wd:Q7318358",
    "wd:Q2782326",
    "wd:Q815382",
    "wd:Q1348305",
    "wd:Q187685",
    "wd:Q1907875",
    "wd:Q18918145",
    "wd:Q1266946",
    "wd:Q23927052",
    "wd:Q1504425",
    "wd:Q45182324",
    "wd:Q1402850",
    "wd:Q7316896",
    "wd:Q580922",
    "wd:Q30749496",
    "wd:Q111475835",
    "wd:Q92998777",
    "wd:Q114613919",
    "wd:Q798134",
    "wd:Q1385450",
    "wd:Q10885494",
    "wd:Q51282918",
    "wd:Q51282711",
    "wd:Q111475860",
    "wd:Q51283092",
    "wd:Q15706459",
    "wd:Q59387148",
    ]

scholarly_counts = { clss: 0 for clss in scholarly_classes }

block = ''  # current block - lines for an item (or some non-item, but they will not be recognized as scholarly)
scholarly = None  # current item is scholarly, is not scholarly, or it is unknown (None) - currently the second is not possible
classes = False # in values for P31 section

log_file = open('/tmp/scholarly-log.text', 'w')
log_file.write(str(scholarly_counts))
log_file.write('\n')

i = 0
with open(args.file, 'r') as file:
    i += 1
    if i > 10000:
        exit()
    for line in file:
        if line.startswith('@prefix '):  # copy over prefix lines
            print(line, end='')
            continue
        if line.endswith(" a schema:Dataset ;\n"):  # new block (almost always an item)
            if scholarly is True:  # print previous block if it is scholarly
                print(block, end='')
            block = ''
            scholarly = None
            classes = False
##            print("BLOCK  ", scholarly, classes, line, end='')
        if scholarly is not False:  # only process line if might be in scholarly block
            block += line
            if scholarly is None:  # if scholarly is unknown, check for types and publication property
                if "wdt:P13046 " in line:
                    scholarly = True
##                    print("PUBLICN", scholarly, classes, line, end='')
                    continue
                if 'wdt:P31 ' in line: # beginning of instance of values
##                    print("CLASSES", scholarly, classes, line, end='')
                    classes = True
                if classes:  # get class and check if in list of scholarly classes
                    match = re.search(r'wd:Q\d+',line) # get the class
##                    print("CLASS  ", scholarly, classes, line, end='')
                    if match and match.group(0) in scholarly_classes:
                        scholarly_counts[match.group(0)] += 1
                        scholarly = True
                    if line.endswith(';\n') or line.endswith('.\n'):  # end of instance of block
                        classes = False
##                        print("END    ", scholarly, classes)
                        # scholarly = False # can't make decision because might be a P13046 statement
    if scholarly is True:  # print last block if it is scholarly
        print(block, end='')

log_file.write(str(scholarly_counts))
log_file.write('\n')
