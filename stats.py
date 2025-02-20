#!/bin/python

# Compute statistics for a benchmark run on several engines / variants

# Open the files for each engine / variant
# For each query, i.e., for each line of each file
#  For each engine / variant
#   Extract time, result, code,
#   Determine whether engine / variant timed out (timeout)
#   Determine whether engine / variant had an error, including timeout, unsual output, known likely-wrong result, or HTTP error code (error)
#   Determine whether engine / variant returned a value different from the most-common value without producing an error (diverge)
#  Determine whether there is more than one non-error answer
# For each engine / variant
#  Compute statistics: min, Q1, median, Q3, max, mean
#  Count timeouts, reported errors, unreported errors, incorrect results
# See benchmark.py for description of input data files

## build dictionary with entry for each query
##   value is dictionary with entry for each engine / variant
##     value is dictionary with time, result, code, error, timeout, error string, correct (T/F/None)
## for each engine / variant
##   iterate over dictionary to build time array and counts
##   compute time statistics
##   print data

import csv
import sys
import statistics
import argparse

maxtime = 600000
truncated_time = 60000

data = dict()    

# process a row of input by putting it into the data dictionary
i = 0
def process_row(row):
    row_index = int(row[0])
    row_entry = data.get(row_index, None)
    global i
    i += 1
    if row_entry is None:
        row_entry = data[row_index] = dict()
    if len(row) >= 8:
        engine, variant, time, _, result, code, error_message = row[1:8]
    else:
        print(f"ERROR: row without 8 fields {row}")
        sys.exit()
    engine_index = f"{engine}/{variant}" if variant else engine
    if row_entry.get(engine_index, None) is not None:
        print(f"WARNING: repeating data for {row_index} {engine_index}")
    timeout = int(time) >= maxtime
    err = bool((error_message != "") or (result.strip() == "None") or int(code) >= 400 or timeout)
    if err and args.error: time = maxtime
    row_entry[engine_index] = { "time": int(time), "result": result.strip(), "code": int(code) if code != "None" else "500",
                                "error_message": error_message, "timeout": timeout,
                                "error": err }

# determine the result of a query and score engines, return whether all non-error answers agree
def process_query(index, query):
    real_results = []
    for engine, row in query.items():
        if row['error'] or row['timeout']:  
            continue # ignore errors
        if "100000" == row['result'].split('=')[-1].strip():
            continue # ignore common incorrect answer
        if engine.startswith("V") and "1048576" == row['result'].split('=')[-1].strip():
            continue # ignore Virtuoso maximum response size
        if row['result'].strip() != "None":
            real_results.append(row['result'])
    if len(real_results) == 0:
        real_result = None
        identical = True
    elif len(real_results) == 1:
        real_result = real_results[0]
        identical = True
    else:
        counts = dict()
        for result in real_results:
            counts[result.strip()] = counts[result.strip()] + 1 if result.strip() in counts else 1
        count = 0
        mode = None
        for key, value in counts.items():
            if value > count:
                mode, count = key, value
            elif value == count:
                mode = None
        real_result = mode if count > 1 else None
        identical = real_result is not None and count == len(real_results)
    query["result"] = real_result
    query["identical"] = identical
    for row in query.values():
        if isinstance(row, dict):
            row["correct"] = bool(not row["error"] and ( (real_result is None) or row["result"] == real_result ))
            row["diverge"] = bool(not row["correct"] and not row["error"])
    return not identical

def compute_engine_stats(data, engine):
    times = []
    incorrect = timeouts = errors = diverges = 0
    for index, entry in data.items():
        row = entry.get(engine, None)
        if row:
            times.append(row["time"])
            timeouts += row["timeout"]
            errors += row["error"]
            diverges += row["diverge"]
            incorrect += not row["correct"]
    mean = int(statistics.mean(times))
    tmean = int(statistics.mean([min(time,truncated_time) for time in times]))
    minimum = min(times)
    maximum = max(times)
    q = statistics.quantiles(times, method='exclusive')
    return(len(times), minimum, q, maximum, mean, tmean, incorrect, timeouts, errors, diverges)

