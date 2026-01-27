# Benchmarking Wikidata

Programs and data for benchmarking SPARQL queries on Wikidata. 
These are used in the [Scaling Wikidata](https://www.wikidata.org/wiki/Wikidata:Scaling_Wikidata/Benchmarking) project, to evaluate different potential Wikidata backends. 

Supported in part by two grants ([Phase 1](https://meta.wikimedia.org/wiki/Wikimedia_CH/Grant_apply/Scaling_Wikidata_by_benchmarking_QLever) and
[Phase 2](https://meta.wikimedia.org/wiki/Wikimedia_CH/Grant_apply/Scaling_Wikidata_through_Benchmarking,_Part_2))
from [Wikimedia CH](https://wikimedia.ch/). 


## Phase 1:  Evaluation of four SPARQL engines on Wikidata

The file PROCESSING contains a log of all the commands run to perform the benchmarks.  Not included in PROCESSING is the commands needed to run and stop the SPARQL engine being benchmarked.
This file also contains raw results for most of the runs and some analysis of the results that was later incorporated into the analysis pages under 

A few of the benchmarking runs caused crashes.  In these cases the run was restarted just before the crash and the outputs spliced together.  If the crash reoccured, the run was started after the crash and data on the crash was manually added.

Also present in PROCESSING is a log of the commands run to generate statistics and places where engines differ plus the output of these commands.

Results of the benchmarks are in results-original.  Results of cleaning up the Scholia benchmark to exclude non-standard queries are in results-clean.

Statistics for the existing benchmarks and Scholia benchmark are in stats-original:
* existing.text
* existing-errs.text
* existing-counted.text
* existing-counted-errs.text
* existing-nodups.text
* existing-nodups-errs.text
* scholia.text
* scholia-errs.text
* scholia-clean.text
* scholia-clean.md

### Results

Results of the runs are in directories that start with `results-`

The output of a run is a tab-separated values file with the following fields:
* number of query in the run
* engine used - QLever, etc.
* variant - '' for normal, COUNTED, NODUPS
* elapsed time in millseconds as measured by benchmark.py
* time reported by engine (almost always no information)
* result - None for some sort of error, `Result=` is first value for a single result, `Count=` is the number of results otherwise
* HTTP result code
* error information
* message provided for query

```
results-original
results-clean
results-second
results-third
results-current
results-iswc
```

### Reports

* [Phase 1 Final Report][https://www.wikidata.org/wiki/Wikidata:Scaling_Wikidata/Benchmarking/Final_Report]
* Benchmarking SPARQL Engines on Wikidata Queries at the 2025 Wikidata Workshop, ISWC-2025, November 2025, Nara, Japan



## Phase 2: 

The file Progress-second-phase.text has details on how the various versions of Wikidata were generated and where the results are stored.

Programs used in this phase:
* benchmark.py - perform a benchmark run
* run-existing - run all the exiting benchmarks
* run-ontology - run the ontology benchmark
* run-scholia - run the Scholia benchmark
* compare.py - compare the results of several benchmark runs on several versions

### Evaluation of QLever on doubled and historial Wikidata

Results directories:

The results are in directories of the form results-dump-qlever-doubling
where
* dump is 2020 for wikidata-20201109-all-BETA.ttl dump,
2024 for wikidata-20241028-all-BETA.ttl dump,
and 2025 for wikidata-20251021-all-BETA.ttl dump;
* qlever is mar for QLever version of March 2025 and oct for QLever version of October 2025; and
* doubling is single or empty for just Wikidata,
double-SS for the simple doubling, 
double-o1 with one-way ontology interleaving added,
double-o2 with two-way ontology interleaving added,
double-interleaved for the interleaved doubling,
and double-big for interleaved plus original Wikidata.

```
results-2020-mar
results-2020-oct
results-2024-mar-single
results-2024-mar-double-SS
results-2024-mar-double-o1
results-2024-mar-double-o2
results-2024-mar-double-big
results-2024-mar-double-interleaved
results-2024-oct-single
results-2025-oct-single
results-2025-oct-double-SS
```

For more information and results see the [doubling report]9https://www.wikidata.org/wiki/Wikidata:Scaling_Wikidata/Benchmarking/Phase_2_Doubling_Report).


### Evaluation of QLever on doubled and historial Wikidata

The results are in the directories

```
results-2025-nov-update
results-2025-nov-update-updating
```

For more information see the [updating report](https://www.wikidata.org/wiki/Wikidata:Scaling_Wikidata/Benchmarking/Phase_2_Update_Report).


### Evaluation of QLever with much main memory

The file Progress-second-phase-aws.text has details on how the benchmarking was performed on AWS instances and how the results files were created.

The results are in the directories

```
results-aws-ebs
results-aws-ssd
results-aws-ram
```

For more information see the [main-memory report](https://www.wikidata.org/wiki/Wikidata:Scaling_Wikidata/Benchmarking/Phase_2_Memory_Report).

