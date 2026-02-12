# s00_readabs_datalist.py

# --- CONFIGURATION ---
HISTORY_YEARS = 10  # How many years of data to keep
OUTPUT_DIRECTORY = "abs_data_output" 

# --- DATASET REGISTRY ---
# Strictly matched to the "Relevant data" column in your CSV.
# Keys are generated based on the Table numbers listed (e.g. Table 33 -> 8752033).

ABS_DATASETS = [

    # 1. National Accounts (GDP) - 5206.0
    # Listed: Table 1, Table 5
    {
        "name": "National Accounts (GDP)",
        "cat_id": "5206.0",
        "frequency": "Quarterly",
        "tables": {
            # OPTION 2: Series IDs
            "5206001_Key_Aggregates": {
                "filename": "GDP_Key_Aggregates_sa.csv",
                "display_title": "Gross Domestic Product - Key Aggregates",
                "calc_type": "qoq",  # Quarter-on-quarter % change
                "plot_ids": [
                    "A2304370T",  # GDP Quarterly Result
                    "A2304372W",  # GDP Per Capita Quarterly Result
                    "A2304392F",  # GDP Per Hour Worked
                    "A3606054R",  # GVA Market Sector
                    "A130272205W",  # GVA Non Market Sector
                    "A2304400V"   # Terms of Trade
                ]
            },
        }
    },

    # 2. CPI - 6401.0
    # Listed: Table 1, Table 2
    {
        "name": "CPI",
        "cat_id": "6401.0",
        "frequency": "Monthly",
        "tables": {
            # OPTION 2: Series IDs
            "640101": {
                "filename": "CPI_Table1_All_Groups.csv",
                "display_title": "Consumer Price Index - All Groups",
                "calc_type": "raw",  # Already % change in source data
                "plot_ids": [
                    "A130393721F",  # All groups CPI change from month in previous year
                    "A130393722J"  # All groups CPI change from previous month
                ]
            },
            "640106": {
                "filename": "CPI_Table6_CPI_Means.csv",
                "display_title": "Consumer Price Index - Underlying Measures",
                "calc_type": "yoy",  # Year-on-year % change
                "plot_ids": [
                    "A130607784C", # Weight Average, All Groups CPI
                    "A130400383T", # Weight Average, Trimmed Mean
                    "A130400614R"  # Weight Average, Weighted Median
                ]
            }
        }
    },

    # 3. Building Activity - 8752.0
    # Listed: Table 33, Table 37
    {
        "name": "Building Activity",
        "cat_id": "8752.0",
        "frequency": "Quarterly",
        "tables": {
            # OPTION 2: Series IDs
            "87520033": {
                "filename": "Building_Activity_Table33_Starts.csv",
                "display_title": "Building Activity - Dwelling Starts",
                "calc_type": "raw",
                "plot_ids": [
                    "A83793840W",  # Total dwelling starts
                    "A83794056K",  # Total unit starts
                    "A83801544L"   # Total house starts
                ]
            },
            "87520037": {
                "filename": "Building_Activity_Table37_Completions.csv",
                "display_title": "Building Activity - Dwelling Completions",
                "calc_type": "raw",
                "plot_ids": [
                    "A83801545R",  # Total dwelling completions
                    "A83794057L",  # Total unit completions
                    "A83793841X"   # Total house completions
                ]
            }
        }
    },

    # 4. Building Approvals - 8731.0
    # Listed: Table 1, Table 2, Table 3, Table 4
    {
        "name": "Building Approvals",
        "cat_id": "8731.0",
        "frequency": "Monthly",
        "tables": {
            # OPTION 2: Series IDs
            "8731006": {
                "filename": "Building_Approvals_Table6_Dwellings_sa.csv",
                "display_title": "Building Approvals - Dwelling Units",
                "calc_type": "raw",
                "plot_ids": [
                    "A422070J",  # Total dwelling approvals
                    "A421265R",  # Total unit approvals
                    "A418431A"   # Total house approvals
                ]
            }
        }
    },

    # 5. Population - 3101.0
    # Listed: Table 1, Table 2, Table 6A, Table 6B
    {
        "name": "Population",
        "cat_id": "3101.0",
        "frequency": "Quarterly",
        "tables": {
            # OPTION 2: Series IDs
            "310101": {
                "filename": "Population_Table1_ERP.csv",
                "display_title": "Australia - Estimated Resident Population",
                "calc_type": "raw",
                "plot_ids": [
                    "A2133251W",   # Estimated Resident Population
                    "A2133252X",   # Natural Increase
                    "A2133254C",   # Net Overseas Migration
                    "A2133256J"    # Percentage ERP Change
                ]
            },
        }
    },

    # 6. Overseas Arrivals/Departures - 3401.0
    # Listed: Table 1, Table 2
    {
        "name": "Overseas Arrivals & Departures",
        "cat_id": "3401.0",
        "frequency": "Monthly",
        "tables": {
            # OPTION 2: Series IDs
            "340101": {
                "filename": "OAD_Table1_Arrivals.csv",
                "display_title": "Overseas Migration - Arrivals",
                "calc_type": "raw",
                "plot_ids": [
                    "A85232555A"    # Permanent and Long Term Arrivals
                ]
            },
            "340102": {
                "filename": "OAD_Table2_Departures.csv",
                "display_title": "Overseas Migration - Departures",
                "calc_type": "raw",
                "plot_ids": [
                    "A85232558J"    # Permanent and Long Term Departures
                ]
            }
        }
    },

    # 7. Labour Force - 6202.0
    # Listed: Table 1, Table 12
    {
        "name": "Labour Force",
        "cat_id": "6202.0",
        "frequency": "Monthly",
        "tables": {
            # OPTION 2: Series IDs
            "6202001": {
                "filename": "LabourForce_Table1_Unemployment_sa.csv",
                "display_title": "Labour Force - Unemployment & Participation",
                "calc_type": "raw",  # Already rates in source data
                "plot_ids": [
                    "A84423050A",  # Unemployment rate, persons
                    "A84423051C",  # Participation rate, persons
                    "A84423047L"   # Labour force total
                ]
            },
            "6202022": {
                "filename": "LabourForce_Table22_Underemployment_sa.csv",
                "display_title": "Labour Force - Underemployment & Underutilisation",
                "calc_type": "raw",  # Already rates in source data
                "plot_ids": [
                    "A85256565A",   # Underemployment rate, persons
                    "A85255726K"    # Underutilisation rate, persons
                ]
            }
        }
    },
]