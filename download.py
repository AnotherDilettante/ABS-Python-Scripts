# download.py

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
    from config import ABS_DATASETS, HISTORY_YEARS, OUTPUT_DIRECTORY
except ImportError:
    print("Error: Could not find 'config.py'.")
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
        table_count = len(ds.get('tables', {})) or (1 if ds.get('merge_tables') else 0)
        print(f"{cat_id:<12} {freq:<12} {name:<40} {table_count} table(s)")
    print(f"\nTotal: {len(datasets)} dataset(s)")
    print("-" * 90)


def get_rows_to_keep(frequency, years):
    freq = str(frequency).lower()
    if "monthly" in freq:     return years * 12
    elif "quarterly" in freq: return years * 4
    elif "half" in freq:      return years * 2
    elif "yearly" in freq or "annual" in freq: return years * 1
    else:                     return years * 4


def ensure_datetime_index(df):
    """
    Convert a DataFrame index to DatetimeIndex regardless of whether readabs
    returned a PeriodIndex (monthly data) or a plain object index (quarterly data).
    """
    if hasattr(df.index, 'to_timestamp'):
        # PeriodIndex - readabs returns this for monthly catalogues
        df.index = df.index.to_timestamp()
    else:
        df.index = pd.to_datetime(df.index)
    return df


def resample_quarterly(df, method):
    """
    Resample a monthly DataFrame to quarterly frequency.

    method: "sum"  - sum all monthly values within the quarter (e.g. dwelling counts)
            "last" - take the last observation in the quarter (e.g. rate series)
            "mean" - average across the quarter
    """
    df = ensure_datetime_index(df)
    if method == "sum":
        return df.resample("QE").sum()
    elif method == "last":
        return df.resample("QE").last()
    elif method == "mean":
        return df.resample("QE").mean()
    else:
        return df.resample("QE").last()


def fetch_raw_catalogue(cat_id):
    """Download an ABS catalogue and return (tables_dict, meta_df), or None on failure."""
    f = io.StringIO()
    with redirect_stdout(f), redirect_stderr(f):
        logging.getLogger().setLevel(logging.ERROR)
        result = ra.read_abs_cat(cat_id)
        logging.getLogger().setLevel(logging.WARNING)
    if not isinstance(result, tuple):
        return None
    return result


def build_desc_map(meta_df):
    """Build a Series-ID -> description mapping from the metadata DataFrame."""
    if 'Data Item Description' in meta_df.columns:
        return meta_df['Data Item Description'].to_dict()
    return {}


def rename_columns(df, id_to_desc):
    """Rename raw Series-ID column headers to 'Description (ID)' format."""
    new_names = []
    for col_id in df.columns:
        desc = id_to_desc.get(col_id, "")
        desc = str(desc).strip().replace('\n', ' ')
        if desc:
            new_names.append(f"{desc} ({col_id})")
        else:
            new_names.append(col_id)
    df.columns = new_names
    return df


def save_df(df, filename):
    """Ensure output directory exists and save DataFrame as CSV."""
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIRECTORY, filename)
    df.to_csv(output_path)
    return output_path


def process_standard_tables(dataset_info, all_tables_dict, id_to_desc, rows_to_keep,
                             do_quarterly, resample_method):
    """Process the standard 'tables' dict entries for a dataset."""
    tables = dataset_info.get('tables', {})

    for key, value in tables.items():
        target_ids = []
        if isinstance(value, dict):
            filename = value['filename']
            target_ids = value.get('plot_ids', [])
        else:
            filename = value

        if key not in all_tables_dict:
            print(f"  [X] Table '{key}' not found. Skipping.")
            continue

        df = all_tables_dict[key].copy()
        df.columns = df.columns.str.strip()

        # Filter to requested Series IDs
        if target_ids:
            found_cols = [c for c in df.columns if c in target_ids]
            if found_cols:
                df = df[found_cols]
                missing = set(target_ids) - set(found_cols)
                if missing:
                    print(f"      [!] Warning: Could not find these IDs: {missing}")
            else:
                print(f"      [!] Warning: No match for requested IDs. Saving full table instead.")

        # Rename columns to Description (ID) format
        df = rename_columns(df, id_to_desc)

        # Sort chronologically and take most recent N rows (monthly window)
        if not df.index.is_monotonic_increasing:
            df = df.sort_index()
        df = df.tail(rows_to_keep)

        # Resample monthly -> quarterly if requested
        if do_quarterly:
            df = resample_quarterly(df, resample_method)
            df = df.tail(HISTORY_YEARS * 4)

        save_df(df, filename)
        print(f"  [OK] Saved: {filename} ({len(df.columns)} series)")


