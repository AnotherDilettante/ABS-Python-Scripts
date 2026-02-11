# s05_dashboard.py — ABS Economic Data Dashboard
# Run with: streamlit run s05_dashboard.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime

# --- CONFIGURATION ---
OUTPUT_DIRECTORY = "abs_data_output"

# Colour palette — primary red matches your existing charts, then distinct colours for additional series
COLORS = ['#ED3144', '#000000', '#2563EB', '#059669', '#D97706', '#7C3AED']

# --- DATASET REGISTRY ---
# Try to import from s00 for proper grouping and names.
# If s00 isn't found (e.g. running from a different folder), fall back to scanning the CSV directory.
try:
    from s00_readabs_datalist import ABS_DATASETS
    REGISTRY_AVAILABLE = True
except ImportError:
    ABS_DATASETS = []
    REGISTRY_AVAILABLE = False


def build_file_map():
    """
    Build a mapping: { "Dataset Name": [ (csv_filename, display_name), ... ] }
    Uses s00 registry if available, otherwise scans the output directory.
    """
    file_map = {}

    if REGISTRY_AVAILABLE:
        for dataset in ABS_DATASETS:
            name = dataset['name']
            tables = dataset['tables']
            file_map[name] = []
            for key, value in tables.items():
                filename = value['filename'] if isinstance(value, dict) else value
                display = filename.replace('.csv', '').replace('_', ' ')
                file_map[name].append((filename, display))
    else:
        # Fallback: group CSVs by filename prefix (first word before underscore)
        if os.path.exists(OUTPUT_DIRECTORY):
            for f in sorted(os.listdir(OUTPUT_DIRECTORY)):
                if f.endswith('.csv'):
                    display = f.replace('.csv', '').replace('_', ' ')
                    group = f.split('_')[0]
                    if group not in file_map:
                        file_map[group] = []
                    file_map[group].append((f, display))

    return file_map


def load_csv(filename):
    """Load a CSV from the output directory, return DataFrame with datetime index."""
    path = os.path.join(OUTPUT_DIRECTORY, filename)
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


def short_name(col):
    """Extract description from 'Description (SeriesID)' column format."""
    if '(' in col:
        return col[:col.rfind('(')].strip()
    return col


# =============================================================================
# APP LAYOUT
# =============================================================================

def main():
    st.set_page_config(
        page_title="ABS Economic Dashboard",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 ABS Economic Data Dashboard")
    st.caption("Interactive explorer for Australian Bureau of Statistics economic indicators")

    # Build dataset -> file mapping
    file_map = build_file_map()

    if not file_map:
        st.error(
            f"No data found in '{OUTPUT_DIRECTORY}/'. "
            "Run your download script (s01) first to populate the CSV files."
        )
        return

    # ----- SIDEBAR: Data Selection -----
    with st.sidebar:
        st.header("Data Selection")

        # 1. Pick a dataset
        dataset_name = st.selectbox("Dataset", list(file_map.keys()))

        # 2. Pick a table within that dataset (if more than one)
        tables = file_map[dataset_name]
        if len(tables) > 1:
            table_lookup = {display: filename for filename, display in tables}
            selected_display = st.selectbox("Table", list(table_lookup.keys()))
            selected_file = table_lookup[selected_display]
        else:
            selected_file = tables[0][0]
            selected_display = tables[0][1]

    # ----- LOAD DATA -----
    df = load_csv(selected_file)

    if df is None or df.empty:
        st.warning(f"No data in {selected_file}. Run s01 to download, then try again.")
        return

    # Build short-name lookup for columns
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

    # Apply date filter
    mask = (df.index >= pd.Timestamp(date_range[0])) & (df.index <= pd.Timestamp(date_range[1]))
    df_view = df.loc[mask]

    if not selected_series:
        st.info("Toggle at least one series on in the sidebar.")
        return

    # ----- CHART -----
    fig = go.Figure()

    for i, col in enumerate(selected_series):
        color = COLORS[i % len(COLORS)]
        fig.add_trace(go.Scatter(
            x=df_view.index,
            y=df_view[col],
            name=col_short[col],
            line=dict(color=color, width=2.5 if i == 0 else 1.5),
            hovertemplate='%{x|%b %Y}<br>%{y:,.1f}<extra>' + col_short[col] + '</extra>'
        ))

    fig.update_layout(
        title=dict(
            text=f"{dataset_name}: {selected_display}",
            font=dict(size=18)
        ),
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="left",
            x=0
        ),
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
        if len(series) >= 2:
            latest = series.iloc[-1]
            prev = series.iloc[-2]
            change = latest - prev
            pct = (change / prev * 100) if prev != 0 else 0.0
            rows.append({
                "Series": col_short[col],
                "Date": series.index[-1].strftime('%b %Y'),
                "Latest": f"{latest:,.1f}",
                "Previous": f"{prev:,.1f}",
                "Change": f"{change:+,.1f}",
                "% Change": f"{pct:+,.2f}%",
            })
        elif len(series) == 1:
            rows.append({
                "Series": col_short[col],
                "Date": series.index[-1].strftime('%b %Y'),
                "Latest": f"{series.iloc[-1]:,.1f}",
                "Previous": "—",
                "Change": "—",
                "% Change": "—",
            })

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ----- FOOTER -----
    st.divider()
    st.caption("Data Source: Australian Bureau of Statistics  •  Dashboard powered by Streamlit + Plotly")


if __name__ == "__main__":
    main()
