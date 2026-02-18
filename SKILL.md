# ABS Economic Data Pipeline - Skill Guide

**Purpose:** Enable Claude to help maintain, extend, and analyze an automated pipeline for downloading, processing, and visualizing Australian Bureau of Statistics (ABS) economic indicators.

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
├── s00_readabs_datalist-AllTables.py # Reference: Download all tables (not filtered)
├── Key ABS Time Series.xlsx          # Reference: Original dataset list
├── Summary.md                        # Project overview and quick-start guide
├── DASHBOARD_SETUP.md                # Dashboard installation and usage guide
├── SKILL.md                          # This file
├── requirements.txt                  # Python package dependencies
├── check_fonts.py                    # Utility: Verify matplotlib fonts
├── .gitignore                        # Git version control exclusions
├── venv/                             # Python virtual environment
├── abs_data_output/                  # Generated CSV files (gitignored)
├── abs_charts_output/                # Generated PNG charts (gitignored)
├── .readabs_cache/                   # Hidden: readabs download cache (gitignored)
└── __pycache__/                      # Python bytecode cache (gitignored)
```

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

**Standard Dataset Entry:**
```python
{
    "name": "National Accounts (GDP)",
    "cat_id": "5206.0",              # ABS Catalogue ID
    "frequency": "Quarterly",        # "Monthly", "Quarterly", or "Annual"
    "tables": {
        "5206001_Key_Aggregates": {
            "filename": "GDP_Key_Aggregates_sa.csv",
            "display_title": "Gross Domestic Product - Key Aggregates",
            "calc_type": "raw",      # "raw", "yoy", "qoq", "mom"
            "value_format": "percent",
            "plot_ids": [
                "A2304370T",         # GDP Quarterly Result
                "A2304372W",         # GDP Per Capita
            ]
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

**Merged Output Dataset (OAD):**
```python
{
    "name": "Overseas Arrivals & Departures",
    "cat_id": "3401.0",
    "frequency": "Monthly",
    "resample_to_quarterly": True,
    "resample_method": "sum",
    "merge_tables": {                # Fetch + merge multiple series
        "340101": "A85232555A",      # Arrivals series ID
        "340102": "A85232558J",      # Departures series ID
    },
    "merged_output": {
        "filename": "OAD_Combined.csv",
        "display_title": "Overseas Migration - Long Term Movements",
        "calc_type": "raw",
        "value_format": "thousands",
        "arrivals_label":   "Long Term Arrivals ('000)",
        "departures_label": "Long Term Departures ('000)",
        "net_label":        "Net Long Term Arrivals ('000)",
    },
    "tables": {},                    # Empty - handled via merge_tables
}
```

**calc_type Options:**
- `"raw"` - No transformation, plot source values as-is (default)
- `"yoy"` - Year-on-year % change (12 periods for monthly, 4 for quarterly)
- `"qoq"` - Quarter-on-quarter % change (1 period)
- `"mom"` - Month-on-month % change (1 period)

**value_format Options:**
- `"percent"` - End label: "6.1%", Y-axis: "% / Rate"
- `"thousands"` - End label: "61.0", Y-axis: "'000s"
- `"count"` - End label: "18,797", Y-axis: "Dwellings"
- `"index"` - End label: "102.3", Y-axis: "Index"
- `"raw"` - End label: "18,797.0", Y-axis: "Value" (default)
- `"mixed"` - Per-series format resolved by Series ID lookup (see below)

**resample_method Options:**
- `"last"` - Use the last observation in the quarter (for rates and % changes)
- `"sum"` - Sum all monthly values within the quarter (for counts and movements)
- `"mean"` - Average across the quarter

**Frequency-Based Row Calculation:**
- Monthly: HISTORY_YEARS x 12 rows
- Quarterly: HISTORY_YEARS x 4 rows
- Half-yearly: HISTORY_YEARS x 2 rows
- Annual: HISTORY_YEARS x 1 row

### Mixed Format Datasets

Some datasets contain series of different types (e.g. Population has both '000s counts
and a percentage change). These use `"value_format": "mixed"` and the format for each
series is resolved by Series ID lookup tables in generate_charts.py and dashboard.py.

**Current mixed-format Series ID registries:**

`PERCENT_SERIES_IDS` (displayed as "6.1%"):
- A84423050A - Unemployment rate
- A84423051C - Participation rate
- A85256565A - Underemployment rate
- A85255726K - Underutilisation rate
- A2133256J - Percentage ERP Change

`THOUSANDS_SERIES_IDS` (displayed as "61.0"):
- A84423047L - Labour force total
- A2133251W - Estimated Resident Population
- A2133252X - Natural Increase
- A2133254C - Net Overseas Migration

**When adding a new mixed-format series**, update both lookup sets in generate_charts.py
and dashboard.py to ensure consistent formatting.

### Quarterly Resampling

Monthly datasets flagged with `resample_to_quarterly: True` are automatically converted
to quarterly frequency after download. This allows direct comparison with natively
quarterly datasets (GDP, Building Activity, Population).

**Process:**
1. Download full monthly history (HISTORY_YEARS x 12 rows)
2. Apply `resample_quarterly()` using the specified method
3. Trim to last HISTORY_YEARS x 4 quarters
4. Save as CSV with quarterly DatetimeIndex

**Important - PeriodIndex handling:** readabs returns monthly data with a PeriodIndex
(e.g. Period('2024-01', 'M')) rather than a DatetimeIndex. The helper function
`ensure_datetime_index()` in download.py handles this by calling `.to_timestamp()`
before resampling. This is applied to both standard tables and the OAD merge handler.
Do not use `pd.to_datetime()` directly on readabs output - it will raise a TypeError.

### OAD Merged Output

The Overseas Arrivals & Departures dataset uses a special merge handler because the
arrivals and departures series come from different ABS tables. The handler:

1. Fetches Table 340101 (arrivals) and Table 340102 (departures) separately
2. Joins them on the date index
3. Divides both by 1,000 (converts raw counts to '000s)
4. Derives a net column: arrivals - departures
5. Resamples monthly -> quarterly (sum of movements per quarter)
6. Saves as OAD_Combined.csv with three columns

Old separate files (OAD_Table1_Arrivals.csv, OAD_Table2_Departures.csv) are no
longer generated.

### Readabs Package Limitations

**CAN Handle:**
- Standard time series tables (Table 1, Table 2, etc.)
- Monthly and quarterly frequencies
- Series ID filtering and metadata extraction

**CANNOT Handle:**
- Data Cube files (complex multi-dimensional Excel)
- ZIP archives containing multiple files
- Non-standard or supplementary formats

**Note on index types:** readabs returns a PeriodIndex for monthly data and a
DatetimeIndex for quarterly data. Always use `ensure_datetime_index()` before
any date operations to handle both cases safely.

**Red Light Datasets** (require manual scraping - not yet implemented):
- 3407.0 - Overseas Migration (Data Cube format)
- 5352.0 - International Investment Position Supplementary (ZIP format)

### Chart Styling Constants

**Colors:**
- `COLOR_PRIMARY = '#ED3144'` (Strong Red - first/primary series)
- `COLOR_SECONDARY = '#000000'` (Black - all other series)
- `COLOR_GRID = '#e0e0e0'` (Light Gray - gridlines)

**Typography:**
- Font stack: Roboto -> Montserrat -> Zalando Sans -> Reddit Sans -> sans-serif
- Title: 16pt, bold
- Subtitle: 10pt, regular
- Caption: 8pt, regular
- Axis labels: semibold
- End-of-line values: 10pt, bold

**Layout:**
- DPI: 300 (high resolution)
- Figure size: (10, 7)
- Top/right spines: hidden
- Y-axis grid: dotted lines
- Margins: top=0.83, bottom=0.18

### Windows Encoding Note

All Python files must use only ASCII characters in string literals, print statements,
and comments. The Windows terminal uses cp1252 encoding by default and cannot render
Unicode characters such as arrows (U+2192), bullets (U+2022), or em-dashes (U+2013).

Safe substitutes:
- Use `->` instead of the Unicode right arrow
- Use `|` instead of the Unicode bullet in footers
- Use `-` instead of Unicode dashes in docstrings

---

## 2. PROCESS GUIDELINES

### Adding New Datasets

**Step 1: Identify ABS Catalogue**
1. Visit abs.gov.au and find the relevant release
2. Note the catalogue number (format: ####.0)

**Step 2: Discover Table Numbers**
1. Download the latest Excel release from ABS
2. Note sheet names (e.g. "Data1" = Table 1 = "640101")

**Step 3: Find Series IDs**
1. Open the desired sheet
2. Series IDs are in column headers (format: A########X)
3. "Data Item Description" row describes each series

**Step 4: Configure in config.py**
```python
{
    "name": "Your Dataset Name",
    "cat_id": "####.0",
    "frequency": "Quarterly",    # or "Monthly"
    "tables": {
        "table_id": {
            "filename": "descriptive_name.csv",
            "display_title": "Professional Chart Title",
            "calc_type": "raw",
            "value_format": "count",   # see value_format options above
            "plot_ids": [
                "A########X",
            ]
        }
    }
}
```

For monthly datasets that should align with quarterly data, add:
```python
"resample_to_quarterly": True,
"resample_method": "last",  # or "sum" for count data
```

**Step 5: Test Download**
```bash
python download.py --cat ####.0
```
Check console for "[OK] Saved: filename.csv (N series)"

**Step 6: Verify Output**
- Open `abs_data_output/your_file.csv`
- Confirm date range and row count
- Verify column names include Series IDs in parentheses

**Step 7: Generate and Inspect Chart**
```bash
python generate_charts.py
```
- Charts appear in `abs_charts_output/`
- Verify line colors, end-of-line labels, title, subtitle, footer

### Running Regular Updates

**Using the TUI (recommended):**
```bash
python start.py
# Option 4: Full update (download + charts)
# Option 1: Download only, with frequency filter
```

**Direct CLI:**
```bash
# Download all datasets
python download.py

# Download only monthly datasets
python download.py --freq Monthly

# Download only quarterly datasets
python download.py --freq Quarterly

# Download specific catalogue
python download.py --cat 6401.0

# List available datasets without downloading
python download.py --list
```

**Update Cycles:**
- Monthly: CPI, Labour Force, Building Approvals, Overseas Migration
- Quarterly: GDP, Building Activity, Population

### Troubleshooting Common Issues

**Error: "Table not found"**
- Check table ID format (some use "640101", others "6401001")
- Verify table still exists in latest ABS release
- Download raw Excel from ABS to confirm sheet names

**Error: "Series ID missing"**
- ABS occasionally changes Series IDs between releases
- Download latest Excel and check column headers
- Update Series IDs in config.py

**TypeError: "Passing PeriodDtype data is invalid"**
- readabs returned a PeriodIndex; you used pd.to_datetime() directly
- Fix: use `ensure_datetime_index(df)` from download.py instead

**UnicodeEncodeError: 'charmap' codec can't encode character**
- A Unicode character (arrow, bullet, dash) is in a print statement or string
- Fix: replace with ASCII equivalent (-> instead of arrow, | instead of bullet)
- This affects any file run via the Windows terminal (cp1252 encoding)

**Warning: "No valid columns found to plot"**
- plot_ids in config.py don't match columns in downloaded data
- Check if Series ID format changed

**Charts appear empty or truncated**
- Data may be outside 10-year window
- Check raw CSV to confirm data exists
- Adjust HISTORY_YEARS if needed

**Font warnings in console**
- Matplotlib can't find Roboto - will fall back to sans-serif
- Non-critical, safe to ignore

### Working with the Cache

`.readabs_cache/` stores raw ABS Excel files to speed up subsequent downloads.
Clear it if you suspect stale data:
```bash
rmdir /s /q .readabs_cache   # Windows
rm -rf .readabs_cache         # Mac/Linux
```

---

## 3. QUALITY STANDARDS

### Data Validation Requirements

**Date Index:**
- Must be DatetimeIndex (not PeriodIndex) after processing
- Must be monotonic increasing (sorted chronologically)

**Row Counts (after any resampling):**
| Frequency | Expected Rows (10 years) |
|-----------|--------------------------|
| Monthly   | 120 +/- 2                |
| Quarterly | 40 +/- 1                 |
| Annual    | 10 +/- 0                 |

**Column Naming Convention:**
- Format: `Data Item Description (SERIES_ID)`
- Example: `Gross domestic product; Chain volume measures (A2304370T)`
- Exception: OAD_Combined.csv uses plain human-readable labels (no Series ID suffix)

**Data Types:**
- Index: datetime64
- Values: float64
- Allow NaN for missing observations (rare but valid)

### Chart Quality Standards

**Visual Requirements:**
- All text readable at 300 DPI
- Primary series (first) in red (#ED3144), others in black
- End-of-line labels formatted per value_format
- No overlapping labels
- Grid enhances readability without distracting

**Text Elements Required:**
1. **Title** - display_title from config (16pt bold)
2. **Subtitle** - "Latest Data: [Month Year]  |  [Frequency]" (10pt)
3. **Y-axis label** - derived from value_format (semibold)
4. **X-axis label** - "Date" (semibold)
5. **Footer** - "Data Source: Australian Bureau of Statistics  |  Chart generated via readabs" (8pt)

**File Standards:**
- Format: PNG, 300 DPI
- Naming: `Chart_[csv_filename_without_extension].png`
- Size: approximately 500-800 KB per chart

### Error Handling Expectations

**Console Output Format:**
```
Processing: CPI (Cat: 6401.0) | Freq: Monthly -> Quarterly
  [OK] Saved: CPI_Table1_All_Groups.csv (2 series)
  [OK] Saved: CPI_Table6_CPI_Means.csv (3 series)
```

**Warning Format:**
```
  [!] Warning: Could not find these IDs: ['A999999X']
  [!] Could not find Series ID 'A999999X' in CPI_Table1.csv
```

Scripts should never crash mid-process. Failed datasets print an error and
continue to the next dataset.

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

**Total Coverage:**
- 7 distinct datasets (GDP, CPI, Building, Population, Migration, Labour)
- 10 CSV files, 10 static PNG charts, 1 interactive web dashboard
- All data covers previous 10 years (configurable via HISTORY_YEARS)
- Monthly datasets resampled to quarterly for cross-dataset comparison

**Two Output Modes:**

| Task | Static Charts (generate_charts.py) | Dashboard (dashboard.py) |
|------|------------------------------------|--------------------------|
| Quick exploration | Must regenerate PNGs | Instant toggling |
| Report insertion | Direct PNG embedding | Screenshot needed |
| Multiple series comparison | Fixed in advance | Toggle any combination |
| Date range adjustment | Must edit code | Interactive slider |
| Sharing outputs | Email PNG files | Recipients need dashboard |
| Professional styling | Publication-ready | Web-focused design |

**Recommended Usage:**
- Dashboard first - Explore data, identify interesting patterns
- Static charts second - Generate PNGs of key findings for reports

---

## 4A. INTERACTIVE DASHBOARD (dashboard.py)

### Overview

The Streamlit dashboard provides a web-based interface for exploring ABS data
interactively. Unlike static PNG charts, the dashboard lets you toggle series,
adjust timeframes, and compare different indicators without editing code.

**Key Features:**
- Dataset and table selection from dropdowns
- Series toggles (show/hide individual lines)
- Date range slider
- Interactive Plotly charts (hover, zoom, pan)
- Latest values table with period-on-period changes
- Format-aware display (%, '000s, counts) matching static chart conventions
- Auto-refresh when CSV files change (no restart needed)

**Launch:**
```bash
streamlit run dashboard.py
# Opens at http://localhost:8501
# Stop with Ctrl+C
```

**Color Palette:**
- Primary: `#ED3144` (red - matches static charts)
- Additional: `#000000`, `#2563EB`, `#059669`, `#D97706`, `#7C3AED`

---

## 4B. TUI CONTROL CENTER (start.py)

The TUI provides a single interactive menu to orchestrate the entire pipeline
without needing to remember script names or arguments.

**Launch:**
```bash
python start.py
```

**Menu Options:**
- **0** - Show pipeline status (file counts, timestamps, dependency checks)
- **1** - Download data (all, monthly only, or quarterly only)
- **2** - Generate static charts
- **3** - Launch interactive dashboard
- **4** - Full update (download + charts in sequence)
- **5** - View configured datasets
- **Q** - Quit

**Built with:** `rich` library for colored output, tables, and panels.
Runs scripts via `subprocess` to capture and display live output.

---

## 4C. FUTURE ENHANCEMENTS - IMPLEMENTATION ROADMAP

The following items are planned but not yet implemented.

#### A) AI-Generated Commentary and Analysis

**Goal:** Automatically analyze trends and generate written insights for each chart.

**Approach:** Two-phase implementation:

Phase 1 - Python trend detection (calculate latest value, 1-year change, direction
of last 4 periods). Phase 2 - Pass stats to Claude API to generate 2-3 sentence
professional commentary. Output either as chart text boxes or a separate Markdown
report file.

Requires Claude API access. See earlier versions of this SKILL.md for full
implementation code template.

#### B) Manual Scrapers for Special Datasets

**Problem:** readabs cannot handle Data Cube or ZIP format ABS releases.

**Target Datasets:**
1. **3407.0 - Overseas Migration** (Data Cube .xlsx format)
2. **5352.0 - International Investment Position Supplementary** (ZIP with multiple files)

**Approach:** Use `requests` + `BeautifulSoup` to scrape the ABS download page,
find the file link, download it, and parse manually. Save output in the same CSV
format as other pipeline outputs for seamless integration with generate_charts.py
and dashboard.py.

#### C) Cross-Dataset Quarterly Comparisons

**Goal:** Multi-indicator charts combining series from different datasets on a
single chart (e.g. GDP growth vs unemployment rate vs building approvals).

Now more feasible since all monthly datasets are already resampled to quarterly,
aligning their time axes with natively quarterly datasets. The `s03_construction_cycle.py`
file demonstrates the resample + join pattern to follow.

---

## 5. USING THIS SKILL WITH CLAUDE

### When to Reference This Skill

- "Using my ABS pipeline skill, add the Retail Trade dataset (8501.0)"
- "Help me troubleshoot why Building Activity table isn't downloading"
- "Implement AI commentary as outlined in the skill roadmap"
- "Analyze the latest GDP trends using data from my pipeline"

### Claude's Analysis Capabilities

When given access to the CSV files, Claude can:

1. **Identify Trends** - direction, acceleration, cyclical patterns, structural breaks
2. **Contextualize Data** - compare to historical norms, relate to economic theory
3. **Generate Insights** - e.g. "GDP growth has slowed to 0.3% QoQ, the weakest since..."
4. **Draft Commentary** - chart captions, executive summaries, technical notes

### Workflow Examples

**Monthly Update:**
```
python start.py -> Option 1 (Monthly only) -> Option 3 (Dashboard to review)
```

**Adding a Dataset:**
```
1. Find catalogue ID and Series IDs on abs.gov.au
2. Add entry to config.py following the template above
3. python download.py --cat ####.0   (test download)
4. python generate_charts.py         (verify chart)
5. streamlit run dashboard.py        (verify dashboard)
```

**Quarterly Update:**
```
python start.py -> Option 4 (Full update)
```

---

## 6. MAINTENANCE & VERSION CONTROL

### Regular Maintenance Schedule

**Monthly:** Update monthly datasets (CPI, Labour Force, Building Approvals, Migration)

**Quarterly:** Update quarterly datasets (GDP, Building Activity, Population).
Verify Series IDs haven't changed.

**Annually:** Review dataset list relevance. Update Python packages:
```bash
pip install --upgrade readabs pandas matplotlib streamlit plotly rich
```

### Changelog

```
### 2026-02-18
- Fixed UnicodeEncodeError on Windows terminal (cp1252): replaced all Unicode
  arrows, bullets and dashes with ASCII equivalents across download.py,
  config.py, and generate_charts.py
- Fixed TypeError from readabs PeriodIndex: added ensure_datetime_index() helper
  in download.py that calls .to_timestamp() for PeriodIndex and pd.to_datetime()
  otherwise; applied in both resample_quarterly() and process_merged_oad()

### 2026-02-16
- Implemented quarterly resampling for monthly datasets (CPI, Building Approvals,
  OAD, Labour Force) via resample_to_quarterly + resample_method config flags
- Implemented OAD merge handler: fetches arrivals and departures tables separately,
  joins them, converts to '000s, derives net column, saves as OAD_Combined.csv
- Implemented value_format system: "percent", "thousands", "count", "index",
  "mixed" - controls end-of-line labels and y-axis titles in both static charts
  and the dashboard
- Added mixed-format support via PERCENT_SERIES_IDS / THOUSANDS_SERIES_IDS
  lookup tables in generate_charts.py and dashboard.py

### 2026-02-13
- Renamed all scripts from numbered prefixes to descriptive action-based names:
  s00 -> config.py, s01 -> download.py, s02 -> generate_charts.py,
  s05 -> dashboard.py, s99 -> start.py
- Added CLI arguments to download.py (--freq, --cat, --list)
- Added display_title field to all table configs
- Added calc_type field for percentage change calculations (raw, yoy, qoq, mom)
- Updated generate_charts.py to use display titles and apply transformations
- Updated all documentation to reflect new script names

### 2025-02-11
- Added interactive Streamlit dashboard (now dashboard.py)
- Set up virtual environment (venv) and requirements.txt
- Added .gitignore for version control

### 2025-02-04
- Initial pipeline: 7 datasets, Series ID filtering, static PNG charts
- Red/black styling, professional 300 DPI output
```

### Version Control with Git

**What Gets Committed:**
- All Python scripts (config.py, download.py, generate_charts.py, dashboard.py, start.py)
- Configuration files (requirements.txt, .gitignore)
- Documentation (SKILL.md, DASHBOARD_SETUP.md, Summary.md)
- Reference files (Key ABS Time Series.xlsx)

**What Gets Ignored** (regenerated from source):
- abs_data_output/ - CSV files downloaded from ABS
- abs_charts_output/ - PNG charts generated from CSVs
- venv/ - recreated from requirements.txt
- .readabs_cache/ - performance cache only
- __pycache__/ - Python bytecode

**Workflow:**
```bash
git add config.py download.py generate_charts.py dashboard.py start.py SKILL.md Summary.md
git commit -m "Description of changes"
git push origin main
```

**Recovery from Git backup:**
```bash
git clone <repository-url>
cd ABS-Project
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python download.py          # Redownload data from ABS
streamlit run dashboard.py  # Dashboard ready immediately
```

---

## 7. CONCLUSION

This pipeline transforms manual ABS data work into a three-command workflow:

```bash
python start.py                  # Interactive control center
python download.py               # Or: direct data download
streamlit run dashboard.py       # Or: direct dashboard launch
python generate_charts.py        # Or: direct chart generation
```

**Current State (February 2026):**
- 7 datasets, 10 CSV outputs, 10 static charts + interactive dashboard
- All monthly datasets resampled to quarterly for cross-dataset alignment
- Format-aware labeling (%, '000s, counts) throughout charts and dashboard
- OAD arrivals + departures merged into single file with derived net column
- Full CLI support for selective downloads
- Robust PeriodIndex handling for readabs compatibility
- ASCII-safe output for Windows terminal compatibility

**Remaining Roadmap:**
- AI-generated commentary (Claude API integration)
- Manual scrapers for Data Cube / ZIP format datasets
- Cross-dataset multi-indicator comparison charts
