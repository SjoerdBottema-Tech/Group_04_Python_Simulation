import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).parent
CONFIG_FILE = PROJECT_DIR / "inputs" / "simulation_config.json"
DASHBOARD_FILE = PROJECT_DIR / "group04_dashboard.xlsx"
DATA_FILE = PROJECT_DIR / "inputs" / "group04_p2_data_analysis.xlsx"
OUTPUT_FILE = PROJECT_DIR / "results" / "simulation_output.csv"
SUMMARY_FILE = PROJECT_DIR / "results" / "simulation_results.csv"
ANALYSIS_FILE = PROJECT_DIR / "group04_p3_analysis.xlsx"

CONFIG_SHEET = "Simulation Config"
SUPPLIER_SHEET = "Sheet1"
SUPPLIER_ID_COLUMN = "Supplier"
ONSET_COUNT_COLUMN = "Started Episodes\n(Onsets)"


def load_supplier_onset_probabilities(
    data_file: Path,
) -> tuple[list[str], np.ndarray]:
    supplier_df = pd.read_excel(
        data_file,
        sheet_name=SUPPLIER_SHEET,
        usecols=[SUPPLIER_ID_COLUMN, ONSET_COUNT_COLUMN],
    )
    supplier_df = supplier_df.dropna(subset=[SUPPLIER_ID_COLUMN]).copy()
    supplier_df[SUPPLIER_ID_COLUMN] = (
        supplier_df[SUPPLIER_ID_COLUMN].astype(str).str.strip()
    )
    supplier_df[ONSET_COUNT_COLUMN] = pd.to_numeric(
        supplier_df[ONSET_COUNT_COLUMN],
        errors="raise",
    )

    if supplier_df[SUPPLIER_ID_COLUMN].eq("").any():
        raise ValueError("The supplier data contains an empty supplier ID.")
    if supplier_df[SUPPLIER_ID_COLUMN].duplicated().any():
        raise ValueError("The supplier data contains duplicate supplier IDs.")
    if (
        not np.isfinite(supplier_df[ONSET_COUNT_COLUMN]).all()
        or (supplier_df[ONSET_COUNT_COLUMN] < 0).any()
    ):
        raise ValueError("Supplier onset counts must be finite and non-negative.")

    total_onsets = supplier_df[ONSET_COUNT_COLUMN].sum()
    if total_onsets <= 0:
        raise ValueError("Supplier onset counts must sum to a positive value.")

    supplier_ids = supplier_df[SUPPLIER_ID_COLUMN].tolist()
    historical_probabilities = (
        supplier_df[ONSET_COUNT_COLUMN].to_numpy(dtype=float) / total_onsets
    )
    return supplier_ids, historical_probabilities


def _coerce_dashboard_integer(value: object) -> object:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _parse_dashboard_value(setting: str, value: object) -> object:
    if pd.isna(value):
        return None

    if not isinstance(value, str):
        if setting == "simulation_counts":
            return [_coerce_dashboard_integer(value)]
        if setting == "key_suppliers":
            return [value]
        if setting in {
            "seed",
            "months_per_year",
            "duration_threshold_days",
        }:
            return _coerce_dashboard_integer(value)
        return value

    value = value.strip()
    if not value:
        return None
    if setting in {"simulation_counts", "key_suppliers"}:
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            items = [
                item.strip()
                for item in value.split(",")
                if item.strip()
            ]
            if setting == "simulation_counts":
                parsed_value = []
                for item in items:
                    try:
                        parsed_value.append(json.loads(item))
                    except json.JSONDecodeError:
                        parsed_value.append(item)
            else:
                parsed_value = items
        if not isinstance(parsed_value, list):
            parsed_value = [parsed_value]
        if setting == "simulation_counts":
            parsed_value = [
                _coerce_dashboard_integer(item) for item in parsed_value
            ]
        return parsed_value
    if setting == "scenarios":
        try:
            return json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Dashboard 'scenarios' must be a JSON array."
            ) from error

    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value

    integer_settings = {
        "seed",
        "simulation_counts",
        "months_per_year",
        "duration_threshold_days",
    }
    if setting in integer_settings:
        if isinstance(parsed_value, list):
            return [_coerce_dashboard_integer(item) for item in parsed_value]
        return _coerce_dashboard_integer(parsed_value)
    return parsed_value


