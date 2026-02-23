# dashboard.py — ABS Economic Data Dashboard
# Run with: streamlit run dashboard.py

import math
import re
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- CONFIGURATION ---
OUTPUT_DIRECTORY = "abs_data_output"

# Six-colour palette matching generate_charts.py
COLORS = ['#ED3144', '#1B4F8A', '#059669', '#D97706', '#7C3AED', '#555555']

# --- DATASET REGISTRY ---
try:
    from config import ABS_DATASETS
    REGISTRY_AVAILABLE = True
except ImportError:
    ABS_DATASETS = []
    REGISTRY_AVAILABLE = False

# Mirror the same lookup sets used in generate_charts.py
PERCENT_SERIES_IDS = {
    "A84423050A", "A84423051C", "A85256565A",
    "A85255726K", "A2133256J",
}
THOUSANDS_SERIES_IDS = {
    "A84423047L", "A2133251W", "A2133252X", "A2133254C",
}


# ---------------------------------------------------------------------------
# LABEL & FORMAT HELPERS
# ---------------------------------------------------------------------------

def get_series_id(col_name):
    """Extract ABS Series ID from 'Description (A1234567X)' column name."""
    if '(' in col_name and col_name.endswith(')'):
        return col_name[col_name.rfind('(') + 1:-1].strip()
    return col_name


def resolve_label(col_name, labels_map):
    """
    Return the display label for a column.
    Checks labels_map (Series ID -> short label) first, then falls back to
    stripping the Series ID suffix from the raw ABS column name.
    """
    if labels_map:
        sid = get_series_id(col_name)
        if sid in labels_map:
            return labels_map[sid]
    # Fallback: strip Series ID and trailing semicolons
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


def resolve_col_format(value_format, col_name):
    """Return effective format for a column ('percent', 'thousands', 'count', 'raw')."""
    if value_format == "mixed":
        sid = get_series_id(col_name)
        if sid in PERCENT_SERIES_IDS:
            return "percent"
        elif sid in THOUSANDS_SERIES_IDS:
            return "thousands"
        return "raw"
    return value_format or "raw"


def fmt_value(value, fmt):
    """Format a float for display in the Latest Values table."""
    if fmt == "percent":
        return f"{value:.2f}%"
    elif fmt == "thousands":
        return f"{value:,.1f}"
    elif fmt == "count":
        return f"{int(round(value)):,}"
    return f"{value:,.2f}"


def fmt_change(change, fmt):
    """Format a change value (with sign) for the Latest Values table."""
    if fmt == "percent":
        return f"{change:+.2f}pp"
    elif fmt in ("thousands", "count"):
        return f"{change:+,.1f}"
    return f"{change:+,.2f}"


# ---------------------------------------------------------------------------
# CLEAN Y-AXIS BOUNDS  (mirrors generate_charts.py logic)
# ---------------------------------------------------------------------------

def compute_clean_ylim(data_min, data_max, n_ticks=7, force_min=None):
    """
    Compute clean y-axis bounds and tick interval so that both the bottom and
    top limits fall on a round tick value.

    Parameters
    ----------
    data_min / data_max : float  — min and max of the data to be plotted
    n_ticks             : int    — target number of ticks
    force_min           : float  — hard lower bound override (e.g. Population)

    Returns (bottom, top, dtick) — all in the same units as the input data.
    """
    span = data_max - data_min
    if span == 0:
        span = abs(data_max) or 1

    raw_interval = span / (n_ticks - 1)
    magnitude    = 10 ** math.floor(math.log10(raw_interval))
    nice_steps   = [1, 2, 2.5, 5, 10]
    interval     = min(nice_steps, key=lambda s: abs(s * magnitude - raw_interval))
    interval    *= magnitude

    bottom = math.floor(data_min / interval) * interval
    top    = math.ceil(data_max  / interval) * interval

    if force_min is not None:
        bottom = force_min

    return bottom, top, interval


def get_yaxis_range(df_view, selected_series, value_format):
    """
    Compute clean y-axis range for the plotted data.
    Returns (bottom, top, dtick) or (None, None, None) if data is empty.
    """
    vals = pd.concat(
        [df_view[c].dropna() for c in selected_series if c in df_view.columns],
        ignore_index=True
    )
    if vals.empty:
        return None, None, None

    return compute_clean_ylim(float(vals.min()), float(vals.max()))


