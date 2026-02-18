# config.py

# --- CONFIGURATION ---
HISTORY_YEARS = 10  # How many years of data to keep
OUTPUT_DIRECTORY = "abs_data_output"

# --- DATASET REGISTRY ---
ABS_DATASETS = [

    # 1. National Accounts (GDP) - 5206.0
    {
        "name": "National Accounts (GDP)",
        "cat_id": "5206.0",
        "frequency": "Quarterly",
        "tables": {
            "5206001_Key_Aggregates": {
                "filename": "GDP_Key_Aggregates_sa.csv",
                "display_title": "Gross Domestic Product - Key Aggregates",
                "calc_type": "raw",          # Source data is already QoQ % change
                "value_format": "percent",
                "plot_ids": [
                    "A2304370T",    # GDP Quarterly Result
                    "A2304372W",    # GDP Per Capita Quarterly Result
                    "A2304392F",    # GDP Per Hour Worked
                    "A3606054R",    # GVA Market Sector
                    "A130272205W",  # GVA Non Market Sector
                    "A2304400V",    # Terms of Trade
                ]
            },
        }
    },

    # 2. CPI - 6401.0
    {
        "name": "CPI",
        "cat_id": "6401.0",
        "frequency": "Monthly",
        "resample_to_quarterly": True,   # Convert monthly to quarterly for comparison
        "resample_method": "last",       # Use last obs of quarter (% change series)
        "tables": {
            "640101": {
                "filename": "CPI_Table1_All_Groups.csv",
                "display_title": "Consumer Price Index - All Groups",
                "calc_type": "raw",      # Already % change in source data
                "value_format": "percent",
                "plot_ids": [
                    "A130393721F",  # All groups CPI, change from prev year's month
                    "A130393722J",  # All groups CPI, change from prev month
                ]
            },
            "640106": {
                "filename": "CPI_Table6_CPI_Means.csv",
                "display_title": "Consumer Price Index - Underlying Measures",
                "calc_type": "raw",      # Already period % change in source data
                "value_format": "percent",
                "plot_ids": [
                    "A130607784C",  # Weighted Avg, All Groups CPI
                    "A130400383T",  # Weighted Average, Trimmed Mean
                    "A130400614R",  # Weighted Average, Weighted Median
                ]
            }
        }
    },

    # 3. Building Activity - 8752.0
    {
        "name": "Building Activity",
        "cat_id": "8752.0",
        "frequency": "Quarterly",
        "tables": {
            "87520033": {
                "filename": "Building_Activity_Table33_Starts.csv",
                "display_title": "Building Activity - Dwelling Starts",
                "calc_type": "raw",
                "value_format": "count",
                "plot_ids": [
                    "A83793840W",  # Total dwelling starts
                    "A83794056K",  # Total unit starts
                    "A83801544L",  # Total house starts
                ]
            },
            "87520037": {
                "filename": "Building_Activity_Table37_Completions.csv",
                "display_title": "Building Activity - Dwelling Completions",
                "calc_type": "raw",
                "value_format": "count",
                "plot_ids": [
                    "A83801545R",  # Total dwelling completions
                    "A83794057L",  # Total unit completions
                    "A83793841X",  # Total house completions
                ]
            }
        }
    },

    # 4. Building Approvals - 8731.0
    {
        "name": "Building Approvals",
        "cat_id": "8731.0",
        "frequency": "Monthly",
        "resample_to_quarterly": True,   # Convert monthly to quarterly for comparison
        "resample_method": "sum",        # Sum dwellings within each quarter
        "tables": {
            "8731006": {
                "filename": "Building_Approvals_Table6_Dwellings_sa.csv",
                "display_title": "Building Approvals - Dwelling Units",
                "calc_type": "raw",
                "value_format": "count",
                "plot_ids": [
                    "A422070J",  # Total dwelling approvals
                    "A421265R",  # Total unit approvals
                    "A418431A",  # Total house approvals
                ]
            }
        }
    },

    # 5. Population - 3101.0
    {
        "name": "Population",
        "cat_id": "3101.0",
        "frequency": "Quarterly",
        "tables": {
            "310101": {
                "filename": "Population_Table1_ERP.csv",
                "display_title": "Australia - Estimated Resident Population",
                "calc_type": "raw",
                "value_format": "mixed",  # ERP/NOM/NI = '000s; % ERP change = %
                "plot_ids": [
                    "A2133251W",  # Estimated Resident Population
                    "A2133252X",  # Natural Increase
                    "A2133254C",  # Net Overseas Migration
                    "A2133256J",  # Percentage ERP Change
                ]
            },
        }
    },

    # 6. Overseas Arrivals/Departures - 3401.0
    # NOTE: download.py merges the two tables into one combined CSV with a net column.
    {
        "name": "Overseas Arrivals & Departures",
        "cat_id": "3401.0",
        "frequency": "Monthly",
        "resample_to_quarterly": True,   # Convert monthly to quarterly for comparison
        "resample_method": "sum",        # Sum movements within each quarter
        "merge_tables": {                # Special handler: merge + derive net column
            "340101": "A85232555A",      # Long Term Arrivals series ID
            "340102": "A85232558J",      # Long Term Departures series ID
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
        "tables": {},                    # No standard tables - handled via merge_tables
    },

    # 7. Labour Force - 6202.0
    {
        "name": "Labour Force",
        "cat_id": "6202.0",
        "frequency": "Monthly",
        "resample_to_quarterly": True,   # Convert monthly to quarterly for comparison
        "resample_method": "last",       # Use last obs of quarter (rate series)
        "tables": {
            "6202001": {
                "filename": "LabourForce_Table1_Unemployment_sa.csv",
                "display_title": "Labour Force - Unemployment & Participation",
                "calc_type": "raw",      # Already rates in source data
                "value_format": "mixed", # Rates = %; Labour force total = '000s
                "plot_ids": [
                    "A84423050A",  # Unemployment rate, persons
                    "A84423051C",  # Participation rate, persons
                    "A84423047L",  # Labour force total
                ]
            },
            "6202022": {
                "filename": "LabourForce_Table22_Underemployment_sa.csv",
                "display_title": "Labour Force - Underemployment & Underutilisation",
                "calc_type": "raw",      # Already rates in source data
                "value_format": "percent",
                "plot_ids": [
                    "A85256565A",  # Underemployment rate, persons
                    "A85255726K",  # Underutilisation rate, persons
                ]
            }
        }
    },
]

# --- VALUE FORMAT REFERENCE ---
# "percent"   -> End label: "6.1%"      Y-axis: "% / Rate"
# "thousands" -> End label: "61.0"      Y-axis: "'000s"
# "count"     -> End label: "18,797"    Y-axis: "Dwellings"
# "index"     -> End label: "102.3"     Y-axis: "Index"
# "raw"       -> End label: "18,797.0"  Y-axis: "Value"  (default)
# "mixed"     -> Per-series format resolved by Series ID lookup in generate_charts.py / dashboard.py
