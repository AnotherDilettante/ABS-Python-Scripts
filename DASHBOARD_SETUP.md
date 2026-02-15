# ABS Dashboard — Setup Guide

## What this is

`dashboard.py` is an interactive web dashboard that runs locally in your browser. It reads the CSV files your pipeline already produces in `abs_data_output/` and lets you toggle datasets, series, and date ranges on the fly. No data leaves your machine.

## First-time setup (5 minutes)

### 1. Install the two new packages

Open a terminal in your ABS project folder and run:

```
pip install streamlit plotly --break-system-packages
```

Or if you're using your project's virtual environment:

```
pip install streamlit plotly
```

That's it for dependencies. Everything else (pandas, etc.) you already have.

### 2. Verify file structure

Your ABS project folder should look like this:

```
ABS-Project/
├── start.py                     # TUI control center
├── config.py                    # Dataset configuration
├── download.py                  # Data downloader
├── generate_charts.py           # Static chart generator
├── dashboard.py                 # Interactive dashboard
├── abs_data_output/
├── abs_charts_output/
└── ...
```

The dashboard needs to be in the same folder as `config.py` so it can import your dataset registry for grouping and names.

### 3. Make sure you have data

If you haven't already, run your download script first:

```
python download.py
```

You can also use CLI flags to selectively download:
```
python s01_readabs_datadownload.py --list          # List available datasets
python s01_readabs_datadownload.py --freq Monthly  # Download monthly datasets only
python s01_readabs_datadownload.py --cat 6401.0    # Download specific catalogue
```

The dashboard reads from `abs_data_output/`. No CSVs = nothing to display.

## Running the dashboard

From your ABS project folder:

```
streamlit run dashboard.py
```

Your default browser will open automatically at `http://localhost:8501`. If it doesn't, just open that URL manually.

### To stop it

Press `Ctrl+C` in the terminal where it's running.

## How to use it

- **Left sidebar** has all the controls
- **Dataset dropdown** picks which ABS release to view (GDP, CPI, Labour Force, etc.)
- **Table dropdown** appears when a dataset has multiple tables (e.g. CPI has Table 1 and Table 6)
- **Series checkboxes** toggle individual data series on/off on the chart
- **Date range slider** adjusts the time window — drag either end
- **Chart** is interactive: hover for values, click-drag to zoom, double-click to reset
- **Latest Values table** below the chart shows the most recent data point and period-on-period change

## Updating data

The dashboard reads CSVs live on each interaction. Your workflow is:

1. Run `python download.py` (refreshes the CSVs)
2. Refresh the dashboard in your browser (or it auto-detects changes)

No need to restart Streamlit.

## Troubleshooting

**"No data found" error**
→ Your `abs_data_output/` folder is empty. Run download.py first.

**"ModuleNotFoundError: No module named 'streamlit'"**
→ You installed it in a different Python environment. Make sure you're using the same Python/pip that has your other ABS packages.

**Browser doesn't open automatically**
→ Open `http://localhost:8501` manually. Completely normal on some systems.

**Port 8501 already in use**
→ Another Streamlit instance is running. Either stop it or run with a different port:
```
streamlit run dashboard.py --server.port 8502
```