def load_dashboard_overrides(config: dict) -> dict:
    dashboard_df = pd.read_excel(
        DASHBOARD_FILE,
        sheet_name=CONFIG_SHEET,
        header=None,
        usecols="A:B",
    )
    if dashboard_df.empty:
        print(
            f"No settings found on the '{CONFIG_SHEET}' sheet; "
            "using the existing JSON settings."
        )
        return {}

    overrides = {}
    for row_number, (raw_setting, raw_value) in enumerate(
        dashboard_df.itertuples(index=False, name=None),
        start=1,
    ):
        if pd.isna(raw_setting) and pd.isna(raw_value):
            continue
        if not isinstance(raw_setting, str):
            raise ValueError(
                f"Dashboard setting in cell A{row_number} must be text."
            )

        setting = raw_setting.strip().lower().replace(" ", "_").replace("-", "_")
        if row_number == 1 and setting in {"parameter", "setting"}:
            continue
        is_replication_count = setting == "replications"
        if is_replication_count:
            setting = "simulation_counts"

        if setting not in {
            "seed",
            "simulation_counts",
            "monthly_episode_rate",
            "months_per_year",
            "duration_mean_days",
            "duration_threshold_days",
            "key_suppliers",
            "scenarios",
        }:
            raise ValueError(
                f"Unsupported dashboard setting '{raw_setting}' "
                f"in cell A{row_number}."
            )
        if setting in overrides:
            raise ValueError(f"Duplicate dashboard setting: {raw_setting}")

        parsed_value = _parse_dashboard_value(setting, raw_value)
        if parsed_value is not None:
            if is_replication_count and len(parsed_value) == 1:
                simulation_counts = list(config["simulation_counts"])
                replication_count = parsed_value[0]
                if replication_count not in simulation_counts:
                    largest_count_index = max(
                        range(len(simulation_counts)),
                        key=simulation_counts.__getitem__,
                    )
                    simulation_counts[largest_count_index] = replication_count
                parsed_value = simulation_counts
            overrides[setting] = parsed_value

    if not overrides:
        print(
            f"No settings found on the '{CONFIG_SHEET}' sheet; "
            "using the existing JSON settings."
        )
    return overrides


def load_config() -> dict:
    with CONFIG_FILE.open(encoding="utf-8") as config_file:
        config = json.load(config_file)

    config.update(load_dashboard_overrides(config))
    validate_config(config)
    temporary_config_file = CONFIG_FILE.with_name(
        f"{CONFIG_FILE.name}.tmp"
    )
    with temporary_config_file.open("w", encoding="utf-8") as config_file:
        json.dump(config, config_file, indent=2, ensure_ascii=False)
        config_file.write("\n")
    temporary_config_file.replace(CONFIG_FILE)
    print(f"Configuration updated: {CONFIG_FILE}")
    return config


def validate_config(config: dict) -> None:
    if not isinstance(config.get("seed"), int) or isinstance(config["seed"], bool):
        raise ValueError("Configuration 'seed' must be an integer.")

    simulation_counts = config.get("simulation_counts")
    if (
        not isinstance(simulation_counts, list)
        or len(simulation_counts) < 2
        or any(
            not isinstance(count, int) or isinstance(count, bool) or count <= 0
            for count in simulation_counts
        )
        or len(simulation_counts) != len(set(simulation_counts))
    ):
        raise ValueError(
            "'simulation_counts' must contain at least two distinct positive integers."
        )

    months = config.get("months_per_year")
    episode_rate = config.get("monthly_episode_rate")
    duration_mean = config.get("duration_mean_days")
    duration_threshold = config.get("duration_threshold_days")
    if not isinstance(months, int) or isinstance(months, bool) or months <= 0:
        raise ValueError("'months_per_year' must be a positive integer.")
    if (
        not isinstance(episode_rate, (int, float))
        or isinstance(episode_rate, bool)
        or not np.isfinite(episode_rate)
        or episode_rate <= 0
    ):
        raise ValueError("'monthly_episode_rate' must be positive.")
    if (
        not isinstance(duration_mean, (int, float))
        or isinstance(duration_mean, bool)
        or not np.isfinite(duration_mean)
        or duration_mean < 1
    ):
        raise ValueError("'duration_mean_days' must be at least 1.")
    if (
        not isinstance(duration_threshold, int)
        or isinstance(duration_threshold, bool)
        or duration_threshold < 0
    ):
        raise ValueError("'duration_threshold_days' must be a non-negative integer.")

    scenarios = config.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 2:
        raise ValueError("'scenarios' must contain at least two scenarios.")
    key_suppliers = config.get("key_suppliers")
    if (
        not isinstance(key_suppliers, list)
        or not key_suppliers
        or any(
            not isinstance(supplier, str) or not supplier.strip()
            for supplier in key_suppliers
        )
        or len(key_suppliers) != len(set(key_suppliers))
    ):
        raise ValueError("'key_suppliers' must contain unique, non-empty supplier IDs.")

    scenario_names = []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("Each scenario must be a JSON object.")
        name = scenario.get("name")
        description = scenario.get("description")
        historical_weight = scenario.get("historical_onset_weight")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Each scenario must have a non-empty name.")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"Scenario '{name}' must have a description.")
        if name in scenario_names:
            raise ValueError(f"Duplicate scenario name: {name}")
        scenario_names.append(name)
        if (
            not isinstance(historical_weight, (int, float))
            or isinstance(historical_weight, bool)
            or not 0 <= historical_weight <= 1
        ):
            raise ValueError(
                f"Scenario '{name}' historical_onset_weight must be between 0 and 1."
            )


