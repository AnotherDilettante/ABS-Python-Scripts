# s02_readabs_plotting.py

import pandas as pd
import matplotlib.pyplot as plt
import os
import sys
import warnings
import logging

# --- SILENCE WARNINGS ---
# 1. Silence Pandas "Could not infer format"
warnings.filterwarnings("ignore", message="Could not infer format")
# 2. Silence Matplotlib "findfont" noise
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

# --- IMPORT CONFIGURATION ---
try:
    from s00_readabs_datalist import ABS_DATASETS, OUTPUT_DIRECTORY
except ImportError:
    print("Error: Could not find 's00_readabs_datalist.py'.")
    sys.exit(1)

# --- STYLE SETTINGS ---
# Tries Roboto first, then Arial, then generic sans-serif
plt.rcParams["font.family"] = ["Roboto", "Montserrat", "Zalando Sans", "Reddit Sans", "sans-serif"]

COLOR_PRIMARY = '#ED3144' # Strong Red
COLOR_SECONDARY = '#000000' # Black
COLOR_GRID = '#e0e0e0'


def apply_calc_transformation(df, calc_type, frequency):
    """
    Apply percentage change transformations based on calc_type and frequency.

    calc_type options:
        - "raw": No transformation (default)
        - "yoy": Year-on-year % change
        - "qoq": Quarter-on-quarter % change (quarterly data)
        - "mom": Month-on-month % change (monthly data)
    """
    if calc_type == "raw" or calc_type is None:
        return df, False  # No transformation, not a percentage

    freq_lower = str(frequency).lower()

    if calc_type == "yoy":
        # Year-on-year: 12 periods for monthly, 4 for quarterly
        if "monthly" in freq_lower:
            periods = 12
        elif "quarterly" in freq_lower:
            periods = 4
        else:
            periods = 4  # Default to quarterly
        transformed = df.pct_change(periods=periods) * 100
        return transformed, True

    elif calc_type == "qoq":
        # Quarter-on-quarter (1 period for quarterly data)
        transformed = df.pct_change(periods=1) * 100
        return transformed, True

    elif calc_type == "mom":
        # Month-on-month (1 period for monthly data)
        transformed = df.pct_change(periods=1) * 100
        return transformed, True

    return df, False  # Unknown calc_type, return unchanged


def create_abs_chart(df, title, subtitle, filename_prefix, columns_to_plot, is_percentage=False):
    """
    Generates a line chart for the given ABS DataFrame.
    """
    print(f"Generating chart: {title}...")

    # Setup Figure
    fig, ax = plt.subplots(dpi=300, figsize=(10, 7))

    # Plot Lines
    for i, col_name in enumerate(columns_to_plot):
        if col_name not in df.columns:
            print(f"  [!] Warning: Column '{col_name}' not found in data.")
            continue
            
        color = COLOR_PRIMARY if i == 0 else COLOR_SECONDARY
        linewidth = 2.5 if i == 0 else 1.5
        alpha = 1.0 if i == 0 else 0.7
        linestyle = '-'
        
        ax.plot(df.index, df[col_name], color=color, linewidth=linewidth, linestyle=linestyle, alpha=alpha, label=col_name)

        # Label at end of line
        # FIX: Use .max() instead of [-1] to satisfy Pylance
        last_date = df.index.max()
        last_val = df[col_name].loc[last_date]
        
        if pd.notnull(last_val):
            ax.text(
                last_date, last_val, f"  {last_val:,.1f}", 
                color=color, ha='left', va='center', 
                fontweight='bold', fontsize=10
            )

    # Styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle=':', color=COLOR_GRID)

    y_label = "% Change" if is_percentage else "Value"
    ax.set_ylabel(y_label, fontweight='semibold')
    ax.set_xlabel("Date", fontweight='semibold')

    # Title & Subtitle
    fig.text(0.1, 0.95, title, ha='left', va='top', fontsize=16, fontweight='bold')
    fig.text(0.1, 0.9, subtitle, ha='left', va='top', fontsize=10, color='#000000')

    # Footer
    caption_text = "Data Source: Australian Bureau of Statistics  •  Chart generated via readabs"
    fig.text(0.1, 0.02, caption_text, ha='left', va='bottom', fontsize=8, color='#000000')

    fig.subplots_adjust(top=0.83, bottom=0.18)

    # Save
    charts_folder = "abs_charts_output"
    os.makedirs(charts_folder, exist_ok=True)
    
    clean_title = filename_prefix.replace(".csv", "").replace(" ", "_")
    save_path = os.path.join(charts_folder, f"Chart_{clean_title}.png")
    
    fig.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("--- ABS CHART GENERATION STARTED ---")

    for dataset in ABS_DATASETS:
        dataset_name = dataset['name']
        frequency = dataset.get('frequency', 'Quarterly')
        tables = dataset['tables']

        for key, value in tables.items():

            # --- DETERMINE FILENAME, SERIES IDS, DISPLAY TITLE, CALC TYPE ---
            target_ids = []
            display_title = None
            calc_type = "raw"

            if isinstance(value, dict):
                csv_filename = value['filename']
                target_ids = value.get('plot_ids', [])
                display_title = value.get('display_title')
                calc_type = value.get('calc_type', 'raw')
            else:
                csv_filename = value
            # ----------------------------------------------------------------

            full_csv_path = os.path.join(OUTPUT_DIRECTORY, csv_filename)

            if not os.path.exists(full_csv_path):
                continue

            try:
                # Load CSV
                df = pd.read_csv(full_csv_path, index_col=0)
                # Convert Index to Date
                df.index = pd.to_datetime(df.index)

                if df.empty:
                    continue

                # --- COLUMN SELECTION LOGIC ---
                cols_to_plot = []

                # Case A: User provided specific IDs
                if target_ids:
                    for tid in target_ids:
                        found = False
                        for col in df.columns:
                            if tid in col:
                                cols_to_plot.append(col)
                                found = True
                                break
                        if not found:
                            print(f"  [!] Could not find Series ID '{tid}' in {csv_filename}")

                # Case B: No IDs provided -> Default to first column
                else:
                    cols_to_plot = [df.columns[0]]
                # ------------------------------

                if not cols_to_plot:
                    print(f"  [!] No valid columns found to plot for {csv_filename}")
                    continue

                # --- APPLY PERCENTAGE CHANGE TRANSFORMATION ---
                plot_df = df[cols_to_plot].copy()
                plot_df, is_percentage = apply_calc_transformation(plot_df, calc_type, frequency)

                # Drop NaN rows created by pct_change
                plot_df = plot_df.dropna()

                if plot_df.empty:
                    print(f"  [!] No data after transformation for {csv_filename}")
                    continue
                # -----------------------------------------------

                # --- GENERATE TITLE ---
                if display_title:
                    title = display_title
                else:
                    # Fallback to auto-generated title
                    title = f"{dataset_name}: {csv_filename.replace('.csv', '').replace('_', ' ')}"
                # ----------------------

                latest_date_str = plot_df.index.max().strftime('%B %Y')
                subtitle = f"Latest Data: {latest_date_str}"

                create_abs_chart(plot_df, title, subtitle, csv_filename, cols_to_plot, is_percentage)

            except Exception as e:
                print(f"Failed to plot {csv_filename}: {e}")

    print("\n--- CHART GENERATION COMPLETE ---")