# ---------------------------------------------------------------------------
# XAXIS TICK HELPERS
# ---------------------------------------------------------------------------

def get_biannual_tickvals(index):
    """
    Return a list of Timestamps for every March and September present in
    or bounding the date index — matching the bi-annual tick style in
    generate_charts.py.
    """
    if index.empty:
        return []
    start = index.min().to_period('Q').start_time
    end   = index.max().to_period('Q').end_time
    ticks = pd.date_range(start=start, end=end, freq='QS-MAR')
    # Keep only March and September quarter starts
    return [t for t in ticks if t.month in (3, 9)]


# ---------------------------------------------------------------------------
# FILE MAP
# ---------------------------------------------------------------------------

def build_file_map():
    """
    Build { "Dataset Name": [ (csv_filename, display_name, value_format,
                               labels_map), ... ] }
    from the config registry.  Falls back to directory scan if unavailable.
    """
    file_map = {}

    if REGISTRY_AVAILABLE:
        for dataset in ABS_DATASETS:
            name    = sanitise_title(dataset['name'])
            entries = []

            # Merged output datasets (e.g. OAD Combined)
            if dataset.get('merge_tables'):
                out_cfg      = dataset.get('merged_output', {})
                filename     = out_cfg.get('filename', 'OAD_Combined.csv')
                display      = sanitise_title(out_cfg.get(
                    'display_title',
                    filename.replace('.csv', '').replace('_', ' ')
                ))
                value_format = out_cfg.get('value_format', 'thousands')
                labels_map   = out_cfg.get('labels', {})
                entries.append((filename, display, value_format, labels_map))

            # Standard table datasets
            for key, value in dataset.get('tables', {}).items():
                if isinstance(value, dict):
                    filename     = value['filename']
                    display      = sanitise_title(value.get(
                        'display_title',
                        filename.replace('.csv', '').replace('_', ' ')
                    ))
                    value_format = value.get('value_format', 'raw')
                    labels_map   = value.get('labels', {})
                else:
                    filename     = value
                    display      = sanitise_title(
                        filename.replace('.csv', '').replace('_', ' '))
                    value_format = 'raw'
                    labels_map   = {}
                entries.append((filename, display, value_format, labels_map))

            if entries:
                file_map[name] = entries

    else:
        if os.path.exists(OUTPUT_DIRECTORY):
            for f in sorted(os.listdir(OUTPUT_DIRECTORY)):
                if f.endswith('.csv'):
                    display = f.replace('.csv', '').replace('_', ' ')
                    group   = f.split('_')[0]
                    if group not in file_map:
                        file_map[group] = []
                    file_map[group].append((f, display, 'raw', {}))

    return file_map


def load_csv(filename):
    """Load a CSV from the output directory with a datetime index."""
    path = os.path.join(OUTPUT_DIRECTORY, filename)
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index, errors='coerce')
    df = df.sort_index()
    return df


