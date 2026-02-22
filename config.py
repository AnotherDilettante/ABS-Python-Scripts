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
                "calc_type": "raw",
                "value_format": "percent",
                "clip_percentile": [5, 95],
                "plot_ids": [
                    "A2304370T",    # GDP Quarterly Result
                    "A2304372W",    # GDP Per Capita Quarterly Result
                    "A2304392F",    # GDP Per Hour Worked
                    "A3606054R",    # GVA Market Sector
                    "A130272205W",  # GVA Non Market Sector
                    "A2304400V",    # Terms of Trade
                ],
                "labels": {
                    "A2304370T":   "GDP",
                    "A2304372W":   "GDP per capita",
                    "A2304392F":   "GDP per hour worked",
                    "A3606054R":   "GVA Market Sector",
                    "A130272205W": "GVA Non-Market Sector",
                    "A2304400V":   "Terms of Trade",
                },
            },
        }
    },

    # 2. CPI - 6401.0
    {
        "name": "CPI",
        "cat_id": "6401.0",
        "frequency": "Monthly",
        "resample_to_quarterly": True,
        "resample_method": "last",
        "tables": {
            "640101": {
                "filename": "CPI_Table1_All_Groups.csv",
                "display_title": "Consumer Price Index - All Groups",
                "calc_type": "raw",
                "value_format": "percent",
                "plot_ids": [
                    "A130393721F",  # All groups CPI, change from prev year's month
                    "A130393722J",  # All groups CPI, change from prev month
                ],
                "labels": {
                    "A130393721F": "Annual change",
                    "A130393722J": "Monthly change",
                },
            },
            "640106": {
                "filename": "CPI_Table6_CPI_Means.csv",
                "display_title": "Consumer Price Index - Underlying Measures",
                "calc_type": "raw",
                "value_format": "percent",
                "plot_ids": [
                    "A130607784C",  # Weighted Avg, All Groups CPI
                    "A130400383T",  # Weighted Average, Trimmed Mean
                    "A130400614R",  # Weighted Average, Weighted Median
                ],
                "labels": {
                    "A130607784C": "Weighted Avg",
                    "A130400383T": "Trimmed Mean",
                    "A130400614R": "Weighted Median",
                },
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
                ],
                "labels": {
                    "A83793840W": "Total starts",
                    "A83794056K": "Unit starts",
                    "A83801544L": "House starts",
                },
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
                ],
                "labels": {
                    "A83801545R": "Total completions",
                    "A83794057L": "Unit completions",
                    "A83793841X": "House completions",
                },
            }
        }
    },

    # 4. Building Approvals - 8731.0
    {
        "name": "Building Approvals",
        "cat_id": "8731.0",
        "frequency": "Monthly",
        "resample_to_quarterly": True,
        "resample_method": "sum",
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
                ],
                "labels": {
                    "A422070J": "Total approvals",
                    "A421265R": "Unit approvals",
                    "A418431A": "House approvals",
                },
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
                "value_format": "mixed",
                "plot_ids": [
                    "A2133251W",  # Estimated Resident Population
                    "A2133252X",  # Natural Increase
                    "A2133254C",  # Net Overseas Migration
                    "A2133256J",  # Percentage ERP Change - excluded below
                ],
                "labels": {
                    "A2133251W": "Population",
                    "A2133252X": "Natural Increase",
                    "A2133254C": "NOM",
                },
                # Dual-axis: ERP on left starting at 20m; NOM and NI on right
                "dual_axis": {
                    "primary_ids":       ["A2133251W"],
                    "secondary_ids":     ["A2133252X", "A2133254C"],
                    "exclude_ids":       ["A2133256J"],
                    "primary_format":    "thousands",
                    "secondary_format":  "thousands",
                    "primary_ymin":      20_000,
                    "y_label_primary":   "ERP (m)",
                    "y_label_secondary": "Persons ('000)",
                },
            },
        }
    },

    # 6. Overseas Arrivals and Departures - 3401.0
    {
        "name": "Overseas Arrivals and Departures",
        "cat_id": "3401.0",
        "frequency": "Monthly",
        "resample_to_quarterly": True,
        "resample_method": "sum",
        "merge_tables": {
            "340101": "A85232555A",   # Long Term Arrivals
            "340102": "A85232558J",   # Long Term Departures
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
                # Net column is derived by download.py; key on its column name prefix
                "Net":        "Net Arrivals",
            },
            "arrivals_label":   "Long Term Arrivals ('000)",
            "departures_label": "Long Term Departures ('000)",
            "net_label":        "Net Long Term Arrivals ('000)",
        },
        "tables": {},
    },

    # 7. Labour Force - 6202.0
    {
        "name": "Labour Force",
        "cat_id": "6202.0",
        "frequency": "Monthly",
        "resample_to_quarterly": True,
        "resample_method": "last",
        "tables": {
            "6202001": {
                "filename": "LabourForce_Table1_Unemployment_sa.csv",
                "display_title": "Labour Force - Unemployment and Participation",
                "calc_type": "raw",
                "value_format": "mixed",
                "plot_ids": [
                    "A84423050A",  # Unemployment rate
                    "A84423051C",  # Participation rate
                    "A84423047L",  # Labour force total
                ],
                "labels": {
                    "A84423047L": "Labour Force",
                    "A84423050A": "Unemployment Rate",
                    "A84423051C": "Participation Rate",
                },
                # Dual-axis: labour force total on left (m), rates on right (%)
                "dual_axis": {
                    "primary_ids":       ["A84423047L"],
                    "secondary_ids":     ["A84423050A", "A84423051C"],
                    "primary_format":    "thousands",
                    "secondary_format":  "percent",
                    "y_label_primary":   "Persons (m)",
                    "y_label_secondary": "Rate (%)",
                },
            },
            "6202022": {
                "filename": "LabourForce_Table22_Underemployment_sa.csv",
                "display_title": "Labour Force - Underemployment and Underutilisation",
                "calc_type": "raw",
                "value_format": "percent",
                "plot_ids": [
                    "A85256565A",  # Underemployment rate
                    "A85255726K",  # Underutilisation rate
                ],
                "labels": {
                    "A85256565A": "Underemployment Rate",
                    "A85255726K": "Underutilisation Rate",
                },
            }
        }
    },
]

# --- VALUE FORMAT REFERENCE ---
# "percent"   -> Y-axis: "Rate (%)"         Title suffix: "(%)"
# "thousands" -> Y-axis: "Persons ('000)"   Title suffix: "('000)" or "(m)"
# "count"     -> Y-axis: "Dwellings ('000)" Title suffix: "('000)"
# "index"     -> Y-axis: "Index"            Title suffix: "(Index)"
# "raw"       -> Y-axis: "Value"            Title suffix: ""
# "mixed"     -> Per-series format resolved by Series ID lookup in generate_charts.py