def build_onset_probabilities(
    historical_probabilities: np.ndarray,
    historical_weight: float,
) -> np.ndarray:
    uniform_probabilities = np.full(
        len(historical_probabilities),
        1 / len(historical_probabilities),
    )
    return (
        historical_weight * historical_probabilities
        + (1 - historical_weight) * uniform_probabilities
    )


def summarize_results(
    results_df: pd.DataFrame,
    duration_threshold_days: int,
) -> pd.DataFrame:
    duration_metric = (
        f"pct_disruptions_over_{duration_threshold_days}_days"
    )
    metric_columns = {
        "mean_total_episodes": "total_episodes",
        "mean_pct_disruptions_over_threshold": duration_metric,
        "mean_suppliers_affected": "suppliers_affected",
        "mean_longest_duration_days": "longest_duration_days",
        "mean_pct_key_supplier_disruptions": "pct_key_supplier_disruptions",
        "mean_duration_days": "mean_duration_days",
    }
    summary_rows = []
    for (scenario, simulation_count), experiment in results_df.groupby(
        ["scenario", "simulation_count"],
        sort=False,
    ):
        row = {
            "experiment": f"{scenario} - {simulation_count:,} replications",
            "scenario": scenario,
            "simulation_count": simulation_count,
        }
        for output_name, metric in metric_columns.items():
            values = experiment[metric]
            row[output_name] = values.mean()
            row[output_name.replace("mean_", "std_")] = (
                values.std(ddof=1) if len(values) > 1 else 0
            )
            row[output_name.replace("mean_", "min_")] = values.min()
            row[output_name.replace("mean_", "max_")] = values.max()
        summary_rows.append(row)
    return pd.DataFrame(summary_rows)


def build_configuration_table(config: dict) -> pd.DataFrame:
    descriptions = {
        "seed": "Random seed used for reproducible random draws.",
        "simulation_counts": "Annual replication counts for each scenario.",
        "monthly_episode_rate": "Poisson mean number of disruption episodes per month.",
        "months_per_year": "Number of months simulated in each replication.",
        "duration_mean_days": "Geometric duration mean in days; recovery probability is 1 / mean.",
        "duration_threshold_days": "KPI counts episodes strictly longer than this threshold.",
        "key_suppliers": "Supplier IDs included in the key-supplier KPI.",
    }
    rows = [
        {
            "section": "Simulation settings",
            "setting": name,
            "value": json.dumps(value, ensure_ascii=False),
            "description": descriptions[name],
        }
        for name, value in config.items()
        if name not in {"scenarios", "description"}
    ]
    rows.extend(
        [
            {
                "section": "KPI definition",
                "setting": "% disruptions over threshold",
                "value": "%",
                "description": "Episodes lasting strictly longer than duration_threshold_days divided by all episodes.",
            },
            {
                "section": "KPI definition",
                "setting": "Suppliers affected",
                "value": "Unique suppliers per replication",
                "description": "Count of distinct suppliers sampled at least once during the replication.",
            },
            {
                "section": "KPI definition",
                "setting": "Key-supplier disruptions",
                "value": "%",
                "description": "Episodes assigned to key_suppliers divided by all episodes.",
            },
            {
                "section": "KPI definition",
                "setting": "Mean and longest duration",
                "value": "Days",
                "description": "Mean duration and longest single duration among episodes in the replication.",
            },
        ]
    )
    rows.extend(
        {
            "section": "Scenario",
            "setting": scenario["name"],
            "value": scenario["historical_onset_weight"],
            "description": scenario["description"],
        }
        for scenario in config["scenarios"]
    )
    return pd.DataFrame(rows)


