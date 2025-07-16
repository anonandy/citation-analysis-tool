# Citation Analysis Tool
This python script takes up to 6000 DOIs and grabs the citation count across multiple academic databases (CrossRef, OpenAlex, Dimensions).

## Overview
This tool processes DOI lists and retrieves citation counts from three major academic databases, providing analysis of citation metrics for research impact evaluation.

## Features
- Multi-source citation retrieval (CrossRef, OpenAlex, Dimensions)
- Batch processing with rate limiting
- Progress checkpointing for large datasets
- Export to CSV format
- Error handling and logging

## Installation

### Using Conda (Recommended)
```bash
conda env create -f environment.yml
conda activate biblio_env
```
### Using pip
```bash
pip install -r requirements.txt
```

## Running the Analysis
#### Input Formats

1. Text file: One DOI per line
2. CSV file: DOI column header required

#### API Rate Limits as of 7/2025

CrossRef: ~50 requests/second 

OpenAlex: 100,000 requests/day

Dimensions: Variable (conservative approach recommended)

#### Output Format

- doi: Digital Object Identifier 
- crossref_citations: Citation count from CrossRef
- openalex_citations: Citation count from OpenAlex
- dimensions_citations: Citation count from Dimensions
- max_citations: Highest count across all sources
processed_at: Timestamp of processing


### Dependencies

- pandas: Data manipulation
- requests: API calls

## Running Analysis 

Load dependencies

With conda (recommended):
```
conda create --name <env> --file requirements.txt
```

With pip:
```
pip install -r requirements.txt
```

Run script 

``` bash
python getcitatations.py 
```
## Output and Interaction Example
```
============================================================
CITATION ANALYSIS TOOL
============================================================
Enter DOI input method:
1. File path (txt or csv)
2. Manual entry (comma-separated)
Choice (1 or 2): 
```
manually enter choice 

```
> 1
```
manually enter file path 
```
Enter file path: ./data/input/testtxt.txt
2025-07-16 16:17:29,951 - INFO - Loaded 3 DOIs from ./data/input/testtxt.txt

Found 3 DOIs to process
Enter delay between API calls in seconds (default 2, recommended 2-3): 2
Enter checkpoint interval (save progress every N DOIs, default 100): 

Estimated time: 0.1 minutes
Start analysis? (y/n): 
```
confirm start analysis
```
> y

Starting citation analysis...
2025-07-16 16:17:39,601 - INFO - Resuming: 0 already processed, 3 remaining
2025-07-16 16:17:39,602 - INFO - Starting citation analysis for 3 DOIs...
2025-07-16 16:17:39,602 - INFO - Processing 1/3: DOI
2025-07-16 16:17:43,009 - INFO - Processing 2/3: 10.1126/science.1127344
2025-07-16 16:17:46,417 - INFO - Processing 3/3: 10.1038/nature12354
2025-07-16 16:17:47,793 - INFO - Checkpoint saved: 3 records

============================================================
CITATION ANALYSIS RESULTS
============================================================
                    doi  crossref_citations  openalex_citations  dimensions_citations  max_citations               processed_at
                    DOI                   0                   0                     0              0 2025-07-16T16:17:41.006164
10.1126/science.1127344                7578                8431                  8020           8431 2025-07-16T16:17:44.415434
    10.1038/nature12354                6055                6451                  6178           6451 2025-07-16T16:17:47.789435

============================================================
SUMMARY STATISTICS
============================================================
Total DOIs processed: 3
CrossRef mean citations: 4544.33
OpenAlex mean citations: 4960.67
Dimensions mean citations: 4732.67

Analysis completed in 0.1 minutes
Results saved to: citation_analysis_final_20250716_161747.csv```

```

