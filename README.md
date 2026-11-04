# M1 Project — Group 04 Monte Carlo Simulation and Dashboard

## Overview

This project supports supplier disruption risk management through Monte Carlo simulation and an Excel-based decision-support dashboard. Users can modify simulation settings through the dashboard, run the simulation in Python, and refresh the dashboard to evaluate alternative disruption scenarios.

## Requirements

The script requires:

1. Python 3.10 or later
2. NumPy
3. pandas
4. openpyxl

## Project Inputs

The simulation reads:

1. `group04_dashboard.xlsx` (`Simulation Config` sheet)
2. `inputs/simulation_config.json` (default configuration and fallback values)
3. `inputs/group04_p2_data_analysis.xlsx` (`Sheet1` supplier onset data)

## Running the Simulation

### 1. Navigate to the Project Folder

```powershell
cd path\to\Group_04_Python_Simulation
```

### 2. Create and Activate a Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install numpy pandas openpyxl
```

### 4. Run the Simulation

```powershell
python run_simulation.py
```

## Dashboard Workflow

The dashboard has been designed as the primary user interface.

```text
Simulation Config Sheet
        ↓
run_simulation.py
        ↓
simulation_config.json
        ↓
Monte Carlo Simulation
        ↓
simulation_output.csv
simulation_results.csv
        ↓
Power Query Refresh
        ↓
Dashboard Visualizations
        ↓
Management Recommendation
```

After the simulation completes:

1. Open `group04_dashboard.xlsx`
2. Select **Data → Refresh All**
3. Review the updated KPI cards, scenario comparison charts, baseline comparisons, variability analysis, and recommendation

## User-Adjustable Settings

The **Simulation Config** sheet serves as the user-facing configuration interface.

The simulation reads only the supported simulation settings. Additional dashboard-related settings that may appear elsewhere on the worksheet are ignored by the simulation.

Supported settings:

| Setting | Description |
|----------|-------------|
| `seed` | Reproducible random number seed |
| `simulation_counts` / `Replications` | Replication counts used in experiments |
| `monthly_episode_rate` | Mean monthly disruption episodes |
| `months_per_year` | Number of months simulated per replication |
| `duration_mean_days` | Mean disruption duration |
| `duration_threshold_days` | Threshold used for long-disruption KPI |
| `key_suppliers` | Supplier IDs used in key-supplier KPI |
| `scenarios` | Scenario definitions and onset-weight settings |

A single numeric **Replications** value replaces the largest configured replication count while preserving the lower comparison replication count.

## Simulation Logic

Each replication:

1. Generates disruption episodes using a Poisson distribution.
2. Selects affected suppliers using scenario-specific onset probabilities.
3. Generates disruption durations using a geometric distribution.
4. Calculates all KPIs.
5. Stores the results.

Historical supplier probabilities are derived from the `Started Episodes (Onsets)` column in `inputs/group04_p2_data_analysis.xlsx`.

Two default scenarios are provided:

- Historical Onset Model (`historical_onset_weight = 1.0`)
- Blended Onset Model (`historical_onset_weight = 0.5`)

## Dashboard Outputs

The dashboard presents:

- KPI Cards
  - Mean Duration (days)
  - Disruptions Above Threshold (%)
  - Suppliers Affected
  - Key Supplier Disruptions (%)
  - Total Episodes

- Scenario Comparison
  - Historical Onset Model
  - Blended Onset Model

- Baseline Comparison
  - Historical operational performance versus simulated alternatives

- Risk and Variability Analysis
  - Average
  - Standard deviation
  - Minimum
  - Maximum

- Management Recommendation

## Generated Outputs

Every execution regenerates:

### `results/simulation_output.csv`

Replication-level results.

Contains:

- scenario
- simulation_count
- replication
- seed
- total_episodes
- pct_disruptions_over_threshold
- suppliers_affected
- longest_duration_days
- pct_key_supplier_disruptions
- mean_duration_days

### `results/simulation_results.csv`

Experiment-level summaries.

Contains:

- Means
- Standard deviations
- Minimum values
- Maximum values

for each KPI, grouped by scenario and replication count.

## Troubleshooting

### Simulation Does Not Run

Verify:

- Python is installed
- Required packages are installed
- All input files are present

### Dashboard Does Not Refresh

Verify:

- `simulation_results.csv` was generated
- `simulation_output.csv` was generated
- Data → Refresh All has been executed

### Power Query Path Issues
The dashboard uses a Power Query parameter (BaseFolder) to centralize file locations.
 
If the project folder is moved to a different location or device:
 
1. Open the Simulation Config sheet.
2. Update the BaseFolder path if required.
3. Select Data → Refresh All.
 
The Power Query connections will then locate:
 
- results/simulation_output.csv
- results/simulation_results.csv
 
using the updated path.

## Reproducibility

Simulation results can be reproduced using:

- The same Python version
- The same package versions
- The same seed
- The same configuration settings
- The same input data

The seed used for a run is recorded in the simulation outputs.