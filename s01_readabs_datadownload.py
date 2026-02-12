# s01_readabs_datadownload.py

import readabs as ra
import pandas as pd
import os
import sys
import logging
import argparse
from contextlib import redirect_stdout, redirect_stderr
import io

# --- IMPORT CONFIGURATION ---
try:
    from s00_readabs_datalist import ABS_DATASETS, HISTORY_YEARS, OUTPUT_DIRECTORY
except ImportError:
    print("Error: Could not find 's00_readabs_datalist.py'.")
    sys.exit(1)

# --- CLI ARGUMENT PARSER ---
def parse_args():
    parser = argparse.ArgumentParser(
        description='Download ABS data from specified catalogues'
    )
    parser.add_argument(
        '--freq',
        choices=['Monthly', 'Quarterly', 'Annual'],
        help='Only download datasets with this frequency'
    )
    parser.add_argument(
        '--cat',
        help='Only download specific catalogue ID (e.g., 6401.0)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        dest='list_only',
        help='List available datasets without downloading'
    )
    return parser.parse_args()


def filter_datasets(datasets, freq=None, cat=None):
    """Filter datasets based on frequency and/or catalogue ID."""
    filtered = datasets

    if freq:
        filtered = [d for d in filtered if d.get('frequency', '').lower() == freq.lower()]

    if cat:
        filtered = [d for d in filtered if d['cat_id'] == cat]

    return filtered


def list_datasets(datasets):
    """Print a formatted list of available datasets."""
    print("\n--- AVAILABLE ABS DATASETS ---\n")
    print(f"{'Cat ID':<12} {'Frequency':<12} {'Name':<40} {'Tables'}")
    print("-" * 90)

    for ds in datasets:
        cat_id = ds['cat_id']
        freq = ds.get('frequency', 'Unknown')
        name = ds['name']
        table_count = len(ds['tables'])

        print(f"{cat_id:<12} {freq:<12} {name:<40} {table_count} table(s)")

    print(f"\nTotal: {len(datasets)} dataset(s)")
    print("-" * 90)

def get_rows_to_keep(frequency, years):
    freq = str(frequency).lower()
    if "monthly" in freq: return years * 12
    elif "quarterly" in freq: return years * 4
    elif "half" in freq: return years * 2
    elif "yearly" in freq or "annual" in freq: return years * 1
    else: return years * 4 

def fetch_and_save_dataset(dataset_info):
    name = dataset_info['name']
    cat_id = dataset_info['cat_id']
    target_tables = dataset_info['tables']
    
    frequency = dataset_info.get('frequency', 'Quarterly')
    rows_to_keep = get_rows_to_keep(frequency, HISTORY_YEARS)

    print(f"\nProcessing: {name} (Cat: {cat_id}) | Freq: {frequency}")

    try:
        # 1. Download data 
        f = io.StringIO()
        with redirect_stdout(f), redirect_stderr(f):
            logging.getLogger().setLevel(logging.ERROR)
            download_result = ra.read_abs_cat(cat_id)
            logging.getLogger().setLevel(logging.WARNING)

        if not isinstance(download_result, tuple):
            print(f"  [X] Error: Unexpected return format for {cat_id}")
            return

        all_tables_dict = download_result[0]
        meta_df = download_result[1] 

        # 2. Build Description Mapping
        id_to_desc = {}
        if 'Data Item Description' in meta_df.columns:
            id_to_desc = meta_df['Data Item Description'].to_dict()

        # 3. LOOP THROUGH TABLES
        for key, value in target_tables.items():
            
            # --- HANDLE CONFIG FORMAT ---
            target_ids = []
            if isinstance(value, dict):
                filename = value['filename']
                target_ids = value.get('plot_ids', [])
            else:
                filename = value
            # ----------------------------

            if key not in all_tables_dict:
                print(f"  [X] Table '{key}' not found. Skipping.")
                continue

            df = all_tables_dict[key]

            # --- FILTER COLUMNS (NEW) ---
            # If the user provided specific IDs, we discard everything else right now.
            if target_ids:
                # Ensure headers are clean
                df.columns = df.columns.str.strip()
                
                # Find which of the requested IDs actually exist in this table
                found_cols = [c for c in df.columns if c in target_ids]
                
                if found_cols:
                    # Filter the dataframe to keep ONLY these columns
                    df = df[found_cols]
                    
                    # Check if we missed any
                    missing = set(target_ids) - set(found_cols)
                    if missing:
                        print(f"      [!] Warning: Could not find these IDs: {missing}")
                else:
                    print(f"      [!] Warning: No match for requested IDs. Saving full table instead.")
            # -----------------------------

            # Apply Descriptions (Renaming columns)
            try:
                new_col_names = []
                for col_id in df.columns:
                    desc = id_to_desc.get(col_id, "")
                    desc = str(desc).strip().replace('\n', ' ')
                    if desc:
                        new_col_names.append(f"{desc} ({col_id})")
                    else:
                        new_col_names.append(col_id)
                df.columns = new_col_names
            except Exception:
                pass

            # Filter Date Range
            if not df.index.is_monotonic_increasing:
                df = df.sort_index()
            filtered_df = df.tail(rows_to_keep)

            # Save
            if not os.path.exists(OUTPUT_DIRECTORY):
                os.makedirs(OUTPUT_DIRECTORY)

            output_path = os.path.join(OUTPUT_DIRECTORY, filename)
            filtered_df.to_csv(output_path)
            
            # Helper message to confirm filtering
            saved_cols_count = len(filtered_df.columns)
            print(f"  [OK] Saved: {filename} ({saved_cols_count} series)")

    except Exception as e:
        print(f"  [!] Failed to process {name}: {e}")

if __name__ == "__main__":
    args = parse_args()

    # Filter datasets based on CLI arguments
    datasets_to_process = filter_datasets(ABS_DATASETS, freq=args.freq, cat=args.cat)

    if not datasets_to_process:
        print("No datasets match the specified filters.")
        sys.exit(0)

    # List mode: show datasets and exit
    if args.list_only:
        list_datasets(datasets_to_process)
        sys.exit(0)

    # Download mode
    filter_info = []
    if args.freq:
        filter_info.append(f"Freq: {args.freq}")
    if args.cat:
        filter_info.append(f"Cat: {args.cat}")
    filter_str = f" ({', '.join(filter_info)})" if filter_info else ""

    print(f"--- ABS BATCH DOWNLOAD STARTED (History: {HISTORY_YEARS} Years){filter_str} ---")
    for item in datasets_to_process:
        fetch_and_save_dataset(item)
    print("\n--- BATCH DOWNLOAD COMPLETE ---")