# ABS Dashboard — Setup Guide

## What this is

`dashboard.py` is an interactive web dashboard that reads the CSV files your pipeline
produces in `abs_data_output/` and lets you toggle datasets, series, and date ranges
on the fly.

**Two ways to access it:**
- **Locally** — run on your own machine at http://localhost:8501
- **Remotely** — deployed publicly on Streamlit Community Cloud (auto-updates when
  you push new CSVs to GitHub)

---

## Local Setup (first time)

### 1. Install dependencies

```
pip install streamlit plotly --break-system-packages
```

Or if using the virtual environment:
```
venv\Scripts\activate
pip install streamlit plotly
```

### 2. Make sure you have data

```
python download.py
```

The dashboard reads from `abs_data_output/`. No CSVs = nothing to display.

### 3. Launch

```
streamlit run dashboard.py
```

Browser opens at `http://localhost:8501`. Stop with `Ctrl+C`.

You can also launch from the TUI:
```
python start.py  ->  Option 3
```

---

## How to use it

**Left sidebar:**
- **Dataset** dropdown — select ABS release (GDP, CPI, Labour Force, etc.)
- **Table** dropdown — appears when a dataset has multiple tables
- **Series checkboxes** — toggle individual series on/off
- **Date range slider** — drag either end to adjust the time window

**Main panel:**
- **Interactive chart** — hover for values, click-drag to zoom, double-click to reset
- **Latest Values table** — most recent data point, previous value, change, and % change

---

## Updating data locally

```
python download.py        # refresh CSVs
# Then refresh browser — dashboard auto-detects changes, no restart needed
```

---

## Streamlit Community Cloud (remote access)

The dashboard is deployed publicly. Any push to GitHub main automatically redeploys
the app within ~2 minutes.

**Monthly update workflow:**
```
python download.py
git add abs_data_output/
git commit -m "Data update - Mar 2026"
git push origin main
```

### Re-deploying from scratch (if needed)

1. Go to share.streamlit.io and sign in with GitHub
2. Click New app
3. Repository: `AnotherDilettante/ABS-Python-Scripts`
4. Branch: `main`
5. Main file path: `dashboard.py`
6. Click Deploy

### Font on Streamlit Cloud

Calibri is not available on the Ubuntu Linux environment Streamlit Cloud uses.
`packages.txt` (in the project root) installs `fonts-crosextra-carlito`, which is
metrically identical to Calibri. The dashboard font stack lists Carlito first so it
is picked up automatically.

---

## Troubleshooting

**"No data found" error**
→ `abs_data_output/` is empty. Run `python download.py` first.

**"ModuleNotFoundError: No module named 'streamlit'"**
→ Installed in a different Python environment. Activate venv or reinstall.

**Browser doesn't open automatically**
→ Open `http://localhost:8501` manually.

**Port 8501 already in use**
→ Another Streamlit instance is running. Stop it, or use a different port:
```
streamlit run dashboard.py --server.port 8502
```

**Streamlit Cloud shows old data**
→ CSVs haven't been pushed to GitHub. Run the monthly update workflow above.
