# M1 Project — Group 04 Monte Carlo simulation

## Run

From the project directory, run:

```powershell
python run_simulation.py
```

The script requires Python 3.10 or later, NumPy, pandas, and openpyxl. It reads
`simulation_config.json` and `inputs/group04_p2_data_analysis.xlsx` (the
`Sheet1` supplier onset data).

## User-adjustable settings

`simulation_config.json` is the simulation interface. Edit it with any text
editor, save valid JSON, then rerun the command above. The file documents each
scenario and can be used to adjust:

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