# ---------------------------------------------------------------------------
# APP
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="ABS Economic Dashboard",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 ABS Economic Data Dashboard")
    st.caption(
        "Interactive explorer for Australian Bureau of Statistics economic indicators"
    )

    file_map = build_file_map()

    if not file_map:
        st.error(
            f"No data found in '{OUTPUT_DIRECTORY}/'. "
            "Run download.py first to populate the CSV files."
        )
        return

    # ----- SIDEBAR: Data Selection -----
    with st.sidebar:
        st.header("Data Selection")
        dataset_name = st.selectbox("Dataset", list(file_map.keys()))

        tables = file_map[dataset_name]
        if len(tables) > 1:
            table_lookup = {
                display: (filename, vfmt, lmap)
                for filename, display, vfmt, lmap in tables
            }
            selected_display = st.selectbox("Table", list(table_lookup.keys()))
            selected_file, value_format, labels_map = table_lookup[selected_display]
        else:
            selected_file, selected_display, value_format, labels_map = tables[0]

    # ----- LOAD DATA -----
    df = load_csv(selected_file)

    if df is None or df.empty:
        st.warning(f"No data in '{selected_file}'. Run download.py first.")
        return

    # ----- SIDEBAR: Series toggles -----
    with st.sidebar:
        st.divider()
        st.header("Series")
        selected_series = []
        for col in df.columns:
            label = resolve_label(col, labels_map)
            if st.checkbox(label, value=True, key=col):
                selected_series.append(col)

    # ----- SIDEBAR: Date range -----
    with st.sidebar:
        st.divider()
        st.header("Date Range")
        min_date = df.index.min().to_pydatetime()
        max_date = df.index.max().to_pydatetime()
        date_range = st.slider(
            "Adjust range",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="MMM YYYY"
        )

    mask    = (df.index >= pd.Timestamp(date_range[0])) & \
              (df.index <= pd.Timestamp(date_range[1]))
    df_view = df.loc[mask]

    if not selected_series:
        st.info("Toggle at least one series on in the sidebar.")
        return

    # ----- CHART -----
    fig = go.Figure()

    for i, col in enumerate(selected_series):
        col_fmt = resolve_col_format(value_format, col)
        label   = resolve_label(col, labels_map)

        if col_fmt == "percent":
            hover_fmt    = ".2f"
            hover_suffix = "%"
        elif col_fmt == "count":
            hover_fmt    = ",.0f"
            hover_suffix = ""
        else:
            hover_fmt    = ",.1f"
            hover_suffix = ""

        fig.add_trace(go.Scatter(
            x=df_view.index,
            y=df_view[col],
            name=label,
            line=dict(
                color=COLORS[i % len(COLORS)],
                width=2.5 if i == 0 else 1.8
            ),
            hovertemplate=(
                f'%{{x|%b %Y}}<br>%{{y:{hover_fmt}}}{hover_suffix}'
                f'<extra>{label}</extra>'
            )
        ))

    # Y-axis label
    y_titles = {
        "percent":   "Rate (%)",
        "thousands": "Persons ('000)",
        "count":     "Dwellings ('000)",
        "index":     "Index",
        "mixed":     "Value",
        "raw":       "Value",
    }
    y_title = y_titles.get(value_format or "raw", "Value")

    # Clean y-axis range
    y_bottom, y_top, y_dtick = get_yaxis_range(df_view, selected_series, value_format)

    # Bi-annual x-axis ticks
    tickvals = get_biannual_tickvals(df_view.index)

    # Chart title
    chart_title = ensure_australian(
        sanitise_title(f"{dataset_name}: {selected_display}")
    )

    fig.update_layout(
        title=dict(
            text=chart_title,
            font=dict(size=16, family="Calibri, Arial, sans-serif")
        ),
        font=dict(family="Calibri, Arial, sans-serif", size=12),
        template="plotly_white",
        hovermode="x unified",
        yaxis=dict(
            title=y_title,
            gridcolor='#e0e0e0',
            range=[y_bottom, y_top] if y_bottom is not None else None,
            dtick=y_dtick,
            tickformat=".1f" if value_format == "percent" else None,
        ),
        xaxis=dict(
            gridcolor='#e0e0e0',
            tickvals=tickvals,
            tickformat="%b-%y",
            tickangle=90,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="left",
            x=0,
            font=dict(size=11)
        ),
        margin=dict(t=60, b=120),
        height=540,
    )

    st.plotly_chart(fig, use_container_width=True)

    # ----- LATEST VALUES TABLE -----
    st.subheader("Latest Values")

    rows = []
    for col in selected_series:
        series  = df_view[col].dropna()
        col_fmt = resolve_col_format(value_format, col)
        label   = resolve_label(col, labels_map)

        if len(series) >= 2:
            latest = series.iloc[-1]
            prev   = series.iloc[-2]
            change = latest - prev
            pct    = (change / abs(prev) * 100) if prev != 0 else 0.0
            rows.append({
                "Series":   label,
                "Date":     series.index[-1].strftime('%b %Y'),
                "Latest":   fmt_value(latest, col_fmt),
                "Previous": fmt_value(prev,   col_fmt),
                "Change":   fmt_change(change, col_fmt),
                "% Change": f"{pct:+.2f}%",
            })
        elif len(series) == 1:
            rows.append({
                "Series":   label,
                "Date":     series.index[-1].strftime('%b %Y'),
                "Latest":   fmt_value(series.iloc[-1], col_fmt),
                "Previous": "—",
                "Change":   "—",
                "% Change": "—",
            })

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ----- FOOTER -----
    st.divider()
    st.caption(
        "Data Source: Australian Bureau of Statistics  |  Analysis by Chris Angus"
    )


if __name__ == "__main__":
    main()
