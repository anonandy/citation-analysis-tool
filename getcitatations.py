
###################
# Interactive script that allows input of a file path 
# of a csv or txt file of dois, for example:
# "10.1002/admi.202000353 
# 10.1021/acschemneuro.7b00193"
# Output is a csv with columns: 
# doi | crossref citation count | openalex citation count | dimensions citation count| max citations | processed at time
# This script cleans links and gives search intervals to not reach API limits. 
# Be sure to import user agent email for ethical API usage.
#
# Script made with assistance of claude.ai

import pandas as pd
import requests
import time
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_dois_from_file(filepath):
    """Load DOIs from a text file (one DOI per line) or CSV file"""
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
            # Assume DOI column is named 'doi' or take the first column
            if 'doi' in df.columns:
                dois = df['doi'].dropna().astype(str).tolist()
            else:
                dois = df.iloc[:, 0].dropna().astype(str).tolist()
        else:
            # Text file - one DOI per line
            with open(filepath, 'r') as f:
                dois = [line.strip() for line in f if line.strip()]
        
        # Clean DOIs - remove any prefixes like "doi:" or "https://doi.org/"
        cleaned_dois = []
        for doi in dois:
            doi = doi.strip()
            if doi.startswith('https://doi.org/'):
                doi = doi.replace('https://doi.org/', '')
            elif doi.startswith('doi:'):
                doi = doi.replace('doi:', '')
            if doi:  # Only add non-empty DOIs
                cleaned_dois.append(doi)
        
        logger.info(f"Loaded {len(cleaned_dois)} DOIs from {filepath}")
        return cleaned_dois
    except Exception as e:
        logger.error(f"Error loading DOIs from {filepath}: {e}")
        return []

def get_dimensions_citations(doi, timeout=10):
    """Get citation count from Dimensions Metrics API"""
    try:
        # Dimensions Metrics API endpoint
        url = f"http://metrics-api.dimensions.ai/doi/{doi}"
        
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return data.get('times_cited', 0)
        elif response.status_code == 404:
            return 0
        else:
            logger.warning(f"Dimensions Metrics API error for {doi}: Status {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Dimensions error for {doi}: {e}")
        return None

