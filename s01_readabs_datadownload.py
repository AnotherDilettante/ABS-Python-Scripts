# s01_readabs_datadownload.py
import readabs as ra
import pandas as pd
import os
import sys
import logging
from contextlib import redirect_stdout, redirect_stderr
import io

# --- IMPORT CONFIGURATION ---
try:
    from s00_readabs_datalist import ABS_DATASETS, HISTORY_YEARS, OUTPUT_DIRECTORY
except ImportError:
    print("Error: Could not find 's00_readabs_datalist.py'.")
    sys.exit(1)

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
            
            # --- HANDLE CONFIG FORMAT (String vs Dict) ---
            if isinstance(value, dict):
                filename = value['filename']
                # We ignore 'plot_ids' here, s01 just saves the file
            else:
                filename = value
            # ---------------------------------------------

            if key not in all_tables_dict:
                print(f"  [X] Table '{key}' not found. Skipping.")
                continue

            df = all_tables_dict[key]

            # Apply Descriptions
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
            
            print(f"  [✓] Saved: {filename}")

    except Exception as e:
        print(f"  [!] Failed to process {name}: {e}")

if __name__ == "__main__":
    print(f"--- ABS BATCH DOWNLOAD STARTED (History: {HISTORY_YEARS} Years) ---")
    for item in ABS_DATASETS:
        fetch_and_save_dataset(item)
    print("\n--- BATCH DOWNLOAD COMPLETE ---")