def process_merged_oad(dataset_info, all_tables_dict, id_to_desc, rows_to_keep,
                       do_quarterly, resample_method):
    """
    Special handler for OAD (and any future merge_tables datasets).

    Fetches arrivals + departures from separate ABS tables, merges them into one
    DataFrame, and appends a derived 'Net Long Term Arrivals' column.
    """
    merge_cfg = dataset_info.get('merge_tables', {})
    out_cfg   = dataset_info.get('merged_output', {})

    filename         = out_cfg.get('filename', 'OAD_Combined.csv')
    arrivals_label   = out_cfg.get('arrivals_label',   "Long Term Arrivals ('000)")
    departures_label = out_cfg.get('departures_label', "Long Term Departures ('000)")
    net_label        = out_cfg.get('net_label',        "Net Long Term Arrivals ('000)")

    series_frames = {}
    table_keys = list(merge_cfg.keys())

    for tbl_key, series_id in merge_cfg.items():
        if tbl_key not in all_tables_dict:
            print(f"  [X] Merge table '{tbl_key}' not found. Skipping OAD merge.")
            return

        df = all_tables_dict[tbl_key].copy()
        df.columns = df.columns.str.strip()

        found = [c for c in df.columns if c == series_id]
        if not found:
            print(f"  [!] Series ID '{series_id}' not found in table '{tbl_key}'.")
            return

        series_frames[tbl_key] = df[[series_id]].copy()

    # Merge on index
    arrivals_key, departures_key = table_keys[0], table_keys[1]
    merged = series_frames[arrivals_key].join(series_frames[departures_key], how='inner')
    merged.columns = [arrivals_label, departures_label]

    # Sort and trim to history window
    merged = ensure_datetime_index(merged)
    merged = merged.sort_index()
    merged = merged.tail(rows_to_keep)

    # Resample monthly -> quarterly if requested
    if do_quarterly:
        merged = resample_quarterly(merged, resample_method)
        merged = merged.tail(HISTORY_YEARS * 4)

    # Convert raw counts to '000s
    merged = merged / 1000.0

    # Derive net column
    merged[net_label] = merged[arrivals_label] - merged[departures_label]

    save_df(merged, filename)
    print(f"  [OK] Saved: {filename} (3 series: arrivals, departures, net)")


def fetch_and_save_dataset(dataset_info):
    name      = dataset_info['name']
    cat_id    = dataset_info['cat_id']
    frequency = dataset_info.get('frequency', 'Quarterly')

    rows_to_keep    = get_rows_to_keep(frequency, HISTORY_YEARS)
    do_quarterly    = dataset_info.get('resample_to_quarterly', False)
    resample_method = dataset_info.get('resample_method', 'last')

    freq_note = " -> Quarterly" if do_quarterly else ""
    print(f"\nProcessing: {name} (Cat: {cat_id}) | Freq: {frequency}{freq_note}")

    result = fetch_raw_catalogue(cat_id)
    if result is None:
        print(f"  [X] Error: Unexpected return format for {cat_id}")
        return

    all_tables_dict, meta_df = result
    id_to_desc = build_desc_map(meta_df)

    if dataset_info.get('merge_tables'):
        process_merged_oad(dataset_info, all_tables_dict, id_to_desc,
                           rows_to_keep, do_quarterly, resample_method)
    else:
        try:
            process_standard_tables(dataset_info, all_tables_dict, id_to_desc,
                                    rows_to_keep, do_quarterly, resample_method)
        except Exception as e:
            print(f"  [!] Failed to process {name}: {e}")


# --- MAIN ---
if __name__ == "__main__":
    args = parse_args()

    datasets_to_process = filter_datasets(ABS_DATASETS, freq=args.freq, cat=args.cat)

    if not datasets_to_process:
        print("No datasets match the specified filters.")
        sys.exit(0)

    if args.list_only:
        list_datasets(datasets_to_process)
        sys.exit(0)

    filter_info = []
    if args.freq: filter_info.append(f"Freq: {args.freq}")
    if args.cat:  filter_info.append(f"Cat: {args.cat}")
    filter_str = f" ({', '.join(filter_info)})" if filter_info else ""

    print(f"--- ABS BATCH DOWNLOAD STARTED (History: {HISTORY_YEARS} Years){filter_str} ---")
    for item in datasets_to_process:
        fetch_and_save_dataset(item)
    print("\n--- BATCH DOWNLOAD COMPLETE ---")