def get_crossref_citations(doi, timeout=10):
    """Get citation count from CrossRef"""
    try:
        # CrossRef API endpoint
        url = f"https://api.crossref.org/works/{doi}"
        headers = {
            'User-Agent': 'Citation Analysis Tool (mailto:your-email@domain.com)'  # Replace with your email
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            if 'message' in data:
                return data['message'].get('is-referenced-by-count', 0)
        elif response.status_code == 404:
            return 0
        else:
            logger.warning(f"CrossRef API error for {doi}: Status {response.status_code}")
            return None
        return 0
    except Exception as e:
        logger.error(f"CrossRef error for {doi}: {e}")
        return None

def get_openalex_citations(doi, timeout=10):
    """Get citation count from OpenAlex"""
    try:
        # OpenAlex API endpoint
        url = f"https://api.openalex.org/works/doi:{doi}"
        
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return data.get('cited_by_count', 0)
        elif response.status_code == 404:
            return 0
        else:
            logger.warning(f"OpenAlex API error for {doi}: Status {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"OpenAlex error for {doi}: {e}")
        return None

def save_checkpoint(results, checkpoint_file):
    """Save results to checkpoint file"""
    try:
        df = pd.DataFrame(results)
        df.to_csv(checkpoint_file, index=False)
        logger.info(f"Checkpoint saved: {len(results)} records")
    except Exception as e:
        logger.error(f"Error saving checkpoint: {e}")

def load_checkpoint(checkpoint_file):
    """Load results from checkpoint file"""
    try:
        if os.path.exists(checkpoint_file):
            df = pd.read_csv(checkpoint_file)
            results = df.to_dict('records')
            logger.info(f"Checkpoint loaded: {len(results)} records")
            return results
        return []
    except Exception as e:
        logger.error(f"Error loading checkpoint: {e}")
        return []

def analyze_citations(doi_list, delay=2, checkpoint_interval=100, resume_from_checkpoint=True):
    """
    Analyze citations for a list of DOIs with rate limiting and checkpointing
    
    Parameters:
    - doi_list: List of DOIs to analyze
    - delay: Delay between API calls (seconds) - recommended 2-3 seconds
    - checkpoint_interval: Save progress every N DOIs
    - resume_from_checkpoint: Whether to resume from existing checkpoint
    """
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    checkpoint_file = f"citation_analysis_checkpoint_{timestamp}.csv"
    
    # Load existing checkpoint if resuming
    if resume_from_checkpoint:
        results = load_checkpoint(checkpoint_file)
        processed_dois = {result['doi'] for result in results}
        remaining_dois = [doi for doi in doi_list if doi not in processed_dois]
        logger.info(f"Resuming: {len(processed_dois)} already processed, {len(remaining_dois)} remaining")
    else:
        results = []
        remaining_dois = doi_list
    
    total_dois = len(doi_list)
    processed_count = len(results)
    
    logger.info(f"Starting citation analysis for {len(remaining_dois)} DOIs...")
    
    for i, doi in enumerate(remaining_dois, 1):
        current_progress = processed_count + i
        logger.info(f"Processing {current_progress}/{total_dois}: {doi}")
        
        # Get CrossRef citations (rate limit: ~50 requests per second)
        crossref_count = get_crossref_citations(doi)
        time.sleep(0.5)  # Small delay for CrossRef
        
        # Get OpenAlex citations (rate limit: 100,000 requests per day)
        openalex_count = get_openalex_citations(doi)
        time.sleep(0.5)  # Small delay for OpenAlex
        
        # Get Dimensions citations (rate limit: varies, be conservative)
        dimensions_count = get_dimensions_citations(doi)
        
        # Store results
        result = {
            'doi': doi,
            'crossref_citations': crossref_count,
            'openalex_citations': openalex_count,
            'dimensions_citations': dimensions_count,
            'max_citations': max(filter(None, [crossref_count, openalex_count, dimensions_count])) if any([crossref_count, openalex_count, dimensions_count]) else 0,
            'processed_at': datetime.now().isoformat()
        }
        results.append(result)
        
        # Save checkpoint periodically
        if i % checkpoint_interval == 0:
            save_checkpoint(results, checkpoint_file)
        
        # Rate limiting delay between DOIs
        if i < len(remaining_dois):
            time.sleep(delay)
    
    # Final save
    save_checkpoint(results, checkpoint_file)
    
    return pd.DataFrame(results)

def main():
    """Main function to run the citation analysis"""
    
    print("="*60)
    print("CITATION ANALYSIS TOOL")
    print("="*60)
    
    # Get input method
    input_method = input("Enter DOI input method:\n1. File path (txt or csv)\n2. Manual entry (comma-separated)\nChoice (1 or 2): ").strip()
    
    if input_method == "1":
        # File input
        filepath = input("Enter file path: ").strip()
        dois = load_dois_from_file(filepath)
        
        if not dois:
            print("No DOIs loaded. Exiting.")
            return
            
        if len(dois) > 6000:
            print(f"Warning: {len(dois)} DOIs found. Truncating to first 6000.")
            dois = dois[:6000]
            
    elif input_method == "2":
        # Manual entry
        doi_input = input("Enter DOIs (comma-separated): ").strip()
        dois = [doi.strip() for doi in doi_input.split(",") if doi.strip()]
        
        if len(dois) > 6000:
            print(f"Warning: {len(dois)} DOIs entered. Truncating to first 6000.")
            dois = dois[:6000]
    else:
        print("Invalid choice. Exiting.")
        return
    
    if not dois:
        print("No valid DOIs provided. Exiting.")
        return
    
    print(f"\nFound {len(dois)} DOIs to process")
    
    # Get delay setting
    delay_input = input(f"Enter delay between API calls in seconds (default 2, recommended 2-3): ").strip()
    delay = float(delay_input) if delay_input else 2.0
    
    # Get checkpoint interval
    checkpoint_input = input(f"Enter checkpoint interval (save progress every N DOIs, default 100): ").strip()
    checkpoint_interval = int(checkpoint_input) if checkpoint_input else 100
    
    # Confirm before starting
    estimated_time = len(dois) * delay / 60  # rough estimate in minutes
    print(f"\nEstimated time: {estimated_time:.1f} minutes")
    confirm = input("Start analysis? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("Analysis cancelled.")
        return
    
    # Run the analysis
    print("\nStarting citation analysis...")
    start_time = time.time()
    
    try:
        citation_df = analyze_citations(dois, delay=delay, checkpoint_interval=checkpoint_interval)
        
        # Display results
        print("\n" + "="*60)
        print("CITATION ANALYSIS RESULTS")
        print("="*60)
        print(citation_df.head(10).to_string(index=False))
        
        if len(citation_df) > 10:
            print(f"\n... showing first 10 of {len(citation_df)} results")
        
        # Summary statistics
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)
        print(f"Total DOIs processed: {len(citation_df)}")
        print(f"CrossRef mean citations: {citation_df['crossref_citations'].mean():.2f}")
        print(f"OpenAlex mean citations: {citation_df['openalex_citations'].mean():.2f}")
        print(f"Dimensions mean citations: {citation_df['dimensions_citations'].mean():.2f}")
        
        # Export final results
        output_filename = f"citation_analysis_final_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        citation_df.to_csv(output_filename, index=False)
        
        elapsed_time = time.time() - start_time
        print(f"\nAnalysis completed in {elapsed_time/60:.1f} minutes")
        print(f"Results saved to: {output_filename}")
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user. Progress has been saved to checkpoint file.")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"Analysis failed: {e}")

if __name__ == "__main__":
    main()