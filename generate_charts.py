# generate_charts.py
# Run with: python generate_charts.py

import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.dates import MonthLocator, DateFormatter
import math
import os
import sys
import warnings
import logging

warnings.filterwarnings("ignore", message="Could not infer format")
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)

try:
    from config import ABS_DATASETS, OUTPUT_DIRECTORY
except ImportError:
    print("Error: Could not find 'config.py'.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# STYLE CONSTANTS
# ---------------------------------------------------------------------------

plt.rcParams["font.family"] = ["Calibri", "Roboto", "Arial", "sans-serif"]

COLORS     = ['#ED3144', '#1B4F8A', '#059669', '#D97706', '#7C3AED', '#555555']
COLOR_GRID = '#e0e0e0'

PERCENT_SERIES_IDS = {
    "A84423050A",   # Unemployment rate
    "A84423051C",   # Participation rate
    "A85256565A",   # Underemployment rate
    "A85255726K",   # Underutilisation rate
    "A2133256J",    # Percentage ERP Change
}

THOUSANDS_SERIES_IDS = {
    "A84423047L",   # Labour force total
    "A2133251W",    # Estimated Resident Population
    "A2133252X",    # Natural Increase
    "A2133254C",    # Net Overseas Migration
}


# ---------------------------------------------------------------------------
# LABEL & FORMAT HELPERS
# ---------------------------------------------------------------------------

def get_series_id(col_name):
    """Extract ABS Series ID from 'Description (A1234567X)' column name."""
    if '(' in col_name and col_name.endswith(')'):
        return col_name[col_name.rfind('(') + 1:-1].strip()
    return ''


def resolve_label(col_name, labels_map):
    """
    Return the display label for a column.
    labels_map is a dict of {series_id: short_label} from config.
    Falls back to stripping the Series ID from the column name.
    """
    if labels_map:
        sid = get_series_id(col_name)
        if sid in labels_map:
            return labels_map[sid]
    # Fallback: strip Series ID suffix and trailing semicolons
    desc = re.sub(r'\s*\([A-Z0-9]{6,}\)\s*$', '', col_name).strip()
    desc = re.sub(r'[;\s]+$', '', desc).strip()
    return desc or col_name


def sanitise_title(text):
    """Replace '&' with 'and' in any title or label string."""
    return text.replace(' & ', ' and ')


def ensure_australian(title):
    """Prepend 'Australian' if neither 'Australia' nor 'Australian' is present."""
    if 'australia' not in title.lower():
        return 'Australian ' + title
    return title


def resolve_format(value_format, col_name):
    """Resolve the 'mixed' format keyword to a concrete format per column."""
    if value_format == "mixed":
        sid = get_series_id(col_name)
        if sid in PERCENT_SERIES_IDS:
            return "percent"
        elif sid in THOUSANDS_SERIES_IDS:
            return "thousands"
        return "raw"
    return value_format or "raw"


# ---------------------------------------------------------------------------
# SCALE DETERMINATION
# ---------------------------------------------------------------------------

def determine_scale(value_format, data_max):
    """
    Returns (divisor, title_suffix, y_axis_label, tick_fmt_str).

    divisor      - raw values divided by this for display
    title_suffix - appended to chart title e.g. "('000)", "(m)", "(%)"
    y_axis_label - label on y-axis
    tick_fmt_str - Python format spec for tick values after division
    """
    vf = value_format or "raw"

    if vf == "percent":
        return 1, "(%)", "Rate (%)", ".1f"

    elif vf == "index":
        return 1, "(Index)", "Index", ".1f"

    elif vf == "count":
        return 1_000, "('000)", "Dwellings ('000)", ".0f"

    elif vf in ("thousands", "raw", "mixed"):
        if data_max > 5_000:
            return 1_000, "(m)", "Persons (m)", ".1f"
        elif data_max > 500:
            return 1, "('000)", "Persons ('000)", ".0f"
        else:
            return 1, "", "Value", ".1f"

    return 1, "", "Value", ".1f"


def make_tick_formatter(divisor, tick_fmt):
    """Return a FuncFormatter that divides raw values and formats them."""
    return mticker.FuncFormatter(lambda x, _: f'{x / divisor:{tick_fmt}}')


# ---------------------------------------------------------------------------
# CLEAN Y-AXIS LIMITS
# ---------------------------------------------------------------------------

def compute_clean_ylim(data_min_raw, data_max_raw, divisor, n_ticks=7,
                       force_min_raw=None):
    """
    Compute clean y-axis limits and tick interval so that:
      - Both the bottom and top limits fall on a round tick value
      - Approximately n_ticks evenly-spaced ticks are shown
      - force_min_raw overrides the computed lower bound (e.g. Population = 20 000)

    Returns (y_bottom_raw, y_top_raw, locator_interval_raw).
    All values are in raw data units (before dividing by divisor).
    """
    lo_disp = data_min_raw / divisor
    hi_disp = data_max_raw / divisor
    span    = hi_disp - lo_disp

    if span == 0:
        span = abs(hi_disp) or 1

    # Pick a clean interval in display units
    raw_interval = span / (n_ticks - 1)
    magnitude    = 10 ** math.floor(math.log10(raw_interval))
    nice_steps   = [1, 2, 2.5, 5, 10]
    interval_disp = min(
        (s * magnitude for s in nice_steps),
        key=lambda v: abs(v - raw_interval)
    )

    # Floor min, ceil max to nearest interval multiple
    bottom_disp = math.floor(lo_disp / interval_disp) * interval_disp
    top_disp    = math.ceil(hi_disp  / interval_disp) * interval_disp

    # Add one extra tick of padding at the top so lines don't kiss the border
    top_disp += interval_disp * 0.0   # no extra padding — top tick IS the ceiling

    # Convert back to raw units
    bottom_raw = bottom_disp * divisor
    top_raw    = top_disp    * divisor
    interval_raw = interval_disp * divisor

    # Apply hard minimum override (e.g. Population ERP starting at 20m)
    if force_min_raw is not None:
        bottom_raw = force_min_raw

    return bottom_raw, top_raw, interval_raw


# ---------------------------------------------------------------------------
# AXIS STYLE HELPERS
# ---------------------------------------------------------------------------

def apply_xaxis_style(ax):
    """
    Bi-annual x-axis ticks (March and September), 90 degree rotation,
    font size matching y-axis, formatted as 'Mar-16'.
    """
    ax.xaxis.set_major_locator(MonthLocator(bymonth=[3, 9]))
    ax.xaxis.set_major_formatter(DateFormatter('%b-%y'))
    plt.setp(ax.xaxis.get_majorticklabels(),
             rotation=90, ha='right', va='top', fontsize=10)


def apply_common_style(ax):
    """Remove top/right spines and add light dotted y-grid."""
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', linestyle=':', color=COLOR_GRID, alpha=0.8)


def build_date_range(plot_df):
    """Return e.g. 'Oct 2015 - Sep 2025'."""
    start = plot_df.index.min().strftime('%b %Y')
    end   = plot_df.index.max().strftime('%b %Y')
    return f"{start} - {end}"


def finalise_and_save(fig, title, subtitle, filename_prefix):
    """Write title, subtitle, footer; adjust layout; save PNG."""
    fig.text(0.09, 0.95,  sanitise_title(title),
             ha='left', va='top', fontsize=14, fontweight='bold')
    fig.text(0.09, 0.905, sanitise_title(subtitle),
             ha='left', va='top', fontsize=9, color='#444444')
    fig.text(
        0.09, 0.025,
        "Data Source: Australian Bureau of Statistics  |  Analysis by Chris Angus",
        ha='left', va='bottom', fontsize=8, color='#666666'
    )
    fig.subplots_adjust(top=0.83, bottom=0.14)

    os.makedirs("abs_charts_output", exist_ok=True)
    clean     = filename_prefix.replace(".csv", "").replace(" ", "_")
    save_path = os.path.join("abs_charts_output", f"Chart_{clean}.png")
    fig.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  -> Saved: Chart_{clean}.png")


# ---------------------------------------------------------------------------
# TRANSFORMATIONS
# ---------------------------------------------------------------------------

def apply_calc_transformation(df, calc_type, frequency):
    """Return (transformed_df, is_percentage_flag)."""
    if not calc_type or calc_type == "raw":
        return df, False
    freq = str(frequency).lower()
    if calc_type == "yoy":
        return df.pct_change(periods=12 if "monthly" in freq else 4) * 100, True
    if calc_type in ("qoq", "mom"):
        return df.pct_change(periods=1) * 100, True
    return df, False


# ---------------------------------------------------------------------------
# STANDARD SINGLE-AXIS CHART
# ---------------------------------------------------------------------------

def create_abs_chart(df, title, subtitle, filename_prefix,
                     columns_to_plot, value_format=None,
                     clip_percentile=None, y_min=None, y_max=None,
                     y_label_override=None, labels_map=None):
    """
    Single-axis line chart.

    Parameters
    ----------
    clip_percentile : [lo_pct, hi_pct] or None
        Restrict y-axis to these data percentiles (e.g. [5, 95] for GDP).
    y_min / y_max   : float or None
        Hard y-axis limits in raw data units.
    y_label_override: str or None
        Replaces the auto-derived y-axis label.
    labels_map      : dict {series_id: label} or None
        Short legend labels keyed by ABS Series ID.
    """
    print(f"Generating chart: {title}...")

    fig, ax = plt.subplots(dpi=300, figsize=(10, 7))

    primary_fmt = resolve_format(value_format, columns_to_plot[0]) \
        if columns_to_plot else "raw"

    all_vals = pd.concat(
        [df[c].dropna() for c in columns_to_plot if c in df.columns],
        ignore_index=True
    )
    data_max = float(all_vals.abs().max()) if not all_vals.empty else 100
    divisor, title_suffix, y_label, tick_fmt = determine_scale(primary_fmt, data_max)

    # --- Plot series ---
    for i, col in enumerate(columns_to_plot):
        if col not in df.columns:
            print(f"  [!] Column not found: {col}")
            continue
        ax.plot(df.index, df[col],
                color=COLORS[i % len(COLORS)],
                linewidth=2.5 if i == 0 else 1.8,
                linestyle='-',
                label=resolve_label(col, labels_map))

    # --- Y-axis: clean limits ---
    if not all_vals.empty:
        # Restrict range first if percentile clipping requested
        if clip_percentile:
            lo_raw = float(all_vals.quantile(clip_percentile[0] / 100))
            hi_raw = float(all_vals.quantile(clip_percentile[1] / 100))
        else:
            lo_raw = float(all_vals.min())
            hi_raw = float(all_vals.max())

        bottom_raw, top_raw, interval_raw = compute_clean_ylim(
            lo_raw, hi_raw, divisor,
            force_min_raw=y_min
        )
        if y_max is not None:
            top_raw = y_max

        ax.set_ylim(bottom_raw, top_raw)
        ax.yaxis.set_major_locator(mticker.MultipleLocator(interval_raw))

    ax.yaxis.set_major_formatter(make_tick_formatter(divisor, tick_fmt))
    ax.set_ylabel(y_label_override or y_label, fontweight='semibold', fontsize=10)
    ax.tick_params(axis='y', labelsize=10)

    # --- X-axis ---
    apply_xaxis_style(ax)
    ax.set_xlabel("")

    # --- Style ---
    apply_common_style(ax)
    ax.legend(loc='best', fontsize=9, framealpha=0.9,
              edgecolor='#cccccc', borderpad=0.6)

    date_range   = build_date_range(df.loc[df.index.isin(
        pd.concat([df[c].dropna() for c in columns_to_plot
                   if c in df.columns]).index)] if columns_to_plot else df)
    full_title   = f"{ensure_australian(title)} {title_suffix}, {date_range}".strip()
    full_subtitle = subtitle

    finalise_and_save(fig, full_title, full_subtitle, filename_prefix)


# ---------------------------------------------------------------------------
# DUAL-AXIS CHART  (Labour Force and Population)
# ---------------------------------------------------------------------------

def create_dual_axis_chart(df, title, subtitle, filename_prefix,
                           primary_cols, secondary_cols,
                           primary_format, secondary_format,
                           primary_ymin=None,
                           y_label_primary=None, y_label_secondary=None,
                           labels_map=None):
    """
    Two-axis line chart.
    Primary series  -> left axis  (solid lines).
    Secondary series -> right axis (dashed lines).
    Legend placed below the plot area to avoid overlap.
    """
    print(f"Generating dual-axis chart: {title}...")

    fig, ax1 = plt.subplots(dpi=300, figsize=(10, 7))
    ax2 = ax1.twinx()

    # --- Primary (left) ---
    p_vals = pd.concat(
        [df[c].dropna() for c in primary_cols if c in df.columns],
        ignore_index=True
    ) if primary_cols else pd.Series(dtype=float)

    p_max = float(p_vals.abs().max()) if not p_vals.empty else 100
    p_div, p_sfx, p_ylabel, p_fmt = determine_scale(primary_format, p_max)

    for i, col in enumerate(primary_cols):
        if col not in df.columns:
            continue
        ax1.plot(df.index, df[col],
                 color=COLORS[i % len(COLORS)],
                 linewidth=2.5, linestyle='-',
                 label=resolve_label(col, labels_map))

    if not p_vals.empty:
        p_bottom, p_top, p_interval = compute_clean_ylim(
            float(p_vals.min()), float(p_vals.max()), p_div,
            force_min_raw=primary_ymin
        )
        ax1.set_ylim(p_bottom, p_top)
        ax1.yaxis.set_major_locator(mticker.MultipleLocator(p_interval))

    ax1.yaxis.set_major_formatter(make_tick_formatter(p_div, p_fmt))
    ax1.set_ylabel(y_label_primary or p_ylabel, fontweight='semibold', fontsize=10)
    ax1.tick_params(axis='y', labelsize=10)

    # --- Secondary (right) ---
    s_vals = pd.concat(
        [df[c].dropna() for c in secondary_cols if c in df.columns],
        ignore_index=True
    ) if secondary_cols else pd.Series(dtype=float)

    s_max = float(s_vals.abs().max()) if not s_vals.empty else 100
    s_div, s_sfx, s_ylabel, s_fmt = determine_scale(secondary_format, s_max)

    colour_offset = len(primary_cols)
    for i, col in enumerate(secondary_cols):
        if col not in df.columns:
            continue
        ax2.plot(df.index, df[col],
                 color=COLORS[(colour_offset + i) % len(COLORS)],
                 linewidth=1.8, linestyle='--',
                 label=resolve_label(col, labels_map))

    if not s_vals.empty:
        s_bottom, s_top, s_interval = compute_clean_ylim(
            float(s_vals.min()), float(s_vals.max()), s_div
        )
        ax2.set_ylim(s_bottom, s_top)
        ax2.yaxis.set_major_locator(mticker.MultipleLocator(s_interval))

    ax2.yaxis.set_major_formatter(make_tick_formatter(s_div, s_fmt))
    ax2.set_ylabel(y_label_secondary or s_ylabel, fontweight='semibold', fontsize=10)
    ax2.tick_params(axis='y', labelsize=10)
    ax2.spines['top'].set_visible(False)

    # --- Combined legend below plot ---
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    n_cols = len(h1) + len(h2)
    ax1.legend(h1 + h2, l1 + l2,
               loc='upper center',
               bbox_to_anchor=(0.5, -0.18),
               ncol=min(n_cols, 3),
               fontsize=9, framealpha=0.9, edgecolor='#cccccc')

    # --- Style ---
    apply_common_style(ax1)
    apply_xaxis_style(ax1)
    ax1.set_xlabel("")

    if p_sfx == s_sfx:
        combined_sfx = p_sfx
    elif p_sfx and s_sfx:
        combined_sfx = f"{p_sfx} / {s_sfx}"
    else:
        combined_sfx = p_sfx or s_sfx

    all_cols  = primary_cols + secondary_cols
    date_range = build_date_range(df[[c for c in all_cols if c in df.columns]])
    full_title = f"{ensure_australian(title)} {combined_sfx}, {date_range}".strip()

    finalise_and_save(fig, full_title, subtitle, filename_prefix)


# ---------------------------------------------------------------------------
# CHART DISPATCH — MERGED OUTPUT  (OAD Combined)
# ---------------------------------------------------------------------------

def chart_merged_output(dataset_info):
    """Generate the chart for a merge_tables dataset (OAD Combined)."""
    out_cfg       = dataset_info.get('merged_output', {})
    filename      = out_cfg.get('filename', 'OAD_Combined.csv')
    display_title = out_cfg.get('display_title', 'Overseas Migration')
    calc_type     = out_cfg.get('calc_type', 'raw')
    value_format  = out_cfg.get('value_format', 'thousands')
    y_label       = out_cfg.get('y_label')
    labels_map    = out_cfg.get('labels', {})

    full_path = os.path.join(OUTPUT_DIRECTORY, filename)
    if not os.path.exists(full_path):
        print(f"  [!] {filename} not found - run download.py first.")
        return

    df = pd.read_csv(full_path, index_col=0)
    df.index = pd.to_datetime(df.index)
    if df.empty:
        return

    frequency  = dataset_info.get('frequency', 'Monthly')
    cols       = list(df.columns)
    plot_df, _ = apply_calc_transformation(df[cols].copy(), calc_type, frequency)
    plot_df    = plot_df.dropna(how='all')
    if plot_df.empty:
        return

    subtitle = "Quarterly, summed"
    create_abs_chart(
        plot_df, display_title, subtitle, filename,
        cols, value_format=value_format,
        y_label_override=y_label, labels_map=labels_map
    )


# ---------------------------------------------------------------------------
# CHART DISPATCH — STANDARD TABLES
# ---------------------------------------------------------------------------

def chart_standard_tables(dataset_info):
    """Generate charts for all standard table entries in a dataset."""
    dataset_name = dataset_info['name']
    frequency    = dataset_info.get('frequency', 'Quarterly')
    tables       = dataset_info.get('tables', {})

    for key, value in tables.items():

        if isinstance(value, dict):
            csv_filename  = value['filename']
            target_ids    = value.get('plot_ids', [])
            display_title = value.get('display_title')
            calc_type     = value.get('calc_type', 'raw')
            value_format  = value.get('value_format')
            dual_axis_cfg = value.get('dual_axis')
            clip_pct      = value.get('clip_percentile')
            y_min         = value.get('y_min')
            y_max         = value.get('y_max')
            labels_map    = value.get('labels', {})
        else:
            csv_filename  = value
            target_ids    = []
            display_title = None
            calc_type     = "raw"
            value_format  = None
            dual_axis_cfg = None
            clip_pct      = None
            y_min         = None
            y_max         = None
            labels_map    = {}

        full_path = os.path.join(OUTPUT_DIRECTORY, csv_filename)
        if not os.path.exists(full_path):
            continue

        try:
            df = pd.read_csv(full_path, index_col=0)
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
                        print(f"  [!] Series ID '{tid}' not found in {csv_filename}")
            else:
                cols_to_plot = [df.columns[0]]

            if not cols_to_plot:
                print(f"  [!] No plottable columns for {csv_filename}")
                continue

            # Exclude series flagged in dual_axis config
            if dual_axis_cfg:
                exclude_ids = dual_axis_cfg.get('exclude_ids', [])
                if exclude_ids:
                    cols_to_plot = [
                        c for c in cols_to_plot
                        if not any(eid in c for eid in exclude_ids)
                    ]

            plot_df, _ = apply_calc_transformation(
                df[cols_to_plot].copy(), calc_type, frequency)
            plot_df = plot_df.dropna(how='all')
            if plot_df.empty:
                continue

            title    = display_title or \
                f"{dataset_name}: {csv_filename.replace('.csv','').replace('_',' ')}"
            subtitle = frequency

            if dual_axis_cfg:

                def find_cols(id_list, source_df):
                    out = []
                    for sid in id_list:
                        for col in source_df.columns:
                            if sid in col:
                                out.append(col)
                                break
                    return out

                p_cols = find_cols(dual_axis_cfg.get('primary_ids',   []), plot_df)
                s_cols = find_cols(dual_axis_cfg.get('secondary_ids', []), plot_df)

                create_dual_axis_chart(
                    plot_df, title, subtitle, csv_filename,
                    p_cols, s_cols,
                    primary_format    = dual_axis_cfg.get('primary_format',    'thousands'),
                    secondary_format  = dual_axis_cfg.get('secondary_format',  'percent'),
                    primary_ymin      = dual_axis_cfg.get('primary_ymin'),
                    y_label_primary   = dual_axis_cfg.get('y_label_primary'),
                    y_label_secondary = dual_axis_cfg.get('y_label_secondary'),
                    labels_map        = labels_map,
                )

            else:
                create_abs_chart(
                    plot_df, title, subtitle, csv_filename,
                    cols_to_plot,
                    value_format    = value_format,
                    clip_percentile = clip_pct,
                    y_min           = y_min,
                    y_max           = y_max,
                    labels_map      = labels_map,
                )

        except Exception as e:
            import traceback
            print(f"  [!] Failed to plot {csv_filename}: {e}")
            traceback.print_exc()


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
