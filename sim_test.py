import numpy as np
import pandas as pd
from pathlib import Path

# =============================================
# PATHS
# =============================================

PROJECT_DIR = Path(__file__).parent

DATA_FILE = (
    PROJECT_DIR /
    "inputs" /
    "group04_p2_data_analysis.xlsx"
)

OUTPUT_FILE = (
    PROJECT_DIR /
    "results" /
    "sim_test_output.csv"
)

SEED = 2026
SIMULATION_COUNT = 1000

np.random.seed(SEED)

# =============================================
# LOAD SHEETS
# =============================================

financial_exposure = pd.read_excel(
    DATA_FILE,
    sheet_name="financial_exposure"
)

supplier_disruptions = pd.read_excel(
    DATA_FILE,
    sheet_name="Sheet1"
)

# =============================================
# CLEAN NUMERIC DATA
# =============================================

financial_exposure["Cost Share %"] = pd.to_numeric(
    financial_exposure["Cost Share %"],
    errors="coerce"
)

financial_exposure["Quantity Share %"] = pd.to_numeric(
    financial_exposure["Quantity Share %"],
    errors="coerce"
)

financial_exposure["Exposure Ratio"] = pd.to_numeric(
    financial_exposure["Exposure Ratio"],
    errors="coerce"
)

# =============================================
# HISTORICAL PARAMETERS
# =============================================

cost_mean = (
    financial_exposure["Cost Share %"]
    .dropna()
    .mean()
)

cost_std = (
    financial_exposure["Cost Share %"]
    .dropna()
    .std()
)

quantity_mean = (
    financial_exposure["Quantity Share %"]
    .dropna()
    .mean()
)

quantity_std = (
    financial_exposure["Quantity Share %"]
    .dropna()
    .std()
)

exposure_mean = (
    financial_exposure["Exposure Ratio"]
    .dropna()
    .mean()
)

exposure_std = (
    financial_exposure["Exposure Ratio"]
    .dropna()
    .std()
)

print("\nSimulation Parameters")
print("---------------------")
print("Cost Share Mean:", cost_mean)
print("Quantity Share Mean:", quantity_mean)
print("Exposure Mean:", exposure_mean)

# =============================================
# MONTE CARLO
# =============================================

results = []

for replication in range(
    1,
    SIMULATION_COUNT + 1
):

    simulated_cost_share = np.random.normal(
        cost_mean,
        cost_std
    )

    simulated_quantity_share = np.random.normal(
        quantity_mean,
        quantity_std
    )

    simulated_exposure = np.random.normal(
        exposure_mean,
        exposure_std
    )

    # -----------------------------------------
    # SAMPLE KPIs
    # -----------------------------------------

    risk_score = (
        simulated_cost_share * 0.4 +
        simulated_quantity_share * 0.3 +
        simulated_exposure * 0.3
    )

    high_risk_flag = int(
        risk_score >
        (exposure_mean * 1.25)
    )

    results.append({
        "replication": replication,
        "cost_share": simulated_cost_share,
        "quantity_share": simulated_quantity_share,
        "exposure_ratio": simulated_exposure,
        "risk_score": risk_score,
        "high_risk_flag": high_risk_flag
    })

# =============================================
# SAVE RESULTS
# =============================================

results_df = pd.DataFrame(results)

OUTPUT_FILE.parent.mkdir(
    exist_ok=True
)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)

# =============================================
# QUICK SUMMARY
# =============================================

print("\nSimulation Complete")

print(
    "\nAverage Risk Score:",
    round(
        results_df["risk_score"].mean(),
        4
    )
)

print(
    "Risk Std Dev:",
    round(
        results_df["risk_score"].std(),
        4
    )
)

print(
    "High Risk Probability:",
    round(
        results_df["high_risk_flag"].mean()
        * 100,
        2
    ),
    "%"
)

print(
    "\nOutput File:",
    OUTPUT_FILE
)