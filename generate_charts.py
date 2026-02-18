# generate_charts.py

import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import warnings
import logging

# --- SILENCE WARNINGS ---
warnings.filterwarnings("ignore", message="Could not infer format")
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

# --- IMPORT CONFIGURATION ---
try:
    from config import ABS_DATASETS, OUTPUT_DIRECTORY
except ImportError:
    print("Error: Could not find 'config.py'.")
    sys.exit(1)

# --- STYLE SETTINGS ---
plt.rcParams["font.family"] = ["Roboto", "Montserrat", "Zalando Sans", "Reddit Sans", "sans-serif"]

COLOR_PRIMARY   = '#ED3144'  # Strong Red
COLOR_SECONDARY = '#000000'  # Black
COLOR_GRID      = '#e0e0e0'


# ---------------------------------------------------------------------------
# NUMBER FORMATTING HELPERS
# ---------------------------------------------------------------------------

# Series IDs whose values are percentages/rates (used for "mixed" format datasets)
PERCENT_SERIES_IDS = {
    "A84423050A",   # Unemployment rate
    "A84423051C",   # Participation rate
    "A85256565A",   # Underemployment rate
    "A85255726K",   # Underutilisation rate
    "A2133256J",    # Percentage ERP Change
}

# Series IDs whose values are '000s (used for "mixed" format datasets)
THOUSANDS_SERIES_IDS = {
    "A84423047L",   # Labour force total (already in '000s in source)
    "A2133251W",    # Estimated Resident Population ('000s)
    "A2133252X",    # Natural Increase ('000s)
    "A2133254C",    # Net Overseas Migration ('000s)
}


def get_series_id(col_name):
    """Extract Series ID from a column name formatted as 'Description (SERIES_ID)'."""
    if '(' in col_name and col_name.endswith(')'):
        return col_name[col_name.rfind('(') + 1:-1].strip()
    return col_name


def resolve_format(value_format, col_name):
    """
    Return the effective format string for a column.

    value_format options:
        "percent"   - show as "6.1%",    y-axis = "% / Rate"
        "thousands" - show as "61.0",    y-axis = "'000s"
        "count"     - show as "18,797",  y-axis = "Dwellings"
        "index"     - show as "102.3",   y-axis = "Index"
        "mixed"     - per-series lookup via PERCENT/THOUSANDS_SERIES_IDS
        None/"raw"  - show as "18,797.0" y-axis = "Value"
    """
    if value_format == "mixed":
        sid = get_series_id(col_name)
        if sid in PERCENT_SERIES_IDS:
            return "percent"
        elif sid in THOUSANDS_SERIES_IDS:
            return "thousands"
        else:
            return "raw"
    return value_format or "raw"


def format_end_label(value, fmt):
    """Format a float value for the end-of-line label."""
    if fmt == "percent":
        return f"  {value:.1f}%"
    elif fmt == "thousands":
        return f"  {value:,.1f}"
    elif fmt == "count":
        return f"  {int(round(value)):,}"
    elif fmt == "index":
        return f"  {value:.1f}"
    else:  # raw
        return f"  {value:,.1f}"


def y_axis_label(value_format, is_percentage_calc):
    """Return an appropriate y-axis label."""
    if is_percentage_calc:
        return "% Change"
    label_map = {
        "percent":   "% / Rate",
        "thousands": "'000s",
        "count":     "Dwellings",
        "index":     "Index",
        "mixed":     "Value",
        "raw":       "Value",
    }
    return label_map.get(value_format or "raw", "Value")


# ---------------------------------------------------------------------------
# TRANSFORMATION
# ---------------------------------------------------------------------------

def apply_calc_transformation(df, calc_type, frequency):
    """
    Apply percentage change transformations based on calc_type and frequency.
    Returns (transformed_df, is_percentage_bool).
    """
    if calc_type == "raw" or calc_type is None:
        return df, False

    freq_lower = str(frequency).lower()

    if calc_type == "yoy":
        periods = 12 if "monthly" in freq_lower else 4
        return df.pct_change(periods=periods) * 100, True

    elif calc_type == "qoq":
        return df.pct_change(periods=1) * 100, True

    elif calc_type == "mom":
        return df.pct_change(periods=1) * 100, True

    return df, False


# ---------------------------------------------------------------------------
# CHART CREATION
# ---------------------------------------------------------------------------

def create_abs_chart(df, title, subtitle, filename_prefix, columns_to_plot,
                     is_percentage=False, value_format=None):
    """
    Generates a styled line chart for the given ABS DataFrame.

    value_format controls end-of-line label and y-axis formatting.
    For "mixed" datasets, each column's format is resolved individually.
    """
    print(f"Generating chart: {title}...")

    fig, ax = plt.subplots(dpi=300, figsize=(10, 7))

    for i, col_name in enumerate(columns_to_plot):
        if col_name not in df.columns:
            print(f"  [!] Warning: Column '{col_name}' not found in data.")
            continue

        col_fmt   = resolve_format(value_format, col_name)
        color     = COLOR_PRIMARY if i == 0 else COLOR_SECONDARY
        linewidth = 2.5 if i == 0 else 1.5
        alpha     = 1.0 if i == 0 else 0.7

        ax.plot(df.index, df[col_name],
                color=color, linewidth=linewidth, linestyle='-', alpha=alpha,
                label=col_name)

        # End-of-line label
        last_date = df.index.max()
        last_val  = df[col_name].loc[last_date]

        if pd.notnull(last_val):
            label_text = format_end_label(last_val, col_fmt)
            ax.text(last_date, last_val, label_text,
                    color=color, ha='left', va='center',
                    fontweight='bold', fontsize=10)

    # Axes styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle=':', color=COLOR_GRID)

    ax.set_ylabel(y_axis_label(value_format, is_percentage), fontweight='semibold')
    ax.set_xlabel("Date", fontweight='semibold')

    # Titles
    fig.text(0.1, 0.95, title,    ha='left', va='top', fontsize=16, fontweight='bold')
    fig.text(0.1, 0.90, subtitle, ha='left', va='top', fontsize=10, color='#000000')

    # Footer
    fig.text(0.1, 0.02,
             "Data Source: Australian Bureau of Statistics  |  Chart generated via readabs",
             ha='left', va='bottom', fontsize=8, color='#000000')

    fig.subplots_adjust(top=0.83, bottom=0.18)

    # Save
    os.makedirs("abs_charts_output", exist_ok=True)
    clean_prefix = filename_prefix.replace(".csv", "").replace(" ", "_")
    save_path = os.path.join("abs_charts_output", f"Chart_{clean_prefix}.png")
    fig.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)


