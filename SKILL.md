# ABS Economic Data Pipeline - Skill Guide

**Purpose:** Enable Claude to help maintain, extend, and analyze an automated pipeline for downloading, processing, and visualizing Australian Bureau of Statistics (ABS) economic indicators.

**Primary Focus:** Pipeline automation and maintenance  
**Secondary Focus:** AI-driven data analysis and commentary generation

---

## 1. CONSTRAINTS & PARAMETERS

### File Structure
```
C:\Users\angus\Sync\Claude Code\ABS-Project\
├── s00_readabs_datalist.py           # Configuration registry
├── s00_readabs_datalist-AllTables.py # Alternative: Download all tables (not filtered)
├── s01_readabs_datadownload.py       # Data downloader
├── s02_readabs_plotting.py           # Static chart generator (PNG)
├── s05_dashboard.py                  # Interactive Streamlit web dashboard
├── Key ABS Time Series.xlsx          # Reference: Original dataset list
├── Summary.md                        # Original project documentation
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
- **Standard library:** os, sys, logging, io, warnings, contextlib

**Interactive Dashboard (s05):**
- **streamlit** - Web dashboard framework
- **plotly** - Interactive charting library

**Installation:**
```bash
# Option 1: Using pip (system-wide)
pip install readabs pandas matplotlib streamlit plotly --break-system-packages

# Option 2: Using virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Full dependency list available in:** `requirements.txt`

### Virtual Environment (venv)

**Purpose:** Isolates project dependencies from system Python installation

**Activation:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

**Deactivation:**
```bash
deactivate
```

**When activated:**
- Command prompt shows `(venv)` prefix
- `pip install` affects only this project
- `python` command uses venv's Python interpreter

**Best Practice:** Always activate venv before running scripts or installing packages

### Core Configuration (s00_readabs_datalist.py)

**Global Parameters:**
```python
HISTORY_YEARS = 10           # Data retention period
OUTPUT_DIRECTORY = "abs_data_output"
```

**Dataset Dictionary Structure:**
```python
{
    "name": "National Accounts (GDP)",
    "cat_id": "5206.0",              # ABS Catalogue ID
    "frequency": "Quarterly",         # or "Monthly", "Annual"
    "tables": {
        "5206001_Key_Aggregates": {
            "filename": "GDP_Key_Aggregates_sa.csv",
            "plot_ids": [
                "A2304370T",         # Series ID for GDP
                "A2304372W",         # Series ID for GDP per capita
                # ... additional series
            ]
        }
    }
}
```

**Frequency-Based Row Calculation:**
- Monthly: HISTORY_YEARS × 12 rows
- Quarterly: HISTORY_YEARS × 4 rows  
- Half-yearly: HISTORY_YEARS × 2 rows
- Annual: HISTORY_YEARS × 1 row

### Readabs Package Limitations

**CAN Handle:**
- Standard time series tables (Table 1, Table 2, etc.)
- Both monthly and quarterly frequencies
- Series ID filtering and metadata extraction

**CANNOT Handle:**
- Data Cube files (complex multi-dimensional Excel files)
- ZIP archives containing multiple files
- Non-standard formats or supplementary datasets

**Red Light Datasets** (require manual scraping):
- 3407.0 - Overseas Migration (Data Cube format)
- 5352.0 - International Investment Position Supplementary (ZIP format)

### Chart Styling Constants

**Colors:**
- `COLOR_PRIMARY = '#ED3144'` (Strong Red - primary series)
- `COLOR_SECONDARY = '#000000'` (Black - secondary series)
- `COLOR_GRID = '#e0e0e0'` (Light Gray - gridlines)

**Typography:**
- Font stack: Roboto → Montserrat → Zalando Sans → Reddit Sans → sans-serif
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

---

## 2. PROCESS GUIDELINES

### Adding New Datasets

