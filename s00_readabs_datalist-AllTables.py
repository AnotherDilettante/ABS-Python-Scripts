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
            "5206001_Key_Aggregates": "GDP_Table1_Key_Aggregates.csv",
            "5206005_Expenditure_Implicit_Price_Deflators": "GDP_Table5_Terms_of_Trade.csv"
        }
    },

    # 2. Average Weekly Earnings - 6302.0
    # Listed: Table 2, Table 5, Table 8
    {
        "name": "Average Weekly Earnings", 
        "cat_id": "6302.0", 
        "frequency": "Half Yearly",
        "tables": {
            "6302002": "AWE_Table1_AUS_SA.csv", 
            "6302005": "AWE_Table5_Private_SA.csv", 
            "6302008": "AWE_Table8_Public_SA.csv"
        }
    },

    # 3. Balance of Payments - 5302.0
    # Listed: Table 1, Table 2, Table 7
    {
        "name": "Balance of Payments", 
        "cat_id": "5302.0", 
        "frequency": "Quarterly",
        "tables": {
            "530201": "BoP_Table1_Overview.csv", 
            "530202": "BoP_Table2_Current_Account.csv", 
            "530207": "BoP_Table7_Capital_Financial_Account.csv" 
        }
    },

    # 4. Building Activity - 8752.0
    # Listed: Table 33, Table 37
    {
        "name": "Building Activity", 
        "cat_id": "8752.0", 
        "frequency": "Quarterly",
        "tables": {
            "87520033": "Building_Activity_Table33_Commencements.csv", 
            "87520037": "Building_Activity_Table37_Completions.csv" 
        }
    },

    # 5. Building Approvals - 8731.0
    # Listed: Table 1, Table 2, Table 3, Table 4
    {
        "name": "Building Approvals", 
        "cat_id": "8731.0", 
        "frequency": "Monthly",
        "tables": {
            "8731001": "Building_Approvals_Table1_Total.csv", 
            "8731002": "Building_Approvals_Table2_Trend.csv", 
            "8731003": "Building_Approvals_Table3_Value.csv", 
            "8731004": "Building_Approvals_Table4_Value_Trend.csv" 
        }
    },

    # 6. Business Indicators - 5676.0
    # Listed: Table 1, Table 2
    {
        "name": "Business Indicators", 
        "cat_id": "5676.0", 
        "frequency": "Quarterly",
        "tables": {
            "5676001": "Business_Ind_Table1_Key_Stats.csv", 
            "5676002": "Business_Ind_Table2_Trend.csv" 
        }
    },

    # 7. CPI - 6401.0
    # Listed: Table 1, Table 2
    {
        "name": "CPI", 
        "cat_id": "6401.0", 
        "frequency": "Quarterly",
        "tables": {
            "640101": "CPI_Table1_All_Groups.csv", 
            "640102": "CPI_Table2_Weighted_Avg_Cap_Cities.csv" 
        }
    },

    # 8. International Trade - 5368.0
    # Listed: Table 1, Table 2, Table 3, Table 4, Table 5, Table 7
    {
        "name": "International Trade", 
        "cat_id": "5368.0", 
        "frequency": "Monthly",
        "tables": {
            "536801": "Trade_Table1_Overview_Balance.csv", 
            "536802": "Trade_Table2_Goods_Credits.csv", 
            "536803": "Trade_Table3_Goods_Debits.csv", 
            "536804": "Trade_Table4_Commodities_Exports.csv", 
            "536805": "Trade_Table5_Commodities_Imports.csv", 
            "536807": "Trade_Table7_Trading_Partners.csv" 
        }
    },

    # 9. Job Vacancies - 6354.0
    # Listed: Table 1, Table 2, Table 3, Table 4
    {
        "name": "Job Vacancies", 
        "cat_id": "6354.0", 
        "frequency": "Quarterly",
        "tables": {
            "6354001": "Job_Vacancies_Table1_State.csv", 
            "6354002": "Job_Vacancies_Table2_Private.csv", 
            "6354003": "Job_Vacancies_Table3_Public.csv", 
            "6354004": "Job_Vacancies_Table4_Industry.csv" 
        }
    },

    # 10. Labour Force - 6202.0
    # Listed: Table 1, Table 12
    {
        "name": "Labour Force", 
        "cat_id": "6202.0", 
        "frequency": "Monthly",
        "tables": {
            "6202001": "Labour_Force_Table1_AUS.csv", 
            "6202012": "Labour_Force_Table12_SexState.csv" 
        }
    },

    # 11. Labour Force Detailed - 6291.0.55.001
    # Listed: Table 1, Table 6, Table 11
    {
        "name": "Labour Force Detailed", 
        "cat_id": "6291.0.55.001", 
        "frequency": "Monthly",
        "tables": {
            "6291001": "LF_Detailed_Table1_Occupation_Industry.csv", 
            "6291006": "LF_Detailed_Table6_Duration_Unemployment.csv", 
            "6291011": "LF_Detailed_Table11_Hours_Worked.csv" 
        }
    },

    # 12. Population - 3101.0
    # Listed: Table 1, Table 2, Table 6A, Table 6B
    {
        "name": "Population", 
        "cat_id": "3101.0", 
        "frequency": "Quarterly",
        "tables": {
            "310101": "Population_Table1_ERP.csv", 
            "310102": "Population_Table2_ERPState.csv", 
            "3101016A": "Population_Table6A_InterstateArr.csv",
            "3101016B": "Population_Table6B_InterstateDep.csv"
        }
    },

    # 13. Overseas Arrivals/Departures - 3401.0
    # Listed: Table 1, Table 2
    {
        "name": "Overseas Arrivals & Departures", 
        "cat_id": "3401.0", 
        "frequency": "Monthly",
        "tables": {
            "340101": "OAD_Table1_Arrivals.csv", 
            "340102": "OAD_Table2_Departures.csv"
        }
    },

    # 14. Capex - 5625.0
    # Listed: Table 1, Table 4, Table 7
    {
        "name": "Capex", 
        "cat_id": "5625.0", 
        "frequency": "Quarterly",
        "tables": {
            "01_current_prices_original_capex": "Capex_Table1_Actual_Expenditure.csv", 
            "04_current_prices_seasonally_adjusted_capex": "Capex_Table4_Industry_CurrentPrices.csv", 
            "07_volume_measures_seasonally_adjusted_capex": "Capex_Table7_Industry_ChainVolume.csv" 
        }
    },

    # 15. PPI - 6427.0
    # Listed: Table 1, Table 17, Table 18
    {
        "name": "Producer Price Index", 
        "cat_id": "6427.0", 
        "frequency": "Quarterly",
        "tables": {
            "642701": "PPI_Table1_FinalDemand.csv", 
            "6427017": "PPI_Table17_Output_Construction.csv", 
            "6427018": "PPI_Table18_Output_Housing.csv" 
        }
    },

    # 16. Retail Trade - 8501.0
    # Listed: Table 3, Table 4
    {
        "name": "Retail Trade", 
        "cat_id": "8501.0", 
        "frequency": "Monthly",
        "tables": {
            "850103": "Retail_Table3_Industry_Subgroups.csv", 
            "850104": "Retail_Table4_States.csv" 
        }
    },

    # 17. WPI - 6345.0
    # Listed: Table 1
    {
        "name": "Wage Price Index", 
        "cat_id": "6345.0", 
        "frequency": "Quarterly",
        "tables": {
            "634501": "WPI_Table1_Total_Hourly_Rates.csv" 
        }
    }
]