# ---------------------------------------------------------------------------
# CHART DISPATCH
# ---------------------------------------------------------------------------

def chart_merged_output(dataset_info):
    """Generate the chart for a merge_tables dataset (e.g. OAD Combined)."""
    out_cfg      = dataset_info.get('merged_output', {})
    filename     = out_cfg.get('filename', 'OAD_Combined.csv')
    display_title = out_cfg.get('display_title', 'Overseas Migration')
    calc_type    = out_cfg.get('calc_type', 'raw')
    value_format = out_cfg.get('value_format', 'thousands')

    full_path = os.path.join(OUTPUT_DIRECTORY, filename)
    if not os.path.exists(full_path):
        print(f"  [!] {filename} not found - run download.py first.")
        return

    df = pd.read_csv(full_path, index_col=0)
    df.index = pd.to_datetime(df.index)
    if df.empty:
        return

    cols_to_plot = list(df.columns)
    frequency    = dataset_info.get('frequency', 'Monthly')
    plot_df, is_pct = apply_calc_transformation(df[cols_to_plot].copy(), calc_type, frequency)
    plot_df = plot_df.dropna(how='all')

    if plot_df.empty:
        print(f"  [!] No data after transformation for {filename}")
        return

    latest     = plot_df.index.max()
    latest_str = latest.strftime('%b %Y') if hasattr(latest, 'strftime') else str(latest)
    subtitle   = f"Latest Data: {latest_str}  |  Quarterly, summed"

    create_abs_chart(plot_df, display_title, subtitle, filename,
                     cols_to_plot, is_percentage=is_pct, value_format=value_format)


def chart_standard_tables(dataset_info):
    """Generate charts for all standard 'tables' entries in a dataset."""
    dataset_name = dataset_info['name']
    frequency    = dataset_info.get('frequency', 'Quarterly')
    tables       = dataset_info.get('tables', {})
    is_resampled = dataset_info.get('resample_to_quarterly', False)

    for key, value in tables.items():
        target_ids    = []
        display_title = None
        calc_type     = "raw"
        value_format  = None

        if isinstance(value, dict):
            csv_filename  = value['filename']
            target_ids    = value.get('plot_ids', [])
            display_title = value.get('display_title')
            calc_type     = value.get('calc_type', 'raw')
            value_format  = value.get('value_format')
        else:
            csv_filename = value

        full_csv_path = os.path.join(OUTPUT_DIRECTORY, csv_filename)
        if not os.path.exists(full_csv_path):
            continue

        try:
            df = pd.read_csv(full_csv_path, index_col=0)
            df.index = pd.to_datetime(df.index)
            if df.empty:
                continue

            # Column selection
            cols_to_plot = []
            if target_ids:
                for tid in target_ids:
                    for col in df.columns:
                        if tid in col:
                            cols_to_plot.append(col)
                            break
                    else:
                        print(f"  [!] Could not find Series ID '{tid}' in {csv_filename}")
            else:
                cols_to_plot = [df.columns[0]]

            if not cols_to_plot:
                print(f"  [!] No valid columns found to plot for {csv_filename}")
                continue

            # Transformation
            plot_df, is_pct = apply_calc_transformation(
                df[cols_to_plot].copy(), calc_type, frequency)
            plot_df = plot_df.dropna(how='all')

            if plot_df.empty:
                print(f"  [!] No data after transformation for {csv_filename}")
                continue

            # Title
            title = display_title or \
                f"{dataset_name}: {csv_filename.replace('.csv', '').replace('_', ' ')}"

            # Subtitle - note if data was resampled to quarterly
            latest     = plot_df.index.max()
            latest_str = latest.strftime('%b %Y') if hasattr(latest, 'strftime') else str(latest)
            freq_note  = "Quarterly" if is_resampled else frequency
            subtitle   = f"Latest Data: {latest_str}  |  {freq_note}"

            create_abs_chart(plot_df, title, subtitle, csv_filename,
                             cols_to_plot, is_percentage=is_pct, value_format=value_format)

        except Exception as e:
            print(f"Failed to plot {csv_filename}: {e}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("--- ABS CHART GENERATION STARTED ---")

    for dataset in ABS_DATASETS:
        if dataset.get('merge_tables'):
            chart_merged_output(dataset)
        else:
            chart_standard_tables(dataset)

    print("\n--- CHART GENERATION COMPLETE ---")