def write_analysis_workbook(
    results_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    config: dict,
) -> None:
    with pd.ExcelWriter(ANALYSIS_FILE, engine="openpyxl") as writer:
        results_df.to_excel(writer, sheet_name="simulation_output", index=False)
        summary_df.to_excel(writer, sheet_name="simulation_results", index=False)
        build_configuration_table(config).to_excel(
            writer,
            sheet_name="configuration",
            index=False,
        )

    from openpyxl import load_workbook
    from openpyxl.chart import BarChart, Reference
    from openpyxl.styles import Font, PatternFill
    from openpyxl.worksheet.table import Table, TableStyleInfo

    workbook = load_workbook(ANALYSIS_FILE)
    visualizations = workbook.create_sheet("visualizations", index=2)
    visualizations["A1"] = "Monte Carlo scenario comparison"
    visualizations["A1"].font = Font(bold=True, size=16, color="1F4E78")
    visualizations["A2"] = (
        "Average KPI values by scenario and replication count. "
        "See simulation_results for variability and ranges."
    )
    for worksheet in workbook.worksheets:
        if worksheet.title == "visualizations":
            continue
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for cell in worksheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F4E78")
        for column in worksheet.columns:
            column_letter = column[0].column_letter
            max_length = max(
                len(str(cell.value)) if cell.value is not None else 0
                for cell in column[:1000]
            )
            worksheet.column_dimensions[column_letter].width = min(
                max(max_length + 2, 12),
                55,
            )
        if worksheet.max_row > 1:
            table = Table(
                displayName=f"{worksheet.title}_table",
                ref=worksheet.dimensions,
            )
            table.tableStyleInfo = TableStyleInfo(
                name="TableStyleMedium2",
                showRowStripes=True,
                showColumnStripes=False,
            )
            worksheet.add_table(table)

    for column_index, column_name in enumerate(results_df.columns, start=1):
        if column_name.startswith("pct_"):
            for row_index in range(2, len(results_df) + 2):
                workbook["simulation_output"].cell(
                    row=row_index,
                    column=column_index,
                ).number_format = '0.00"%"'

    summary_sheet = workbook["simulation_results"]
    for column_index, column_name in enumerate(summary_df.columns, start=1):
        if column_name.startswith(("mean_pct_", "std_pct_", "min_pct_", "max_pct_")):
            for row_index in range(2, summary_sheet.max_row + 1):
                summary_sheet.cell(
                    row=row_index,
                    column=column_index,
                ).number_format = '0.00"%"'

    chart_metrics = [
        (
            "mean_pct_disruptions_over_threshold",
            "Disruptions longer than threshold (%)",
            "Percentage",
        ),
        ("mean_suppliers_affected", "Unique suppliers affected", "Suppliers"),
        (
            "mean_pct_key_supplier_disruptions",
            "Key-supplier disruptions (%)",
            "Percentage",
        ),
        ("mean_duration_days", "Mean disruption duration", "Days"),
    ]
    for chart_index, (column_name, title, y_axis_title) in enumerate(chart_metrics):
        summary_column_index = summary_df.columns.get_loc(column_name) + 1
        chart = BarChart()
        chart.type = "col"
        chart.style = 10
        chart.title = title
        chart.y_axis.title = y_axis_title
        chart.x_axis.title = "Scenario and replication count"
        chart.height = 8
        chart.width = 16
        chart.add_data(
            Reference(
                summary_sheet,
                min_col=summary_column_index,
                min_row=1,
                max_row=summary_sheet.max_row,
            ),
            titles_from_data=True,
        )
        chart.set_categories(
            Reference(
                summary_sheet,
                min_col=1,
                min_row=2,
                max_row=summary_sheet.max_row,
            )
        )
        chart.legend = None
        visualizations.add_chart(
            chart,
            ("A3", "J3", "A20", "J20")[chart_index],
        )

    workbook.save(ANALYSIS_FILE)


