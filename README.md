# Benchmarking Wikidata

Programs and data for benchmarking SPARQL queries on Wikidata. 
These are used in the [Scaling Wikidata](https://www.wikidata.org/wiki/Wikidata:Scaling_Wikidata/Benchmarking) project, to evaluate different potential Wikidata backends. 

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

Supported in part by a [grant](https://meta.wikimedia.org/wiki/Wikimedia_CH/Grant_apply/Scaling_Wikidata_by_benchmarking_QLever) from [Wikimedia CH](https://wikimedia.ch/). 
