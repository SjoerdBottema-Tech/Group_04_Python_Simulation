# M1 Project — Group 04 Monte Carlo simulation

## Run

The script requires:
1. Python 3.10 or later
2. NumPy
3. pandas
4. openpyxl

It reads:
1. `group04_dashboard.xlsx` (the `Simulation Config` sheet).
2. `inputs/simulation_config.json` (defaults and fallback when the dashboard sheet has no settings).
3. `inputs/group04_p2_data_analysis.xlsx` (the `Sheet1` supplier onset data).

How to Run:

1. Open PowerShell and navigate to the extracted project directory:
  cd path\to\Group_04_Python_Simulation

2. Create and activate a virtual environment:
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1

3. Install the required packages:
  python -m pip install numpy pandas openpyxl

4. Run the simulation:
  python run_simulation.py


## User-adjustable settings

The `Simulation Config` sheet in `group04_dashboard.xlsx` is the user-facing
configuration interface. Add settings as a two-column table with `Parameter`
and `Value` headers. The script applies these values to
`inputs/simulation_config.json`, validates the resulting configuration, and
then runs the simulation. If the sheet is blank, the existing JSON settings
are retained. Unrecognized entries in the sheet (such as other dashboard
settings) are ignored.

Use the configuration keys below as parameter names. List values can be
entered as comma-separated values (for example, `1000, 5000`) or JSON arrays.
The `scenarios` value must be a JSON array containing scenario objects. A
single numeric `Replications` value replaces the largest configured
replication count when it is not already present; the lower comparison count
is retained.

| Setting | What it controls |
| --- | --- |
| `seed` | Reproducible random number seed. |
| `simulation_counts` | At least two distinct positive replication counts. |
| `monthly_episode_rate` | Mean monthly episodes sampled from a Poisson distribution. |
| `months_per_year` | Months simulated in each replication. |
| `duration_mean_days` | Mean geometric duration in days; recovery probability is `1 / mean`. |
| `duration_threshold_days` | KPI threshold. An episode is counted when duration is strictly greater. |
| `key_suppliers` | Supplier IDs counted by the key-supplier KPI; IDs must exist in the input workbook. |
| Each scenario's `historical_onset_weight` | Blend from 1 (all historical supplier onset shares) to 0 (uniform across suppliers). |

Save the dashboard workbook before running `python run_simulation.py`. After
the run completes, open the dashboard and select **Data > Refresh All** to
refresh its Power Query connections to the generated CSV files.

Each replication samples monthly episode counts, disruption durations, and
affected supplier IDs. Historical supplier probabilities are derived from
`Sheet1`'s `Started Episodes (Onsets)` column; each scenario blends those
probabilities with a uniform distribution according to its configured weight.
The configuration requires at least two scenarios and at least two replication
counts, matching the project experiment requirements.

The default scenarios are historical onset shares (`1.0`) and a 50/50 blend
(`0.5`). The four default key suppliers are retained from the original script
and are marked High in the supplied financial-exposure data; confirm this is
the intended priority-supplier set before treating that KPI as a final business
result.

## Results and visualizations

The script generates a row for every replication and experiment, plus
experiment-level means, standard deviations, minima, and maxima for each KPI.
The KPIs include the percentage of episodes over the duration threshold,
unique suppliers affected, longest and mean duration, and key-supplier episode
share.

## Outputs

Running the script regenerates:

- `results/simulation_output.csv` — one row per replication and experiment.
- `results/simulation_results.csv` — one row per experiment with summary
  statistics for each KPI.
- `group04_p3_analysis.xlsx` — formatted `simulation_output`,
  `simulation_results`, `visualizations`, and `configuration` sheets. The
  visualizations sheet compares scenarios with charts; the configuration sheet
  documents the inputs and KPI definitions.