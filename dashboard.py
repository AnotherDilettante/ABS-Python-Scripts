# dashboard.py — ABS Economic Data Dashboard
# Run with: streamlit run dashboard.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# --- CONFIGURATION ---
OUTPUT_DIRECTORY = "abs_data_output"

COLORS = ['#ED3144', '#000000', '#2563EB', '#059669', '#D97706', '#7C3AED']

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
# HELPERS
# ---------------------------------------------------------------------------

def get_series_id(col_name):
    """Extract Series ID from 'Description (SERIES_ID)' column format."""
    if '(' in col_name and col_name.endswith(')'):
        return col_name[col_name.rfind('(') + 1:-1].strip()
    return col_name


def resolve_col_format(value_format, col_name):
    """Return effective format for a column ('percent', 'thousands', 'count', 'raw')."""
    if value_format == "mixed":
        sid = get_series_id(col_name)
        if sid in PERCENT_SERIES_IDS:
            return "percent"
        elif sid in THOUSANDS_SERIES_IDS:
            return "thousands"
        else:
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
    else:
        return f"{value:,.2f}"


def fmt_change(change, fmt):
    """Format a change value (with sign) for the Latest Values table."""
    if fmt == "percent":
        return f"{change:+.2f}pp"   # percentage-point change
    elif fmt in ("thousands", "count"):
        return f"{change:+,.1f}"
    else:
        return f"{change:+,.2f}"


def build_file_map():
    """
    Build { "Dataset Name": [ (csv_filename, display_name, value_format), ... ] }
    from the config registry.  Falls back to directory scan if config unavailable.
    """
    file_map = {}

    if REGISTRY_AVAILABLE:
        for dataset in ABS_DATASETS:
            name = dataset['name']
            entries = []

            # Merged output datasets (e.g. OAD Combined)
            if dataset.get('merge_tables'):
                out_cfg = dataset.get('merged_output', {})
                filename     = out_cfg.get('filename', 'OAD_Combined.csv')
                display      = out_cfg.get('display_title',
                               filename.replace('.csv', '').replace('_', ' '))
                value_format = out_cfg.get('value_format', 'thousands')
                entries.append((filename, display, value_format))

            # Standard table datasets
            for key, value in dataset.get('tables', {}).items():
                if isinstance(value, dict):
                    filename     = value['filename']
                    display      = value.get('display_title',
                                   filename.replace('.csv', '').replace('_', ' '))
                    value_format = value.get('value_format', 'raw')
                else:
                    filename     = value
                    display      = filename.replace('.csv', '').replace('_', ' ')
                    value_format = 'raw'
                entries.append((filename, display, value_format))

            if entries:
                file_map[name] = entries

    else:
        # Fallback: scan directory, no format info available
        if os.path.exists(OUTPUT_DIRECTORY):
            for f in sorted(os.listdir(OUTPUT_DIRECTORY)):
                if f.endswith('.csv'):
                    display = f.replace('.csv', '').replace('_', ' ')
                    group = f.split('_')[0]
                    if group not in file_map:
                        file_map[group] = []
                    file_map[group].append((f, display, 'raw'))

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


def short_name(col):
    """Strip Series ID suffix from column name."""
    if '(' in col:
        return col[:col.rfind('(')].strip()
    return col


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
    st.caption("Interactive explorer for Australian Bureau of Statistics economic indicators")

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
            # (filename, display, value_format)
            table_lookup = {display: (filename, vfmt)
                            for filename, display, vfmt in tables}
            selected_display = st.selectbox("Table", list(table_lookup.keys()))
            selected_file, value_format = table_lookup[selected_display]
        else:
            selected_file, selected_display, value_format = tables[0]

    # ----- LOAD DATA -----
    df = load_csv(selected_file)

    if df is None or df.empty:
        st.warning(f"No data in '{selected_file}'. Run download.py first.")
        return

    col_short = {col: short_name(col) for col in df.columns}

    # ----- SIDEBAR: Series toggles -----
    with st.sidebar:
        st.divider()
        st.header("Series")
        selected_series = []
        for col in df.columns:
            if st.checkbox(col_short[col], value=True, key=col):
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

    mask = (df.index >= pd.Timestamp(date_range[0])) & \
           (df.index <= pd.Timestamp(date_range[1]))
    df_view = df.loc[mask]

    if not selected_series:
        st.info("Toggle at least one series on in the sidebar.")
        return

    # ----- CHART -----
    fig = go.Figure()

    for i, col in enumerate(selected_series):
        col_fmt = resolve_col_format(value_format, col)

        # Hover format string
        if col_fmt == "percent":
            hover_fmt = ".2f"
            hover_suffix = "%"
        elif col_fmt == "count":
            hover_fmt = ",.0f"
            hover_suffix = ""
        else:
            hover_fmt = ",.1f"
            hover_suffix = ""

        fig.add_trace(go.Scatter(
            x=df_view.index,
            y=df_view[col],
            name=col_short[col],
            line=dict(color=COLORS[i % len(COLORS)], width=2.5 if i == 0 else 1.5),
            hovertemplate=(
                f'%{{x|%b %Y}}<br>%{{y:{hover_fmt}}}{hover_suffix}'
                f'<extra>{col_short[col]}</extra>'
            )
        ))

    # Y-axis title
    y_titles = {
        "percent":   "% / Rate",
        "thousands": "'000s",
        "count":     "Dwellings",
        "index":     "Index",
        "mixed":     "Value",
        "raw":       "Value",
    }
    y_title = y_titles.get(value_format or "raw", "Value")

    fig.update_layout(
        title=dict(text=f"{dataset_name}: {selected_display}", font=dict(size=18)),
        template="plotly_white",
        hovermode="x unified",
        yaxis_title=y_title,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="left", x=0),
        margin=dict(t=60, b=100),
        height=520,
    )
    fig.update_xaxes(gridcolor='#e0e0e0')
    fig.update_yaxes(gridcolor='#e0e0e0')

    st.plotly_chart(fig, use_container_width=True)

    # ----- LATEST VALUES TABLE -----
    st.subheader("Latest Values")

    rows = []
    for col in selected_series:
        series = df_view[col].dropna()
        col_fmt = resolve_col_format(value_format, col)

        if len(series) >= 2:
            latest = series.iloc[-1]
            prev   = series.iloc[-2]
            change = latest - prev
            pct    = (change / abs(prev) * 100) if prev != 0 else 0.0

            rows.append({
                "Series":    col_short[col],
                "Date":      series.index[-1].strftime('%b %Y'),
                "Latest":    fmt_value(latest, col_fmt),
                "Previous":  fmt_value(prev,   col_fmt),
                "Change":    fmt_change(change, col_fmt),
                "% Change":  f"{pct:+.2f}%",
            })
        elif len(series) == 1:
            rows.append({
                "Series":    col_short[col],
                "Date":      series.index[-1].strftime('%b %Y'),
                "Latest":    fmt_value(series.iloc[-1], col_fmt),
                "Previous":  "—",
                "Change":    "—",
                "% Change":  "—",
            })

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ----- FOOTER -----
    st.divider()
    st.caption(
        "Data Source: Australian Bureau of Statistics  •  "
        "Dashboard powered by Streamlit + Plotly"
    )


if __name__ == "__main__":
    main()