def compute_stats(data, engines):
    stats = dict()
    for engine in engines:
        stats[engine] = compute_engine_stats(data, engine)
    return stats


def print_rows(print_all, timings):
    engines = set()
    for entry in data.values():
        for engine in entry.keys():
            if engine != 'identical' and engine != 'result': engines.add(engine)
    engines = list(engines)
    engines.sort()
    field_size = 19 + ( 7 if timings else 0 )
    if args.mediawiki:
        print('{| class="wikitable"')
        print("! ROW !! Mode !!", " !! ".join([f'colspan="{2 if timings else 1}" | {engine}' for engine in engines]))
    else:
        print("ROW  Mode Result           ", " ".join([f"{engine:{field_size}}" for engine in engines]))
    for row, entry in data.items():
        if not print_all and entry['identical']: 
            continue
        identical = ' ' if entry['identical'] else '*'
        if args.mediawiki:
            print(f"|-\n| {row:3}{identical} || {str(entry['result'])[0:18]}", end='')
        else:
            print(f"{row:3}{identical} {str(entry['result'])[0:18]:18}", end=' ')
        for engine in engines:
            if engine in entry:
                row = entry[engine]
                flag = "!" if row['error'] else " "
                flag = "*" if row['diverge'] else flag
                flag = " " if row['correct'] else flag
                if args.mediawiki:
                    if timings: print(f' || style="text-align:right;" | {row['time']}', end=' || ')
                    print(f"{flag}{str(row['result'][0:18])}", end= '')
                else:
                    if timings: print(f"{row['time']:7}", end='')
                    print(f"{flag}{str(row['result'][0:18]):18}", end= ' ')
            else:
                if args.mediawiki:
                    print(" || || " if timings else " || ", end='')
                else:
                    if timings: print("       ", end='')
                    print("                   ", end=' ')
        print("")
    if args.mediawiki:
        print("|}")

parser = argparse.ArgumentParser()
parser.add_argument("files", nargs="+", help="Name of file containing query results")
parser.add_argument("-v", "--verbose", action='count', default=0, help="Show query information")
parser.add_argument("-t", "--timings", action='store_true', help="Show timings for all queries with no errors")
parser.add_argument("-m", "--mediawiki", action='store_true', help="Output in mediawiki format")
parser.add_argument("-e", "--error", action='store_true', help="Use maxtime for any errors")
args = parser.parse_args()

for filename in args.files:
    with open(filename) as file:
        reader = csv.reader(file, delimiter='	')
        for row in reader:
            process_row(row)

difference_count = 0
for index, entry in data.items():
    difference_count += process_query(index, entry)

engines = []
for entry in data.values():
    for engine, row in entry.items():
        if isinstance(row, dict):
            engines.append(engine)
    break

stats = compute_stats(data, engines)

if args.mediawiki:
    print('{| class="wikitable" style="text-align: right;" \n! ENGINE !! Count !! min !! q1 !! q2 !! q3 !! max !! mean !! tmean !! wrong !! timeout !! error !! diverge')
else:
    print("ENGINE             Count   min     q1     q2     q3    max   mean  tmean wrong timeout err divergence")

for engine, stats in stats.items():
    if args.mediawiki:
        print(f'|-\n| style="text-align: right;" | {engine} || {stats[0]} || {stats[1]} || {int(stats[2][0])} || {int(stats[2][1])} || {int(stats[2][2])} || {stats[3]} || {stats[4]} || {stats[5]} || {stats[6]} || {stats[7]} || {stats[8]-stats[7]} || {stats[9]}')
    else:
        print(f"{engine:18} {stats[0]:>4} {stats[1]:>6} {int(stats[2][0]):>6} {int(stats[2][1]):>6} {int(stats[2][2]):>6} {stats[3]:>6} {stats[4]:>6} {stats[5]:>6} {stats[6]:>5} {stats[7]:>5} {stats[8]-stats[7]:>5} {stats[9]:>5}")
if args.mediawiki: print("|}\n")
#print(f"Number of queries with different non-error, non-suspect results: {difference_count:3}")


if args.verbose > 0:
    print_rows(args.verbose > 1, args.timings > 0)