**Step 1: Identify ABS Catalogue**
1. Visit abs.gov.au
2. Find the relevant release (e.g., "6401.0 - Consumer Price Index")
3. Note the catalogue number (format: ####.0)

**Step 2: Discover Table Numbers**
1. Download the latest Excel release from ABS
2. Open file and note sheet names (e.g., "Data1", "Data6")
3. Sheet names typically map to table numbers:
   - "Data1" = Table 1 = "640101"
   - "Data6" = Table 6 = "640106"

**Step 3: Find Series IDs**
1. Open the desired table/sheet
2. Series IDs are in the column headers (format: A########X)
3. Look for the "Data Item Description" to understand what each series represents
4. Note the Series IDs you want to track

**Step 4: Configure in s00**
```python
# Add to ABS_DATASETS list in s00_readabs_datalist.py
{
    "name": "Your Dataset Name",
    "cat_id": "####.0",
    "frequency": "Monthly",  # or "Quarterly"
    "tables": {
        "table_id": {
            "filename": "descriptive_name.csv",
            "plot_ids": [
                "A########X",  # First series ID
                "A########X",  # Second series ID
                # Add more as needed
            ]
        }
    }
}
```

**Step 5: Test Download**
```bash
python s01_readabs_datadownload.py
```
- Check console for "Saved: filename.csv (N series)"
- Verify no errors for your new dataset

**Step 6: Verify Output**
1. Open `abs_data_output/your_file.csv`
2. Confirm date range (should be 10 years)
3. Check row count matches frequency:
   - Monthly: ~120 rows
   - Quarterly: ~40 rows
4. Verify column names include Series IDs in parentheses

**Step 7: Generate Charts**
```bash
python s02_readabs_plotting.py
```
- Charts appear in `abs_charts_output/`
- Filename format: `Chart_descriptive_name.png`

**Step 8: Inspect Chart**
- Verify line colors (first series red, others black)
- Check end-of-line labels appear correctly
- Confirm title and subtitle are readable
- Ensure footer attribution is present

### Running Regular Updates

**Monthly Update Cycle** (for monthly datasets):
```bash
cd "C:\Users\angus\Sync\Claude Code\ABS-Project"
python s01_readabs_datadownload.py  # Downloads new data
python s02_readabs_plotting.py      # Regenerates all charts
```

**Quarterly Update Cycle** (for quarterly datasets):
- GDP: First week of March, June, September, December
- Building Activity: Mid-quarter releases
- Population: Mid-quarter releases

**Validation Checklist:**
1. ✓ New data appears in CSV files
2. ✓ Chart subtitle shows updated "Latest Data" date
3. ✓ No error messages in console
4. ✓ All expected charts regenerated
5. ✓ End-of-line values updated

### Troubleshooting Common Issues

**Error: "Table not found"**
- Check table ID format (some use "640101", others "6401001")
- Verify table still exists in latest ABS release
- Try downloading raw Excel to confirm table name

**Error: "Series ID missing" or "Could not find ID"**
- ABS occasionally changes Series IDs between releases
- Download latest Excel and check column headers
- Update Series IDs in s00 configuration

**Warning: "No valid columns found to plot"**
- plot_ids in s00 don't match any columns in downloaded data
- Check if Series ID format changed
- Verify data was actually downloaded

**Charts appear empty or truncated**
- Data may be outside 10-year window
- Check raw CSV to confirm data exists
- Adjust HISTORY_YEARS if needed

**Font warnings in console**
- Matplotlib can't find Roboto font
- Charts will use fallback (Montserrat or Arial)
- Non-critical warning, safe to ignore

### Working with the Cache

**Cache Behavior:**
- `.readabs_cache/` stores raw ABS Excel files
- Speeds up subsequent downloads (uses cached version if recent)
- Automatically refreshed when new ABS data released

**Clearing Cache:**
```bash
# Delete cache folder to force fresh downloads
rm -rf .readabs_cache
```
Only necessary if suspecting stale data or corrupted downloads.

---

## 3. QUALITY STANDARDS

### Data Validation Requirements

**Date Index:**
- Must be datetime format
- Must be monotonic increasing (sorted chronologically)
- No gaps in time series (within expected frequency)

**Row Counts:**
| Frequency | Expected Rows (10 years) |
|-----------|--------------------------|
| Monthly   | 120 ± 2                  |
| Quarterly | 40 ± 1                   |
| Annual    | 10 ± 0                   |

**Column Naming Convention:**
- Format: `Data Item Description (SERIES_ID)`
- Example: `Gross domestic product; Chain volume measures (A2304370T)`
- Series ID must be in parentheses at end

**Data Types:**
- Index: datetime64
- Values: float64
- Allow NaN for missing observations (rare but valid)

### Chart Quality Standards

**Visual Requirements:**
- ✓ All text must be readable at 300 DPI
- ✓ Primary series (first) in red, others in black
- ✓ End-of-line labels with comma-separated thousands
- ✓ No overlapping labels or text collision
- ✓ Grid enhances readability, doesn't distract

**Text Elements Required:**
1. **Title** - Dataset name + table description (16pt bold)
2. **Subtitle** - "Latest Data: [Month Year]" (10pt)
3. **Y-axis label** - "Value" or specific unit (semibold)
4. **X-axis label** - "Date" (semibold)
5. **Footer** - "Data Source: Australian Bureau of Statistics • Chart generated via readabs" (8pt)

**File Standards:**
- Format: PNG
- Resolution: 300 DPI
- Naming: `Chart_[descriptive_name].png`
- Size: ~500-800 KB per chart

### Error Handling Expectations

**Script Execution:**
- Should never crash mid-process
- Failed datasets should print error but continue to next
- All warnings/errors should be descriptive

**Console Output Format:**
```
Processing: CPI (Cat: 6401.0) | Freq: Monthly
  [✓] Saved: CPI_Table1_All_Groups.csv (2 series)
  [✓] Saved: CPI_Table6_CPI_Means.csv (3 series)
```

**Warning Format:**
```
  [!] Warning: Could not find these IDs: ['A999999X']
  [!] Could not find Series ID 'A999999X' in CPI_Table1.csv
```

**Validation Steps:**
1. Check CSV files exist in output directory
2. Verify row counts match expectations
3. Confirm charts generated without errors
4. Spot-check 2-3 charts for visual quality
5. Review console for any [!] warnings

---

## 4. OUTPUT EXPECTATIONS

### Current Pipeline Outputs

**Two Output Modes:**

**1. Static Charts (s02 - Traditional workflow)**
- PNG files in `abs_charts_output/`
- 300 DPI, professional styling
- Red/black color scheme
- Suitable for reports, presentations, publications

**2. Interactive Dashboard (s05 - Exploration workflow)**
- Web-based interface at `http://localhost:8501`
- Toggle datasets and series on/off
- Adjust date ranges with slider
- Interactive Plotly charts with hover tooltips and zoom
- Latest values table with period-on-period changes
- Run with: `streamlit run s05_dashboard.py`

**CSV Data Files** (in `abs_data_output/`):
- GDP_Key_Aggregates_sa.csv (6 series)
- CPI_Table1_All_Groups.csv (2 series)
- CPI_Table6_CPI_Means.csv (3 series)
- Building_Activity_Table33_Starts.csv (3 series)
- Building_Activity_Table37_Completions.csv (3 series)
- Building_Approvals_Table6_Dwellings_sa.csv (3 series)
- Population_Table1_ERP.csv (4 series)
- OAD_Table1_Arrivals.csv (1 series)
- OAD_Table2_Departures.csv (1 series)
- LabourForce_Table1_Unemployment_sa.csv (3 series)
- LabourForce_Table22_Underemployment_sa.csv (2 series)

**Static Chart Files** (in `abs_charts_output/`):
- One PNG per CSV file above
- Professional styling matching employer requirements
- Auto-labeled with latest data point values

**Total Coverage:**
- 7 distinct datasets (GDP, CPI, Building, Population, Migration, Labour)
- 11 CSV files with filtered, clean data
- 11 static PNG charts + 1 interactive web dashboard
- All data covers previous 10 years (configurable)

**Workflow Comparison:**

| Task | Static Charts (s02) | Dashboard (s05) |
|------|---------------------|-----------------|
| Quick exploration | ❌ Must regenerate PNGs | ✅ Instant toggling |
| Report insertion | ✅ Direct PNG embedding | ❌ Screenshot needed |
| Multiple series comparison | ❌ Fixed in advance | ✅ Toggle any combination |
| Date range adjustment | ❌ Must edit code | ✅ Interactive slider |
| Sharing outputs | ✅ Email PNG files | ❌ Recipients need dashboard |
| Professional styling | ✅ Publication-ready | ⚠️ Web-focused design |

**Recommended Usage:**
- **Dashboard first** - Explore data, identify interesting patterns
- **Static charts second** - Generate PNGs of key findings for reports

---

## 4A. INTERACTIVE DASHBOARD (s05_dashboard.py)

### Overview

The Streamlit dashboard provides a web-based interface for exploring your ABS data interactively. Unlike static PNG charts that require regeneration for every change, the dashboard lets you toggle series, adjust timeframes, and compare different indicators instantly.

**Key Features:**
- **Dataset selection** - Choose from any configured ABS dataset
- **Series toggles** - Show/hide individual time series with checkboxes
- **Date range slider** - Dynamically adjust the time window
- **Interactive charts** - Hover for precise values, click-drag to zoom, double-click to reset
- **Latest values table** - Current data points with period-on-period changes
- **Auto-refresh** - Updates when CSV files change (no restart needed)

### First-Time Setup

**1. Install Dependencies (one-time):**
```bash
# If using virtual environment (recommended):
venv\Scripts\activate  # Windows
pip install streamlit plotly

# If using system Python:
pip install streamlit plotly --break-system-packages
```

**2. Verify Data Exists:**
Dashboard requires CSV files in `abs_data_output/`. If folder is empty:
```bash
python s01_readabs_datadownload.py
```

**3. Launch Dashboard:**
```bash
streamlit run s05_dashboard.py
```

Browser opens automatically at `http://localhost:8501`

**To stop:** Press `Ctrl+C` in terminal

### Dashboard Interface Guide

**Left Sidebar (Controls):**
1. **Dataset dropdown** - Select ABS release (GDP, CPI, Labour Force, etc.)
2. **Table dropdown** - Appears when dataset has multiple tables
3. **Series checkboxes** - Toggle individual time series on/off
4. **Date range slider** - Drag endpoints to adjust time window

**Main Panel:**
1. **Interactive chart** - Plotly visualization with hover tooltips
   - Hover: See exact values for all series at that date
   - Click-drag: Zoom into specific region
   - Double-click: Reset zoom
   - Click legend: Hide/show specific series
2. **Latest Values table** - Shows most recent data point, previous value, change, and % change

**Chart Features:**
- Primary series (first selected) in red (#ED3144)
- Additional series in distinct colors
- Grid lines for readability
- Responsive layout (fills window width)

### Common Workflows

**Workflow 1: Exploring a New Dataset**
```
1. Select dataset from dropdown (e.g., "CPI")
2. All series toggle on by default - chart shows everything
3. Uncheck series that aren't relevant
4. Adjust date range slider to focus on recent period
5. Hover over chart to identify peaks/troughs
6. Review Latest Values table for current status
```

**Workflow 2: Comparing Related Indicators**
```
1. Select dataset with multiple related series (e.g., Labour Force)
2. Toggle on: Unemployment rate, Participation rate
3. Use date slider to focus on last 2-3 years
4. Observe correlation/divergence in chart
5. Check Latest Values for quantitative summary
```

**Workflow 3: Preparing for Report Writing**
```
1. Use dashboard to explore all datasets quickly
2. Identify 2-3 series with interesting trends
3. Screenshot or note the key findings
4. Exit dashboard, run s02 to generate publication-quality PNGs
5. Insert PNGs into Word document/PowerPoint
```

**Workflow 4: Monthly Data Updates**
```
1. Run: python s01_readabs_datadownload.py
2. Refresh dashboard in browser (or it auto-detects)
3. Latest Values table shows new data
4. Review chart to see if patterns changed
5. Decide if worth generating new static charts
```

### Troubleshooting

**"No data found in 'abs_data_output/'"**
- Folder is empty or doesn't exist
- Solution: Run `python s01_readabs_datadownload.py` first

**"ModuleNotFoundError: No module named 'streamlit'"**
- Package installed in different Python environment
- Solution: Activate venv or reinstall in current environment

**Browser doesn't open automatically**
- Normal on some systems
- Solution: Manually open `http://localhost:8501`

**"Port 8501 already in use"**
- Another Streamlit instance running
- Solution: Stop other instance, or use different port:
  ```bash
  streamlit run s05_dashboard.py --server.port 8502
  ```

**Dashboard shows old data**
- CSV files haven't been updated
- Solution: Run s01 download script, then refresh browser

**Chart appears empty/blank**
- All series unchecked in sidebar
- Date range slider excludes all data
- Solution: Toggle series on, or reset date range to full span

### Dashboard vs Static Charts Decision Tree

```
Need to explore data interactively? 
  → Use Dashboard (s05)

Need to insert charts in Word/PowerPoint?
  → Use Static Charts (s02)

Need to share findings with others?
  → If recipient has Python/Streamlit: Share dashboard
  → Otherwise: Static PNGs

Working on monthly update cycle?
  → Dashboard for quick review
  → Static charts only for changed/interesting series

Preparing formal publication?
  → Dashboard for exploration
  → Static charts for final output (higher quality, better control)
```

### Technical Details

**How it Works:**
1. Imports `s00_readabs_datalist.py` to get dataset grouping and names
2. Scans `abs_data_output/` for CSV files
3. Loads selected CSV into pandas DataFrame
4. Filters by date range from slider
5. Plots selected series using Plotly
6. Calculates latest values and changes

**Color Palette:**
- Primary: `#ED3144` (red - matches your static charts)
- Secondary: `#000000` (black)
- Additional: `#2563EB`, `#059669`, `#D97706`, `#7C3AED`

**Performance:**
- Handles 10+ years of monthly data smoothly
- Chart renders in <1 second on typical hardware
- No database required - reads CSV files directly

**Customization:**
To modify styling or behavior, edit `s05_dashboard.py`:
- Line 12: COLORS array (add/change colors)
- Line 126-142: Plotly layout settings
- Line 157-175: Latest Values table formatting

---

## 4B. FUTURE ENHANCEMENTS - IMPLEMENTATION ROADMAP

#### A) Quarter-on-Quarter (QoQ) Percentage Calculations

**Current State:** Charts display raw index values or absolute numbers  
**Goal:** Add percentage change calculations for meaningful trend analysis

**Implementation Approach:**

**Option 1 - Modify s01 (calculate during download):**
```python
# After filtering date range in s01_readabs_datadownload.py:
filtered_df = df.tail(rows_to_keep)

# Add QoQ calculations for specified series
if 'calc_type' in value and value['calc_type'] == 'qoq':
    for col in filtered_df.columns:
        if 'Index' in col or 'GDP' in col or 'CPI' in col:
            # For quarterly data: pct_change(1)
            # For monthly data converting to QoQ: pct_change(3)
            qoq_col_name = f"{col} - QoQ % Change"
            filtered_df[qoq_col_name] = filtered_df[col].pct_change(1) * 100
```

**Option 2 - Create s03 (dedicated calculation script):**
```python
# New file: s03_readabs_calculations.py
import pandas as pd
import os
from s00_readabs_datalist import ABS_DATASETS, OUTPUT_DIRECTORY

CALC_CONFIGS = {
    "GDP_Key_Aggregates_sa.csv": {
        "series": ["A2304370T", "A2304372W"],  # GDP and GDP per capita
        "calc": "qoq",
        "periods": 1  # 1 quarter back
    },
    "CPI_Table6_CPI_Means.csv": {
        "series": ["A130607784C", "A130400383T"],  # All groups, Trimmed mean
        "calc": "qoq",
        "periods": 1
    }
}

for csv_file, config in CALC_CONFIGS.items():
    df = pd.read_csv(os.path.join(OUTPUT_DIRECTORY, csv_file), index_col=0)
    df.index = pd.to_datetime(df.index)
    
    for col in df.columns:
        # Check if this series needs calculation
        series_id = col.split('(')[-1].strip(')')
        if series_id in config['series']:
            new_col = f"{col} - QoQ % Change"
            df[new_col] = df[col].pct_change(config['periods']) * 100
    
    # Save augmented file
    df.to_csv(os.path.join(OUTPUT_DIRECTORY, csv_file))
```

**Update s00 configuration:**
```python
"5206001_Key_Aggregates": {
    "filename": "GDP_Key_Aggregates_sa.csv",
    "plot_ids": ["A2304370T", "A2304372W"],
    "calc_type": "qoq",  # NEW: Trigger calculation
    "plot_calc": True     # NEW: Plot the % change instead of raw
}
```

**Update s02 plotting logic:**
```python
# In create_abs_chart(), check if calculated columns exist
if 'plot_calc' in config and config['plot_calc']:
    # Look for " - QoQ % Change" columns
    calc_cols = [c for c in df.columns if "QoQ % Change" in c]
    if calc_cols:
        cols_to_plot = calc_cols
```

#### B) Command-Line Arguments (argparse)

**Goal:** Enable selective pipeline runs without editing code

**Implementation in s01_readabs_datadownload.py:**
```python
import argparse

# Add after imports, before main execution
def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Download ABS economic data with optional filters'
    )
    
    parser.add_argument(
        '--freq',
        choices=['monthly', 'quarterly', 'annual'],
        help='Only download datasets of this frequency'
    )
    
    parser.add_argument(
        '--dataset',
        nargs='+',
        help='Only download specific datasets by name (e.g., "GDP" "CPI")'
    )
    
    parser.add_argument(
        '--years',
        type=int,
        default=HISTORY_YEARS,
        help=f'Override history years (default: {HISTORY_YEARS})'
    )
    
    parser.add_argument(
        '--cat',
        nargs='+',
        help='Only download specific catalogue IDs (e.g., "5206.0" "6401.0")'
    )
    
    return parser.parse_args()

# In main block:
if __name__ == "__main__":
    args = parse_arguments()
    
    # Override HISTORY_YEARS if specified
    years_to_use = args.years if args.years else HISTORY_YEARS
    
    print(f"--- ABS BATCH DOWNLOAD STARTED (History: {years_to_use} Years) ---")
    
    for item in ABS_DATASETS:
        # Filter by frequency
        if args.freq and item['frequency'].lower() != args.freq.lower():
            continue
        
        # Filter by dataset name
        if args.dataset and item['name'] not in args.dataset:
            continue
        
        # Filter by catalogue ID
        if args.cat and item['cat_id'] not in args.cat:
            continue
        
        fetch_and_save_dataset(item, years_to_use)
```

**Usage Examples:**
```bash
# Update only monthly datasets
python s01_readabs_datadownload.py --freq monthly

# Update only GDP and CPI
python s01_readabs_datadownload.py --dataset "National Accounts (GDP)" "CPI"

# Update with 15 years of history instead of 10
python s01_readabs_datadownload.py --years 15

# Combine filters: quarterly datasets from last 5 years
python s01_readabs_datadownload.py --freq quarterly --years 5

# Update specific catalogue IDs
python s01_readabs_datadownload.py --cat "5206.0" "6401.0"
```

#### C) AI-Generated Commentary and Analysis

**Goal:** Automatically analyze trends and generate written insights for each chart

**Implementation Approach:**

**Phase 1 - Trend Detection (Python):**
```python
# Add to s02_readabs_plotting.py or new s04_analysis.py
def analyze_series(df, col_name):
    """Generate basic statistics and trend description"""
    series = df[col_name].dropna()
    
    # Calculate key metrics
    latest = series.iloc[-1]
    one_year_ago = series.iloc[-4] if len(series) >= 4 else series.iloc[0]  # Quarterly
    change_1y = ((latest - one_year_ago) / one_year_ago) * 100
    
    peak = series.max()
    trough = series.min()
    
    # Determine trend
    recent_trend = series.tail(4)  # Last 4 quarters
    if recent_trend.is_monotonic_increasing:
        trend = "increasing"
    elif recent_trend.is_monotonic_decreasing:
        trend = "decreasing"
    else:
        trend = "fluctuating"
    
    return {
        "latest": latest,
        "change_1y": change_1y,
        "peak": peak,
        "trough": trough,
        "trend": trend
    }
```

**Phase 2 - Claude Integration (AI Commentary):**
```python
# This would require Claude API access or running within Claude Desktop
def generate_commentary(series_name, stats, df):
    """Use Claude to generate natural language commentary"""
    
    prompt = f"""Based on this economic data, write 2-3 sentences of analysis:

Series: {series_name}
Latest Value: {stats['latest']:.1f}
1-Year Change: {stats['change_1y']:.1f}%
Recent Trend: {trend}
Peak: {stats['peak']:.1f}
Trough: {stats['trough']:.1f}

Context: This is Australian economic data from the ABS.
Tone: Professional but accessible, suitable for economic reporting.
Focus: What does this tell us about the economy?"""
    
    # Call Claude API or use desktop integration
    commentary = call_claude_api(prompt)
    return commentary
```

**Phase 3 - Add to Charts:**
```python
# In create_abs_chart() function:
stats = analyze_series(df, columns_to_plot[0])
commentary = generate_commentary(series_name, stats, df)

# Add text box to chart
textbox_text = f"Analysis: {commentary}"
ax.text(0.02, 0.98, textbox_text, 
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
```

**Alternative - Markdown Report:**
```python
# Generate separate analysis report
with open('abs_analysis_report.md', 'w') as f:
    f.write("# ABS Economic Indicators Analysis\n\n")
    f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d')}\n\n")
    
    for dataset, commentary in all_commentaries.items():
        f.write(f"## {dataset}\n\n")
        f.write(f"{commentary}\n\n")
        f.write(f"![Chart](abs_charts_output/Chart_{dataset}.png)\n\n")
```

#### D) Manual Scrapers for Special Datasets

**Problem:** Some ABS releases use non-standard formats that readabs can't handle

**Target Datasets:**
1. **3407.0 - Overseas Migration** (Data Cube format)
2. **5352.0 - International Investment Position Supplementary** (ZIP with multiple files)

**Implementation Template:**
```python
# New file: s01b_manual_scrapers.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import zipfile
import io

def scrape_migration_datacube():
    """Manual scraper for 3407.0 Overseas Migration"""
    
    # ABS download page
    url = "https://www.abs.gov.au/statistics/people/population/overseas-migration/latest-release"
    
    # Find download link for data cube
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find Excel file link (usually contains "Data Cubes")
    download_link = soup.find('a', href=lambda x: x and 'DataCube' in x and '.xlsx' in x)
    
    if download_link:
        excel_url = download_link['href']
        if not excel_url.startswith('http'):
            excel_url = 'https://www.abs.gov.au' + excel_url
        
        # Download and parse
        df = pd.read_excel(excel_url, sheet_name='Table 1', skiprows=3)
        
        # Custom processing for this specific format
        # ... extract relevant columns, set date index, etc.
        
        return df

def scrape_iip_supplementary():
    """Manual scraper for 5352.0 IIP Supplementary (ZIP format)"""
    
    url = "https://www.abs.gov.au/statistics/economy/international-trade/international-investment-position-australia-supplementary-statistics/latest-release"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find ZIP file link
    zip_link = soup.find('a', href=lambda x: x and '.zip' in x)
    
    if zip_link:
        zip_url = zip_link['href']
        if not zip_url.startswith('http'):
            zip_url = 'https://www.abs.gov.au' + zip_url
        
        # Download ZIP
        zip_response = requests.get(zip_url)
        
        # Extract specific Excel file from ZIP
        with zipfile.ZipFile(io.BytesIO(zip_response.content)) as z:
            # Find relevant file (usually contains "Table" in name)
            excel_files = [f for f in z.namelist() if f.endswith('.xlsx')]
            
            if excel_files:
                with z.open(excel_files[0]) as excel_file:
                    df = pd.read_excel(excel_file, sheet_name=0)
                    # Custom processing...
                    return df
```

**Integration with Main Pipeline:**
```python
# In s01, check for "manual_scraper" flag:
if 'manual_scraper' in dataset:
    df = dataset['manual_scraper']()  # Call custom function
    # Save as usual
```

#### E) Custom Chart Titles

**Current:** Titles auto-generated from filenames  
**Goal:** Professional, publication-ready titles

**Implementation in s00:**
```python
{
    "name": "National Accounts (GDP)",
    "cat_id": "5206.0",
    "frequency": "Quarterly",
    "tables": {
        "5206001_Key_Aggregates": {
            "filename": "GDP_Key_Aggregates_sa.csv",
            "plot_ids": ["A2304370T", "A2304372W"],
            "display_title": "Australian GDP Growth",  # NEW
            "subtitle_template": "Chain volume measures, seasonally adjusted"  # NEW
        }
    }
}
```

**Update s02 to use custom titles:**
```python
# In plotting loop:
if 'display_title' in value:
    title = value['display_title']
else:
    title = f"{dataset_name}: {csv_filename.replace('.csv', '').replace('_', ' ')}"

if 'subtitle_template' in value:
    subtitle = f"{value['subtitle_template']} | Latest: {latest_date_str}"
else:
    subtitle = f"Latest Data: {latest_date_str}"
```

#### F) Cross-Dataset Quarterly Comparisons

**Goal:** Compare metrics from different datasets on unified quarterly basis

**Example Use Case:** Compare GDP growth vs unemployment rate vs building approvals

**Implementation (see s03_construction_cycle.py as template):**
```python
# New file: s04_cross_dataset_analysis.py
import pandas as pd
import matplotlib.pyplot as plt

# Load monthly data
approvals = pd.read_csv('abs_data_output/Building_Approvals_Table6.csv', 
                        index_col=0, parse_dates=True)

# Convert monthly to quarterly using resample
approvals_quarterly = approvals.resample('Q').sum()

# Load quarterly data
gdp = pd.read_csv('abs_data_output/GDP_Key_Aggregates_sa.csv',
                  index_col=0, parse_dates=True)

# Now both are quarterly - can compare directly
fig, ax = plt.subplots()
ax.plot(gdp.index, gdp['GDP_series'], label='GDP')
ax.plot(approvals_quarterly.index, approvals_quarterly['Approvals'], 
        label='Building Approvals (Quarterly Sum)')
ax.legend()
```

**Normalization for Different Scales:**
```python
# When comparing series with very different magnitudes
def normalize_series(series):
    """Scale to 0-100 range for comparison"""
    return ((series - series.min()) / (series.max() - series.min())) * 100

gdp_norm = normalize_series(gdp['GDP_series'])
approvals_norm = normalize_series(approvals_quarterly['Approvals'])

# Now can plot on same axis
ax.plot(gdp.index, gdp_norm, label='GDP (normalized)')
ax.plot(approvals_quarterly.index, approvals_norm, label='Approvals (normalized)')
```

---

## 5. USING THIS SKILL WITH CLAUDE

### When to Reference This Skill

**Maintenance Tasks:**
- "Using my ABS pipeline skill, update the GDP dataset configuration"
- "Check my pipeline outputs against the quality standards"
- "Help me troubleshoot why Building Activity table isn't downloading"

**Extension Tasks:**
- "Following the ABS skill guide, add the Retail Trade dataset (8501.0)"
- "Implement QoQ calculations as outlined in the skill roadmap"
- "Set up argparse CLI as described in the future enhancements"

**Analysis Tasks:**
- "Analyze the latest GDP trends using data from my pipeline"
- "Compare CPI inflation across the different measures in my data"
- "Generate commentary for the labour force charts"

### Claude's Analysis Capabilities

When analyzing your ABS data, Claude can:

1. **Identify Trends**
   - Directional movement (rising/falling)
   - Acceleration or deceleration
   - Cyclical patterns
   - Structural breaks

2. **Contextualize Data**
   - Compare to historical norms
   - Relate to economic theory
   - Connect multiple indicators
   - Identify leading/lagging relationships

3. **Generate Insights**
   - "GDP growth has slowed to 0.3% QoQ, the weakest result since..."
   - "Building approvals are 15% below their 10-year average, suggesting..."
   - "The trimmed mean CPI is now tracking above the headline rate, indicating..."

4. **Draft Commentary**
   - Chart captions (2-3 sentences)
   - Executive summaries
   - Technical notes
   - Publication-ready analysis

### Workflow Examples

**Example 1: Monthly Update with Dashboard Exploration**
```
User: "It's the first Friday of the month - help me update CPI and Labour Force data"

Claude: 
1. Activates venv and runs s01 with --freq monthly flag
2. Verifies new data downloaded
3. Suggests launching dashboard: "streamlit run s05_dashboard.py"
4. Guides user through dashboard to review latest CPI and unemployment figures
5. If interesting patterns found, runs s02 to generate static PNGs for report
6. Drafts 2-paragraph summary of key changes based on dashboard observations
```

**Example 2: Adding New Dataset**
```
User: "I want to add Retail Trade (8501.0) to track consumer spending"

Claude:
1. Guides through finding table numbers and Series IDs
2. Provides formatted config block for s00
3. Tests the download
4. Verifies chart generation (both static and dashboard)
5. Suggests related indicators (consumer confidence, household income)
```

**Example 3: Deep Analysis Using Both Outputs**
```
User: "Analyze the relationship between building approvals and completions"

Claude:
1. Suggests opening dashboard to explore visually first
2. Guides user to toggle both series on, adjust date range
3. Loads both datasets from abs_data_output/ for quantitative analysis
4. Converts approvals (monthly) to quarterly to match completions
5. Calculates lag correlation
6. Generates comparative static chart for report insertion
7. Explains typical lag period and what current gap indicates
```

**Example 4: Dashboard-First Workflow**
```
User: "What's interesting in the latest economic data?"

Claude:
1. Launches dashboard
2. Systematically reviews each dataset
3. Identifies 2-3 notable trends (e.g., CPI acceleration, unemployment decline)
4. Screenshots key dashboard charts
5. Generates static PNGs of those specific series
6. Drafts commentary for economic briefing
```

---

## 6. MAINTENANCE & VERSION CONTROL

### Regular Maintenance Schedule

**Monthly:**
- Update monthly datasets (CPI, Labour Force, Building Approvals, Migration)
- Review chart outputs for anomalies
- Check ABS website for methodology changes

**Quarterly:**
- Update quarterly datasets (GDP, Building Activity, Population)
- Verify Series IDs haven't changed
- Clear cache if suspecting stale data

**Annually:**
- Review full dataset list - are all still relevant?
- Check for new ABS releases to add
- Update Python packages (`pip install --upgrade readabs pandas matplotlib`)

### Change Log Template

When modifying the pipeline, document changes:

```markdown
## CHANGELOG

### 2025-02-11
- Added s05_dashboard.py - Interactive Streamlit web interface
- Created DASHBOARD_SETUP.md - Installation and usage guide
- Implemented requirements.txt for dependency management
- Set up Python virtual environment (venv)
- Added .gitignore for proper version control
- Dashboard features: toggle series, date slider, interactive Plotly charts, latest values table

### 2025-02-04
- Initial skill documentation created (SKILL.md)
- Pipeline covers 7 core datasets (GDP, CPI, Building, Population, Labour, Migration)
- All using Series ID filtering for clean outputs
- Static PNG chart generation with red/black styling

### [Future Date]
- Added QoQ calculations to GDP and CPI (s03 or s04)
- Implemented argparse CLI in s01
- [etc.]
```

### Version Control with Git

**Current .gitignore Configuration:**
```
# Virtual environment
venv/
.env

# Python cache
__pycache__/
*.pyc

# Generated outputs (can be regenerated)
abs_data_output/
abs_charts_output/
.readabs_cache/

# System files
.DS_Store
```

**What Gets Committed:**
- ✅ All Python scripts (s00, s01, s02, s05)
- ✅ Configuration files (requirements.txt, .gitignore)
- ✅ Documentation (SKILL.md, DASHBOARD_SETUP.md, Summary.md)
- ✅ Reference files (Key ABS Time Series.xlsx)

**What Gets Ignored:**
- ❌ CSV data files (regenerated from ABS on demand)
- ❌ PNG charts (regenerated from CSVs)
- ❌ Virtual environment (each machine creates its own)
- ❌ Download cache (just a performance optimization)
- ❌ Python bytecode (automatically recreated)

**Rationale:** 
Code and configuration are version-controlled. Data and outputs are regenerated from source, so excluding them keeps the repository clean and small.

**Recommended Git Workflow:**
```bash
# Initial setup (first time only)
git init
git add .
git commit -m "Initial commit: ABS data pipeline with dashboard"

# After making changes
git add s05_dashboard.py SKILL.md  # Stage specific files
git commit -m "Update dashboard to include period-on-period changes"
git push origin main

# Before major changes
git checkout -b feature-qoq-calculations  # Work in branch
# ... make changes ...
git commit -m "Add QoQ calculation feature"
git checkout main
git merge feature-qoq-calculations
```

### Backup Strategy

**Critical Files to Backup:**
- `s00_readabs_datalist.py` - Contains all dataset configuration
- `s01_readabs_datadownload.py` - Core download logic
- `s02_readabs_plotting.py` - Static chart generation
- `s05_dashboard.py` - Interactive dashboard application
- `requirements.txt` - Dependency list for reproducibility
- `SKILL.md` - This documentation
- `DASHBOARD_SETUP.md` - Dashboard setup instructions
- `.gitignore` - Version control configuration

**Can Regenerate:**
- `abs_data_output/` - Downloadable from ABS anytime
- `abs_charts_output/` - Regenerated from CSVs via s02
- `.readabs_cache/` - Just a performance optimization
- `venv/` - Recreated from requirements.txt
- `__pycache__/` - Automatically recreated by Python

**Recommended:**
- Use Git for version control (files already configured in .gitignore)
- Commit after each successful enhancement
- Tag releases (e.g., v1.0-baseline, v1.1-dashboard, v1.2-qoq-calcs)
- Push to remote repository (GitHub, GitLab, Bitbucket) for cloud backup

**Recovery Scenario:**
If you lose your local folder but have Git backup:
```bash
git clone <repository-url>
cd ABS-Project
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python s01_readabs_datadownload.py  # Redownload data
streamlit run s05_dashboard.py       # Dashboard works immediately
```
Within minutes, entire pipeline restored and operational.

---

## 7. CONCLUSION

This skill documents a sophisticated, dual-mode pipeline for Australian economic data analysis:

**Static Mode (Traditional):**
- Automated download of 7 core ABS datasets
- Series ID filtering for clean, focused data
- Professional PNG charts for reports and publications
- Red/black styling matching employer requirements

**Interactive Mode (Modern):**
- Streamlit web dashboard for data exploration
- Toggle series on/off, adjust date ranges dynamically
- Plotly charts with hover tooltips and zoom
- Latest values table with period-on-period changes
- No code editing required for different views

**Key Characteristics:**
- ✅ **Maintainable** - Clear structure, documented processes, version controlled
- ✅ **Extensible** - Easy to add new datasets or features
- ✅ **Professional** - Publication-quality outputs when needed
- ✅ **Efficient** - Minimal manual intervention required
- ✅ **Flexible** - Quick exploration (dashboard) or polished outputs (static charts)

**Current Success Metrics:**
- ✅ 11 datasets updated automatically
- ✅ 11 professional static charts + 1 interactive dashboard
- ✅ 10 years of clean historical data
- ✅ Quarterly/monthly update cycle < 5 minutes
- ✅ Zero manual data entry required
- ✅ Interactive exploration without code changes

**Future Roadmap:**
The skill includes detailed implementation guides for:
- QoQ percentage calculations
- CLI arguments with argparse
- AI-generated commentary
- Manual scrapers for special datasets
- Custom chart titles
- Cross-dataset quarterly comparisons
- Full report generation (PDF/Word)

**Transformation Achieved:**
This pipeline transforms what was previously hours of manual work (navigating ABS website, downloading Excel files, copying data, creating charts) into:
1. **One command** for data updates: `python s01_readabs_datadownload.py`
2. **One command** for exploration: `streamlit run s05_dashboard.py`
3. **One command** for report charts: `python s02_readabs_plotting.py`

The addition of the interactive dashboard (February 2025) represents a shift from purely deterministic, static outputs to a hybrid approach: deterministic data processing with dynamic, user-controlled visualization. This maintains the reliability of automated downloads while adding the flexibility of interactive exploration—demonstrating the evolution from simple automation to sophisticated analytical tooling.
