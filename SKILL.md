# ABS Economic Data Pipeline - Skill Guide

**Purpose:** Enable Claude to help maintain, extend, and analyze an automated pipeline for
downloading, processing, and visualizing Australian Bureau of Statistics (ABS) economic
indicators.

**Primary Focus:** Pipeline automation and maintenance
**Secondary Focus:** AI-driven data analysis and commentary generation

---

## 1. CONSTRAINTS & PARAMETERS

### File Structure
```
C:\Users\angus\Sync\Claude Code\ABS-Project\
├── start.py                          # TUI control center (orchestrates all scripts)
├── config.py                         # Configuration registry
├── download.py                       # Data downloader
├── generate_charts.py                # Static chart generator (PNG)
├── dashboard.py                      # Interactive Streamlit web dashboard
├── packages.txt                      # System packages for Streamlit Cloud deployment
├── s00_readabs_datalist-AllTables.py # Reference: Download all tables (not filtered)
├── Key ABS Time Series.xlsx          # Reference: Original dataset list
├── Summary.md                        # Project overview and quick-start guide
├── DASHBOARD_SETUP.md                # Dashboard installation and usage guide
├── SKILL.md                          # This file
├── requirements.txt                  # Python package dependencies
├── check_fonts.py                    # Utility: Verify matplotlib fonts
├── .gitignore                        # Git version control exclusions
├── venv/                             # Python virtual environment
├── abs_data_output/                  # Generated CSV files (tracked in Git for deployment)
├── abs_charts_output/                # Generated PNG charts (gitignored)
├── .readabs_cache/                   # Hidden: readabs download cache (gitignored)
└── __pycache__/                      # Python bytecode cache (gitignored)
```

**Note on abs_data_output/:** The .gitignore line for this folder has been commented out
so CSV files are committed to GitHub. This is required for Streamlit Cloud deployment.
After each monthly data update, commit and push the updated CSVs.

### Python Dependencies

**Core Data Pipeline:**
- **readabs** - ABS data fetching via official API
- **pandas** - Data manipulation and time series handling
- **matplotlib** - Static chart generation (PNG outputs)
- **Standard library:** os, sys, logging, io, warnings, contextlib, argparse, subprocess

**Interactive Dashboard (dashboard.py):**
- **streamlit** - Web dashboard framework
- **plotly** - Interactive charting library

**TUI Control Center (start.py):**
- **rich** - Terminal UI framework for interactive menus and status displays

**Installation:**
```bash
# Using virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt

# Or system-wide
pip install readabs pandas matplotlib streamlit plotly rich --break-system-packages
```

### Virtual Environment (venv)

**Activation:**
```bash
venv\Scripts\activate   # Windows
source venv/bin/activate  # Mac/Linux
```

**Best Practice:** Always activate venv before running scripts or installing packages.

### Core Configuration (config.py)

**Global Parameters:**
```python
HISTORY_YEARS = 10           # Data retention period
OUTPUT_DIRECTORY = "abs_data_output"
```

**Standard Dataset Entry (full example):**
```python
{
    "name": "National Accounts (GDP)",
    "cat_id": "5206.0",              # ABS Catalogue ID
    "frequency": "Quarterly",        # "Monthly", "Quarterly", or "Annual"
    "tables": {
        "5206001_Key_Aggregates": {
            "filename": "GDP_Key_Aggregates_sa.csv",
            "display_title": "Gross Domestic Product - Key Aggregates",
            "calc_type": "raw",          # "raw", "yoy", "qoq", "mom"
            "value_format": "percent",   # see value_format options below
            "clip_percentile": [5, 95],  # optional: clip y-axis to this data range
            "plot_ids": [
                "A2304370T",             # GDP Quarterly Result
                "A2304372W",             # GDP Per Capita
            ],
            "labels": {                  # short legend/sidebar labels keyed by Series ID
                "A2304370T": "GDP",
                "A2304372W": "GDP per capita",
            },
        }
    }
}
```

**Monthly Dataset with Quarterly Resampling:**
```python
{
    "name": "CPI",
    "cat_id": "6401.0",
    "frequency": "Monthly",
    "resample_to_quarterly": True,   # Convert monthly -> quarterly
    "resample_method": "last",       # "sum", "last", or "mean"
    "tables": { ... }
}
```