def run_simulation() -> tuple[pd.DataFrame, pd.DataFrame]:
    config = load_config()

    supplier_ids, historical_probabilities = load_supplier_onset_probabilities(
        DATA_FILE
    )
    unknown_key_suppliers = set(config["key_suppliers"]) - set(supplier_ids)
    if unknown_key_suppliers:
        raise ValueError(
            "Configured key suppliers are missing from the input data: "
            + ", ".join(sorted(unknown_key_suppliers))
        )
    key_suppliers = set(config["key_suppliers"])
    rng = np.random.default_rng(config["seed"])
    recovery_probability = 1 / config["duration_mean_days"]
    duration_metric = (
        f"pct_disruptions_over_{config['duration_threshold_days']}_days"
    )
    results = []

    for scenario in config["scenarios"]:
        onset_probabilities = build_onset_probabilities(
            historical_probabilities,
            scenario["historical_onset_weight"],
        )
        if not np.isclose(onset_probabilities.sum(), 1):
            raise ValueError(
                f"Onset probabilities for '{scenario['name']}' do not sum to 1."
            )

        for simulation_count in config["simulation_counts"]:
            for replication in range(1, simulation_count + 1):
                monthly_episodes = rng.poisson(
                    config["monthly_episode_rate"],
                    size=config["months_per_year"],
                )
                total_episodes = int(monthly_episodes.sum())

                if total_episodes:
                    durations = rng.geometric(
                        p=recovery_probability,
                        size=total_episodes,
                    )
                    suppliers_hit = rng.choice(
                        supplier_ids,
                        size=total_episodes,
                        p=onset_probabilities,
                    )
                    pct_over_threshold = (
                        np.count_nonzero(
                            durations > config["duration_threshold_days"]
                        )
                        / total_episodes
                        * 100
                    )
                    suppliers_affected = len(np.unique(suppliers_hit))
                    longest_duration = int(durations.max())
                    pct_key_supplier_disruptions = (
                        np.count_nonzero(np.isin(suppliers_hit, list(key_suppliers)))
                        / total_episodes
                        * 100
                    )
                    mean_duration = float(durations.mean())
                else:
                    pct_over_threshold = 0.0
                    suppliers_affected = 0
                    longest_duration = 0
                    pct_key_supplier_disruptions = 0.0
                    mean_duration = 0.0

                results.append(
                    {
                        "scenario": scenario["name"],
                        "simulation_count": simulation_count,
                        "replication": replication,
                        "seed": config["seed"],
                        "total_episodes": total_episodes,
                        duration_metric: pct_over_threshold,
                        "suppliers_affected": suppliers_affected,
                        "longest_duration_days": longest_duration,
                        "pct_key_supplier_disruptions": pct_key_supplier_disruptions,
                        "mean_duration_days": mean_duration,
                    }
                )

    results_df = pd.DataFrame(results)
    expected_episode_count = (
        config["months_per_year"] * config["monthly_episode_rate"]
    )
    expected_long_disruption_pct = (
        1 - recovery_probability
    ) ** config["duration_threshold_days"] * 100
    summary_df = summarize_results(
        results_df,
        config["duration_threshold_days"],
    )
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_FILE, index=False)
    summary_df.to_csv(SUMMARY_FILE, index=False)
    write_analysis_workbook(results_df, summary_df, config)

    print(f"Simulation complete. Rows written: {len(results_df)}")
    print(f"Trial-level output: {OUTPUT_FILE}")
    print(f"Experiment summary: {SUMMARY_FILE}")
    print(f"Analysis workbook: {ANALYSIS_FILE}")
    print(f"Expected episodes per year: {expected_episode_count:.2f}")
    print(
        "Theoretical disruptions over "
        f"{config['duration_threshold_days']} days: "
        f"{expected_long_disruption_pct:.2f}%"
    )
    for scenario in config["scenarios"]:
        onset_probabilities = build_onset_probabilities(
            historical_probabilities,
            scenario["historical_onset_weight"],
        )
        expected_affected = np.sum(
            1 - np.power(1 - onset_probabilities, expected_episode_count)
        )
        print(
            f"Expected suppliers affected in {scenario['name']} "
            f"(using n={expected_episode_count:.2f}): {expected_affected:.2f}"
        )
    return results_df, summary_df


if __name__ == "__main__":
    run_simulation()
