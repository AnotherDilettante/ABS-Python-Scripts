# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Automated pipeline for downloading, processing, and visualizing Australian Bureau of Statistics (ABS) economic indicators. Downloads time series data via the `readabs` package, saves filtered CSVs, generates static PNG charts (matplotlib), and serves an interactive Streamlit/Plotly dashboard.

**Tech stack:** Python, pandas, matplotlib, Streamlit, Plotly, readabs, rich

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Interactive TUI control center (orchestrates everything)
python start.py

# Download data from ABS (all datasets)
python download.py

# Download with filters
python download.py --freq Monthly      # Monthly datasets only
python download.py --freq Quarterly    # Quarterly datasets only
python download.py --cat 6401.0        # Specific catalogue only
python download.py --list              # List datasets without downloading

# Generate static PNG charts from downloaded CSVs
python generate_charts.py

# Launch interactive Streamlit dashboard
streamlit run dashboard.py
```

There are no tests or linters configured in this project.

## Architecture

### Data Flow

`config.py` (dataset registry) -> `download.py` (fetch from ABS API) -> `abs_data_output/*.csv` -> `generate_charts.py` (static PNGs to `abs_charts_output/`) + `dashboard.py` (interactive web UI)

### Key Files

- **config.py** — Central dataset registry. `ABS_DATASETS` list defines every dataset's catalogue ID, frequency, table keys, Series IDs (`plot_ids`), display titles, `calc_type`, `value_format`, and resampling settings. All other scripts import from here.
- **download.py** — Fetches data via `readabs.read_abs_cat()`, filters to configured Series IDs, renames columns to `Description (SERIES_ID)` format, trims to `HISTORY_YEARS` rows, optionally resamples monthly->quarterly, saves CSVs.
- **generate_charts.py** — Reads CSVs, applies `calc_type` transformations, produces styled line charts (red primary / black secondary, 300 DPI).
- **dashboard.py** — Streamlit app with Plotly charts, series toggles, date range slider, and latest-values table. Reads CSVs live.
- **start.py** — Rich TUI menu that wraps all pipeline operations via subprocess.

### Critical Patterns

**Adding a new dataset:** Add an entry to `ABS_DATASETS` in `config.py`. All downstream scripts (download, charts, dashboard) pick it up automatically. Test with `python download.py --cat <id>`.

**Monthly-to-quarterly resampling:** Monthly datasets use `resample_to_quarterly: True` with `resample_method` ("sum" for counts, "last" for rates). This aligns them with natively quarterly datasets.

**OAD merge handler:** The Overseas Arrivals & Departures dataset (3401.0) uses `merge_tables` config instead of `tables`. `download.py:process_merged_oad()` joins arrivals + departures from separate ABS tables, converts to thousands, and derives a net column.

**PeriodIndex handling:** `readabs` returns PeriodIndex for monthly data. Always use `ensure_datetime_index()` from `download.py` (calls `.to_timestamp()`) before any date operations. Never use `pd.to_datetime()` directly on readabs monthly output.

**Mixed value formats:** Datasets with `"value_format": "mixed"` resolve per-series formatting via `PERCENT_SERIES_IDS` and `THOUSANDS_SERIES_IDS` lookup sets. These are duplicated in both `generate_charts.py` and `dashboard.py` — when adding a mixed-format series, update both files.

**Column naming convention:** Downloaded CSVs use `Data Item Description (SERIES_ID)` format. Chart/dashboard code extracts the Series ID from parentheses at the end of column names via `get_series_id()`.

### Output Directories (gitignored, regenerated)

- `abs_data_output/` — 10 CSV files
- `abs_charts_output/` — 10 PNG charts
- `.readabs_cache/` — readabs download cache (delete to force re-download)

## Conventions

- All print statements and string literals must use ASCII only (no Unicode arrows, bullets, or em-dashes). The Windows terminal (cp1252) cannot render them. Use `->`, `|`, and `-` as substitutes.
- Chart styling: primary series in `#ED3144` (red), secondary in `#000000` (black), 300 DPI, Roboto font with fallback chain.
- `calc_type` options: `"raw"` (default), `"yoy"`, `"qoq"`, `"mom"`.
- `value_format` options: `"percent"`, `"thousands"`, `"count"`, `"index"`, `"raw"` (default), `"mixed"`.