**Dual-Axis Chart Configuration:**
```python
"dual_axis": {
    "primary_ids":       ["A84423047L"],               # series -> left axis
    "secondary_ids":     ["A84423050A", "A84423051C"], # series -> right axis
    "exclude_ids":       ["A2133256J"],                # drop these series entirely
    "primary_format":    "thousands",
    "secondary_format":  "percent",
    "primary_ymin":      20_000,                       # optional hard lower bound (raw units)
    "y_label_primary":   "Persons (m)",
    "y_label_secondary": "Rate (%)",
},
```

**Merged Output Dataset (OAD):**
```python
{
    "name": "Overseas Arrivals and Departures",
    "cat_id": "3401.0",
    "frequency": "Monthly",
    "resample_to_quarterly": True,
    "resample_method": "sum",
    "merge_tables": {
        "340101": "A85232555A",      # Arrivals series ID
        "340102": "A85232558J",      # Departures series ID
    },
    "merged_output": {
        "filename": "OAD_Combined.csv",
        "display_title": "Overseas Migration - Long Term Movements",
        "calc_type": "raw",
        "value_format": "thousands",
        "y_label": "Persons",
        "labels": {
            "A85232555A": "Arrivals",
            "A85232558J": "Departures",
            "Net":        "Net Arrivals",
        },
        "arrivals_label":   "Long Term Arrivals ('000)",
        "departures_label": "Long Term Departures ('000)",
        "net_label":        "Net Long Term Arrivals ('000)",
    },
    "tables": {},
}
```

**calc_type Options:**
- `"raw"` - No transformation (default)
- `"yoy"` - Year-on-year % change
- `"qoq"` - Quarter-on-quarter % change
- `"mom"` - Month-on-month % change

**value_format Options:**
- `"percent"` - Y-axis: "Rate (%)", title suffix: "(%)"
- `"thousands"` - Y-axis: "Persons ('000)" or "(m)", title suffix: "('000)" or "(m)"
- `"count"` - Y-axis: "Dwellings ('000)", title suffix: "('000)" (divides raw values by 1000)
- `"index"` - Y-axis: "Index", title suffix: "(Index)"
- `"raw"` - Y-axis: "Value", title suffix: "" (default)
- `"mixed"` - Per-series format resolved by Series ID lookup (see Mixed Format section)

**Additional table-level config keys:**
- `"clip_percentile": [5, 95]` - Clip y-axis to 5th-95th percentile of data (used for GDP
  which has Terms of Trade outliers)
- `"y_min"` / `"y_max"` - Hard y-axis limits in raw data units
- `"labels"` - Dict mapping Series ID to short display label (used in chart legends and
  dashboard series checkboxes)

**resample_method Options:**
- `"last"` - Last observation in the quarter (for rates and % changes)
- `"sum"` - Sum all monthly values within the quarter (for counts and movements)
- `"mean"` - Average across the quarter

### Mixed Format Datasets

Some datasets contain series of different types. These use `"value_format": "mixed"` and
the format for each series is resolved by Series ID lookup tables in generate_charts.py
and dashboard.py.

**PERCENT_SERIES_IDS** (displayed as "6.1%"):
- A84423050A - Unemployment rate
- A84423051C - Participation rate
- A85256565A - Underemployment rate
- A85255726K - Underutilisation rate
- A2133256J - Percentage ERP Change

