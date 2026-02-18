# ABS Data Automation & Visualization Pipeline

**Goal:** Automate the extraction, cleaning, and visualization of key Australian economic
indicators (GDP, CPI, Labour Force, etc.) from the Australian Bureau of Statistics (ABS).

**Tech Stack:** Python, Pandas, Matplotlib, Streamlit, Plotly, `readabs`

---

## 1. Script Directory

### `start.py` - Control Center (TUI)
Interactive terminal menu that orchestrates the entire pipeline from a single entry point.
- Real-time status: file counts, last update times, dependency checks
- One-click download, chart generation, dashboard launch, or full update
- Built with the `rich` library
- **Usage:** `python start.py`

### `config.py` - Configuration Registry
Master list of all datasets, tables, and Series IDs to track.
- `ABS_DATASETS` list defines Catalogue ID, frequency, tables, and Series IDs
- Per-table settings: `display_title`, `calc_type`, `value_format`, `plot_ids`
- Per-dataset settings: `resample_to_quarterly`, `resample_method` for monthly data
- Special `merge_tables` + `merged_output` config for OAD combined file
- Global: `HISTORY_YEARS = 10`, `OUTPUT_DIRECTORY = "abs_data_output"`

### `download.py` - Data Downloader
Fetches data from ABS via the `readabs` package and saves filtered CSVs.
- Handles standard tables, quarterly resampling, and the OAD merge
- `ensure_datetime_index()` converts readabs PeriodIndex to DatetimeIndex safely
- `resample_quarterly()` converts monthly data to quarterly (sum/last/mean)
- `process_merged_oad()` merges arrivals + departures, derives net, saves as OAD_Combined.csv
- **CLI flags:** `--freq Monthly/Quarterly`, `--cat 6401.0`, `--list`
- **Usage:** `python download.py` or `python download.py --freq Monthly`

### `generate_charts.py` - Static Chart Generator
Creates publication-quality PNG charts from the CSV files.
- Red/black line styling, 300 DPI, Roboto font with fallback
- Format-aware end-of-line labels and y-axis titles via `value_format` setting
- Supports `calc_type` transformations (raw, yoy, qoq, mom)
- `chart_merged_output()` handles OAD Combined; `chart_standard_tables()` handles everything else
- **Usage:** `python generate_charts.py`

### `dashboard.py` - Interactive Dashboard
Streamlit web app for dynamic data exploration.
- Dataset/table/series selection, date range slider
- Interactive Plotly charts (hover, zoom, pan)
- Format-aware Latest Values table (%, '000s, counts)
- Reads CSVs live - refresh browser after downloading new data
- **Usage:** `streamlit run dashboard.py` (opens at http://localhost:8501)

---

## 2. Current Dataset Coverage

| Dataset | Cat ID | Frequency | Output File | Series |
|---------|--------|-----------|-------------|--------|
| National Accounts (GDP) | 5206.0 | Quarterly | GDP_Key_Aggregates_sa.csv | 6 |
| CPI | 6401.0 | Monthly -> Quarterly | CPI_Table1_All_Groups.csv | 2 |
| CPI | 6401.0 | Monthly -> Quarterly | CPI_Table6_CPI_Means.csv | 3 |
| Building Activity | 8752.0 | Quarterly | Building_Activity_Table33_Starts.csv | 3 |
| Building Activity | 8752.0 | Quarterly | Building_Activity_Table37_Completions.csv | 3 |
| Building Approvals | 8731.0 | Monthly -> Quarterly (sum) | Building_Approvals_Table6_Dwellings_sa.csv | 3 |
| Population | 3101.0 | Quarterly | Population_Table1_ERP.csv | 4 |
| Overseas Arrivals & Departures | 3401.0 | Monthly -> Quarterly (sum) | OAD_Combined.csv | 3 (arrivals, departures, net) |
| Labour Force | 6202.0 | Monthly -> Quarterly | LabourForce_Table1_Unemployment_sa.csv | 3 |
| Labour Force | 6202.0 | Monthly -> Quarterly | LabourForce_Table22_Underemployment_sa.csv | 2 |

**10 CSV files | 10 static PNG charts | 1 interactive dashboard | 10 years of history**

---

## 3. Quick Start

```bash
# Activate virtual environment
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# Install dependencies (first time only)
pip install -r requirements.txt

# Run the control center
python start.py
```

**Or direct commands:**
```bash
python download.py             # Download latest data
python generate_charts.py      # Generate static charts
streamlit run dashboard.py     # Launch interactive dashboard
```

---

## 4. Key Technical Notes

**Quarterly resampling:** Monthly datasets (CPI, Labour Force, Building Approvals, OAD)
are automatically resampled to quarterly frequency for alignment with quarterly datasets
(GDP, Building Activity, Population). Rate/index series use `resample_method: "last"`;
count/movement series use `resample_method: "sum"`.

**OAD merged output:** Arrivals (Table 340101) and Departures (Table 340102) are fetched
separately, merged, converted to '000s, and a net migration column is derived. Output
is OAD_Combined.csv with three columns.

**Value formatting:** Each dataset has a `value_format` setting controlling how values
appear in chart end-of-line labels, y-axis titles, and the dashboard table. Mixed-format
datasets (Population, Labour Force Table 1) resolve format per series via Series ID
lookup tables in generate_charts.py and dashboard.py.

**PeriodIndex handling:** readabs returns a PeriodIndex for monthly data. The helper
`ensure_datetime_index()` in download.py handles conversion safely via `.to_timestamp()`.
Never use `pd.to_datetime()` directly on readabs monthly output.

**Windows encoding:** All print statements and string literals use ASCII only (no Unicode
arrows, bullets, or dashes). The Windows terminal defaults to cp1252 which cannot render
these characters.

---

## 5. Future Enhancements

1. **AI-Generated Commentary** - Claude API integration to auto-generate trend analysis
   and written insights for each chart
2. **Manual Scrapers** - Handle special datasets not supported by readabs:
   - 3407.0 Overseas Migration (Data Cube format)
   - 5352.0 IIP Supplementary (ZIP format)
3. **Cross-Dataset Comparison Charts** - Multi-indicator charts combining series from
   different datasets (feasible now that all data is quarterly-aligned)

See SKILL.md Section 4C for detailed implementation guidance.
