# ABS Data Automation & Visualization Pipeline

**Goal:** Automate the extraction, cleaning, and visualization of key Australian economic
indicators (GDP, CPI, Labour Force, etc.) from the Australian Bureau of Statistics (ABS).

**Tech Stack:** Python, Pandas, Matplotlib, Streamlit, Plotly, `readabs`, `rich`

---

## 1. Script Directory

### `start.py` — Control Center (TUI)
Interactive terminal menu that orchestrates the entire pipeline from a single entry point.
- Real-time status: file counts, last update times, dependency checks
- Menu: download, chart generation, dashboard launch, full update, dataset list
- Built with the `rich` library
- **Usage:** `python start.py`

### `config.py` — Configuration Registry
Master list of all datasets, tables, and Series IDs to track.
- `ABS_DATASETS` list defines Catalogue ID, frequency, tables, Series IDs, and labels
- Per-table settings: `display_title`, `calc_type`, `value_format`, `plot_ids`, `labels`
- Per-dataset settings: `resample_to_quarterly`, `resample_method` for monthly data
- Special `merge_tables` + `merged_output` config for OAD combined file
- `dual_axis` config for Labour Force Table 1 and Population (static charts only)
- Global: `HISTORY_YEARS = 10`, `OUTPUT_DIRECTORY = "abs_data_output"`

### `download.py` — Data Downloader
Fetches data from ABS via the `readabs` package and saves filtered CSVs.
- `ensure_datetime_index()` converts readabs PeriodIndex to DatetimeIndex safely
- `resample_quarterly()` converts monthly data to quarterly (sum/last/mean)
- `process_merged_oad()` merges arrivals + departures, derives net, saves OAD_Combined.csv
- **CLI flags:** `--freq Monthly/Quarterly`, `--cat 6401.0`, `--list`
- **Usage:** `python download.py` or `python download.py --freq Monthly`

### `generate_charts.py` — Static Chart Generator
Creates publication-quality PNG charts from the CSV files.
- House style: Calibri font, 6-colour palette, bi-annual x-axis ticks (Mar-16, 90 deg),
  clean rounded y-axis bounds, short legend labels from config.py labels dicts
- Dual-axis charts for Labour Force Table 1 and Population Table 1
- GDP y-axis clipped to 5th-95th percentile (Terms of Trade outlier management)
- Footer: "Data Source: Australian Bureau of Statistics | Analysis by Chris Angus"
- **Usage:** `python generate_charts.py`

### `dashboard.py` — Interactive Dashboard
Streamlit web app for dynamic data exploration.
- Matching house style: same 6-colour palette, Calibri/Carlito font, bi-annual x-axis,
  clean y-axis bounds, short labels from config.py
- Dataset/table/series selection, date range slider
- Interactive Plotly charts (hover, zoom, pan)
- Latest Values table with period-on-period changes
- **Local:** `streamlit run dashboard.py` -> http://localhost:8501
- **Remote:** Deployed on Streamlit Community Cloud, auto-updates on GitHub push

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
| Overseas Arrivals and Departures | 3401.0 | Monthly -> Quarterly (sum) | OAD_Combined.csv | 3 |
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
streamlit run dashboard.py     # Launch interactive dashboard locally
```

---

## 4. Key Technical Notes

**Quarterly resampling:** Monthly datasets (CPI, Labour Force, Building Approvals, OAD)
are automatically resampled to quarterly for alignment with quarterly datasets.
Rate/index series use `resample_method: "last"`; count/movement series use `"sum"`.

**OAD merged output:** Arrivals and Departures fetched from separate tables, merged,
converted to '000s, net column derived. Output: OAD_Combined.csv (3 columns).

**Value formatting:** `value_format` in config controls how values appear in chart labels,
y-axis titles, and the dashboard table. Mixed-format datasets resolve per series via
Series ID lookup tables in generate_charts.py and dashboard.py.

**Short labels:** Every table entry in config.py has a `labels` dict mapping Series IDs
to short display names. These are used in chart legends, dashboard series checkboxes,
and hover tooltips. Centralising labels in config.py keeps static charts and dashboard
consistent.

**PeriodIndex handling:** readabs returns PeriodIndex for monthly data. Use
`ensure_datetime_index()` — never `pd.to_datetime()` directly on readabs output.

**Windows encoding:** All print statements use ASCII only (no Unicode arrows, bullets,
or dashes). Windows terminal defaults to cp1252.

**Dual-axis charts (static only):** Labour Force Table 1 and Population Table 1 use
two y-axes. Config via `dual_axis` dict in config.py. Not yet implemented in dashboard.

---

## 5. Streamlit Cloud Deployment

The dashboard is hosted publicly on Streamlit Community Cloud.

- Repository: github.com/AnotherDilettante/ABS-Python-Scripts (public)
- `abs_data_output/` CSVs are committed to Git (gitignore line commented out)
- `packages.txt` installs `fonts-crosextra-carlito` for Calibri substitute on Linux
- Any push to main auto-redeploys the live app within ~2 minutes

**Monthly update workflow:**
```bash
python download.py
git add abs_data_output/
git commit -m "Data update - Mar 2026"
git push origin main
```

---

## 6. Future Enhancements

1. **AI-Generated Commentary** — Claude API integration to auto-generate trend analysis
2. **Manual Scrapers** — Handle datasets not supported by readabs:
   - 3407.0 Overseas Migration (Data Cube format)
   - 5352.0 IIP Supplementary (ZIP format)
3. **Cross-Dataset Comparison Charts** — Multi-indicator charts combining series from
   different datasets (feasible now that all data is quarterly-aligned)
4. **Dual-Axis Support in Dashboard** — Detect `dual_axis` config and create secondary
   y-axis in Plotly for Labour Force and Population charts

See SKILL.md Section 4D for detailed implementation guidance.