**THOUSANDS_SERIES_IDS** (displayed with '000 / m scaling):
- A84423047L - Labour force total
- A2133251W - Estimated Resident Population
- A2133252X - Natural Increase
- A2133254C - Net Overseas Migration

When adding a new mixed-format series, update both lookup sets in generate_charts.py
and dashboard.py.

### Chart Styling Constants (generate_charts.py)

**Colors (6-colour palette, same in both static charts and dashboard):**
```python
COLORS = ['#ED3144', '#1B4F8A', '#059669', '#D97706', '#7C3AED', '#555555']
```
- First series: Red #ED3144
- Second series: Navy #1B4F8A
- Third: Teal #059669
- Fourth: Amber #D97706
- Fifth: Purple #7C3AED
- Sixth: Dark Grey #555555

**Typography:**
- Font: Calibri (fallback: Roboto -> Arial -> sans-serif)
- Title: 14pt bold (includes scale suffix and date range)
- Subtitle: 9pt, #444444 (frequency label only)
- Axis labels: 10pt semibold
- Tick labels: 10pt
- Legend: 9pt
- Footer: 8pt, #666666

**Layout:**
- DPI: 300, Figure size: (10, 7)
- Top/right spines hidden; light dotted y-grid (#e0e0e0)
- X-axis: bi-annual ticks (March and September), 90 degree rotation, "%b-%y" format
  (e.g. "Mar-16", "Sep-16") — 20 ticks over 10 years, matching house style
- Y-axis: clean rounded bounds via compute_clean_ylim() — both top and bottom always
  land on a round tick value; MultipleLocator ensures even spacing
- Margins: top=0.83, bottom=0.14
- Footer: "Data Source: Australian Bureau of Statistics  |  Analysis by Chris Angus"

**Chart Title Format:**
```
Australian [Display Title] ([scale]), [start date] - [end date]
e.g. "Australian Building Activity - Dwelling Starts ('000), Oct 2015 - Sep 2025"
```

**Dual-axis charts** (Labour Force Table 1, Population):
- Primary series: solid lines on left axis
- Secondary series: dashed lines on right axis
- Legend placed below plot area (bbox_to_anchor=(0.5, -0.18)) to avoid overlap

### Y-Axis Clean Bounds (compute_clean_ylim)

Both generate_charts.py and dashboard.py share the same clean y-axis logic:
1. Compute span of displayed data
2. Pick a nice interval (~7 ticks) from [1, 2, 2.5, 5, 10] * magnitude
3. Floor minimum and ceil maximum to nearest multiple of the interval
4. Both axis bounds land on a labelled tick — no lines extending beyond the last tick

For dual-axis charts, each axis computes its own clean bounds independently.
For clipped charts (GDP), bounds are computed on the percentile-restricted data range.

### Readabs Package Limitations

**CAN Handle:** Standard time series tables, monthly and quarterly frequencies,
Series ID filtering and metadata extraction.

**CANNOT Handle:** Data Cube files, ZIP archives, non-standard formats.

**Note on index types:** readabs returns a PeriodIndex for monthly data and a
DatetimeIndex for quarterly data. Always use `ensure_datetime_index()` before
any date operations. Never use `pd.to_datetime()` directly on readabs monthly output.

**Red Light Datasets** (require manual scraping - not yet implemented):
- 3407.0 - Overseas Migration (Data Cube format)
- 5352.0 - International Investment Position Supplementary (ZIP format)

### Windows Encoding Note

All Python files must use only ASCII characters in string literals and print statements.
The Windows terminal uses cp1252 encoding by default.

Safe substitutes:
- Use `->` instead of Unicode right arrow (U+2192)
- Use `|` instead of Unicode bullet in footers
- Use `-` instead of Unicode dashes in strings

---

## 2. PROCESS GUIDELINES

### Adding New Datasets

**Step 1:** Find catalogue ID and table numbers on abs.gov.au

**Step 2:** Download latest Excel release, note sheet names and Series IDs

**Step 3:** Add entry to config.py:
```python
{
    "name": "Your Dataset Name",
    "cat_id": "####.0",
    "frequency": "Quarterly",
    "tables": {
        "table_id": {
            "filename": "descriptive_name.csv",
            "display_title": "Professional Chart Title",
            "calc_type": "raw",
            "value_format": "count",
            "plot_ids": ["A########X"],
            "labels": {"A########X": "Short Label"},
        }
    }
}
```

**Step 4:** Test:
```bash
python download.py --cat ####.0
python generate_charts.py
streamlit run dashboard.py
```

### Running Regular Updates

**Using the TUI (recommended):**
```bash
python start.py
# Option 4: Full update (download + charts)
```

**Direct CLI:**
```bash
python download.py                    # all datasets
python download.py --freq Monthly     # monthly only
python download.py --freq Quarterly   # quarterly only
python download.py --cat 6401.0       # specific catalogue
python download.py --list             # list datasets without downloading
```

**Update Cycles:**
- Monthly: CPI, Labour Force, Building Approvals, Overseas Migration
- Quarterly: GDP, Building Activity, Population

**After updating, push CSVs to GitHub** (required to update Streamlit Cloud):
```bash
git add abs_data_output/
git commit -m "Data update - Mar 2026"
git push origin main
```

### Troubleshooting Common Issues

**Error: "Table not found"** - Check table ID format, verify in latest ABS Excel.

**Error: "Series ID missing"** - ABS occasionally changes IDs. Download latest Excel,
update plot_ids in config.py.

**TypeError: "Passing PeriodDtype data is invalid"** - readabs returned PeriodIndex.
Use `ensure_datetime_index(df)` instead of `pd.to_datetime()` directly.

**UnicodeEncodeError: 'charmap' codec** - A Unicode character is in a print statement.
Replace with ASCII equivalent.

**Legend overlaps chart** - For standard charts `loc='best'` should clear it with
short labels. For dual-axis, legend is anchored below the plot area.

**Y-axis top/bottom not on round number** - Check compute_clean_ylim() is being called.
If a hard y_min or primary_ymin is set, the floor may not align — this is expected.

---

## 3. QUALITY STANDARDS

### Data Validation

**Row Counts (after any resampling):**
| Frequency | Expected Rows (10 years) |
|-----------|--------------------------|
| Monthly   | 120 +/- 2                |
| Quarterly | 40 +/- 1                 |
| Annual    | 10 +/- 0                 |

**Column Naming Convention:**
- Format: `Data Item Description (SERIES_ID)`
- Exception: OAD_Combined.csv uses plain human-readable labels (no Series ID suffix)

### Chart Quality Standards

**Required text elements:**
1. Title: `Australian [Display Title] ([scale]), [start] - [end]` (14pt bold)
2. Subtitle: Frequency label only, e.g. "Quarterly" (9pt)
3. Y-axis label: derived from value_format (10pt semibold)
4. Legend: short labels from `labels` dict in config (9pt, loc='best')
5. Footer: "Data Source: Australian Bureau of Statistics  |  Analysis by Chris Angus" (8pt)

**Dual-axis charts** must have:
- Left axis label (primary format)
- Right axis label (secondary format)
- Combined legend below plot area

### Error Handling Expectations

Scripts should never crash mid-process. Failed datasets print an error and continue.

**Console output format:**
```
Processing: CPI (Cat: 6401.0) | Freq: Monthly -> Quarterly
  [OK] Saved: CPI_Table1_All_Groups.csv (2 series)
  -> Saved: Chart_CPI_Table1_All_Groups.csv.png
```

---

## 4. OUTPUT EXPECTATIONS

### Current Pipeline Outputs

**CSV Data Files** (in `abs_data_output/`):

| File | Series | Notes |
|------|--------|-------|
| GDP_Key_Aggregates_sa.csv | 6 | Quarterly |
| CPI_Table1_All_Groups.csv | 2 | Monthly -> Quarterly |
| CPI_Table6_CPI_Means.csv | 3 | Monthly -> Quarterly |
| Building_Activity_Table33_Starts.csv | 3 | Quarterly |
| Building_Activity_Table37_Completions.csv | 3 | Quarterly |
| Building_Approvals_Table6_Dwellings_sa.csv | 3 | Monthly -> Quarterly (sum) |
| Population_Table1_ERP.csv | 4 | Quarterly |
| OAD_Combined.csv | 3 | Monthly -> Quarterly (sum); merged arrivals + departures + net |
| LabourForce_Table1_Unemployment_sa.csv | 3 | Monthly -> Quarterly |
| LabourForce_Table22_Underemployment_sa.csv | 2 | Monthly -> Quarterly |

**10 CSV files | 10 static PNG charts | 1 interactive dashboard | 10 years of history**

### Special Chart Configurations

| Chart | Special Config | Reason |
|-------|---------------|--------|
| GDP Key Aggregates | clip_percentile [5,95] | Terms of Trade outliers compress main GDP lines |
| Labour Force Table 1 | dual_axis | Labour force total (m) left; rates (%) right |
| Population Table 1 | dual_axis, primary_ymin=20000 | ERP (m) left from 20m; NOM/NI ('000) right |

---

## 4A. INTERACTIVE DASHBOARD (dashboard.py)

### Overview

Streamlit web app for dynamic data exploration. Reads CSVs live — refresh browser
after updating data.

**Features:**
- Dataset/table dropdowns, series checkboxes, date range slider
- Interactive Plotly charts (hover, zoom, pan)
- Bi-annual x-axis ticks (Mar-16 format), 90 degree rotation
- Calibri font (falls back to Arial in environments without it)
- Clean y-axis bounds using same compute_clean_ylim() logic as static charts
- 6-colour palette matching static charts
- Short legend labels from `labels` dicts in config.py
- Latest Values table with period-on-period changes
- Footer: "Data Source: ABS | Analysis by Chris Angus"

**Launch locally:**
```bash
streamlit run dashboard.py
# Opens at http://localhost:8501
# Stop with Ctrl+C
```

**Hosted version:** Deployed on Streamlit Community Cloud at the project's public URL.
Updates automatically when new CSVs are pushed to GitHub main branch.

### Dashboard vs Static Charts

| Task | Static Charts | Dashboard |
|------|--------------|-----------|
| Report insertion | Direct PNG embedding | Screenshot needed |
| Exploration | Must regenerate PNGs | Instant toggling |
| Dual-axis charts | Yes (LF, Population) | Single axis only (deferred) |
| Font | Calibri (embedded in PNG) | Calibri/Carlito if installed |
| Sharing | Email PNGs | Public URL (Streamlit Cloud) |

---

## 4B. TUI CONTROL CENTER (start.py)

```bash
python start.py
```

**Menu:**
- **0** - Pipeline status
- **1** - Download data (all / monthly / quarterly)
- **2** - Generate static charts
- **3** - Launch dashboard
- **4** - Full update (download + charts)
- **5** - View configured datasets
- **Q** - Quit

---

## 4C. STREAMLIT CLOUD DEPLOYMENT

The dashboard is deployed publicly on Streamlit Community Cloud.

### Setup (one-time)

1. `abs_data_output/` line in `.gitignore` is commented out so CSVs are tracked
2. `packages.txt` in project root contains `fonts-crosextra-carlito` (Calibri substitute)
3. Repository is public at github.com/AnotherDilettante/ABS-Python-Scripts
4. App deployed at share.streamlit.io pointing to `dashboard.py` on `main` branch

### Monthly Update Workflow

```bash
python download.py                    # refresh data locally
git add abs_data_output/
git commit -m "Data update - Mar 2026"
git push origin main                  # Streamlit Cloud auto-redeploys within ~2 minutes
```

### Font Note

Streamlit Cloud runs on Ubuntu Linux. Calibri is not available. `packages.txt` installs
`fonts-crosextra-carlito` (metrically identical to Calibri) and the dashboard font stack
lists Carlito first: `"Carlito, Calibri, Arial, sans-serif"`.

---

## 4D. FUTURE ENHANCEMENTS

#### A) AI-Generated Commentary

Generate 2-3 sentence trend analysis for each chart via Claude API. Requires:
- Python trend detection (latest value, 1yr change, direction of last 4 periods)
- Claude API call with economic context prompt
- Output as chart text boxes or separate Markdown report

#### B) Manual Scrapers for Special Datasets

Target datasets readabs cannot handle:
- 3407.0 Overseas Migration (Data Cube .xlsx)
- 5352.0 IIP Supplementary (ZIP format)

Approach: `requests` + `BeautifulSoup` to find download link, fetch file, parse manually,
save in standard CSV format.

#### C) Cross-Dataset Comparison Charts

Multi-indicator charts combining series from different datasets (e.g. GDP growth vs
unemployment vs building approvals). Feasible now that all data is quarterly-aligned.

#### D) Dual-Axis Support in Dashboard

Labour Force and Population charts currently show all series on a single axis in the
dashboard. A future enhancement would detect the `dual_axis` config flag and create
a secondary y-axis in Plotly.

---

## 5. USING THIS SKILL WITH CLAUDE

### Workflow Examples

**Monthly Update:**
```
python start.py -> Option 1 (Monthly only) -> review dashboard -> push CSVs to GitHub
```

**Quarterly Update:**
```
python start.py -> Option 4 (Full update) -> review dashboard -> push CSVs to GitHub
```

**Adding a Dataset:**
```
1. Find catalogue ID and Series IDs on abs.gov.au
2. Add entry to config.py (name, cat_id, frequency, tables, plot_ids, labels)
3. python download.py --cat ####.0
4. python generate_charts.py
5. streamlit run dashboard.py
```

**Troubleshooting:**
- Read error message -> check relevant section of this SKILL.md
- For Series ID changes: download latest ABS Excel, find new IDs, update config.py

---

## 6. MAINTENANCE & VERSION CONTROL

### Regular Maintenance

- **Monthly:** Update monthly datasets, push CSVs to GitHub
- **Quarterly:** Full update, push CSVs to GitHub, verify Series IDs
- **Annually:** Review dataset list, upgrade packages

### Changelog

```
### 2026-03-06
- Applied chart house style to dashboard.py:
  - 6-colour palette matching generate_charts.py
  - Calibri/Carlito font via fig.update_layout()
  - Bi-annual x-axis ticks (Mar-16 format), 90 degree rotation
  - Clean y-axis bounds via compute_clean_ylim() (same logic as static charts)
  - Short legend labels from config.py labels dicts
  - "and" replacing "&" throughout
  - "Australian" prefix on chart titles
  - Attribution updated to "Analysis by Chris Angus"
- Deployed dashboard to Streamlit Community Cloud
  - abs_data_output/ now tracked in Git (gitignore line commented out)
  - packages.txt added with fonts-crosextra-carlito
  - Repository made public

### 2026-03-05
- Refactored generate_charts.py for new house style:
  - Font changed to Calibri (Roboto -> Arial fallback)
  - 6-colour palette replacing red/black
  - X-axis: bi-annual ticks (Mar/Sep), 90 degree rotation, "%b-%y" format
  - Y-axis: clean rounded bounds (compute_clean_ylim), MultipleLocator
  - Chart title includes scale suffix and date range
  - Subtitle reduced to frequency label only
  - Footer: "Analysis by Chris Angus" replacing "Chart generated via readabs"
  - Short legend labels from labels dicts in config.py
  - Legend uses loc='best' (standard) or bbox_to_anchor below plot (dual-axis)
  - Dual-axis charts for Labour Force Table 1 and Population Table 1
  - GDP y-axis clipped to 5th-95th percentile
  - Population ERP axis starts at 20m
- Updated config.py:
  - Added labels dicts to all table entries
  - Added dual_axis config to Labour Force Table 1 and Population Table 1
  - Added clip_percentile to GDP
  - "&" replaced with "and" in all names and titles
  - OAD merged_output gains y_label and labels dict

### 2026-02-18
- Fixed UnicodeEncodeError on Windows terminal (cp1252)
- Fixed TypeError from readabs PeriodIndex via ensure_datetime_index()

### 2026-02-16
- Quarterly resampling for monthly datasets
- OAD merge handler (arrivals + departures -> OAD_Combined.csv with net column)
- value_format system (percent, thousands, count, index, mixed)
- Mixed-format support via Series ID lookup tables

### 2026-02-13
- Renamed scripts from numbered prefixes to descriptive names
- CLI arguments added to download.py
- display_title and calc_type fields added to config

### 2025-02-11
- Added interactive Streamlit dashboard
- Virtual environment and requirements.txt

### 2025-02-04
- Initial pipeline: 7 datasets, Series ID filtering, static PNG charts
```

### Version Control

**What gets committed:** All .py scripts, .md docs, requirements.txt, .gitignore,
packages.txt, Key ABS Time Series.xlsx, abs_data_output/ CSVs.

**What gets ignored:** abs_charts_output/, venv/, .readabs_cache/, __pycache__/

**Recovery from backup:**
```bash
git clone <repository-url>
cd ABS-Project
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python download.py
streamlit run dashboard.py
```

---

## 7. CONCLUSION

Three-command workflow:

```bash
python start.py                  # Interactive control center
python download.py               # Direct data download
streamlit run dashboard.py       # Local dashboard
python generate_charts.py        # Static PNG charts
```

**Current State (March 2026):**
- 7 datasets, 10 CSV outputs, 10 static charts + interactive dashboard
- Consistent house style: Calibri, 6-colour palette, bi-annual x-axis, clean y-axis bounds
- Short legend labels centralised in config.py
- Dual-axis charts for Labour Force and Population (static charts only)
- Streamlit Cloud deployment with auto-update on GitHub push
- All monthly datasets resampled to quarterly for cross-dataset alignment
- Full CLI support for selective downloads
- ASCII-safe output for Windows terminal compatibility

**Remaining Roadmap:**
- AI-generated commentary (Claude API integration)
- Manual scrapers for Data Cube / ZIP format datasets
- Cross-dataset multi-indicator comparison charts
- Dual-axis support in dashboard
