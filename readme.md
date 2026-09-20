# File Pipeline

## Overview

File Pipeline is a local ETL pipeline for processing order data from a CSV file.

The pipeline reads raw order records, validates the input data, separates invalid rows into a quarantine output, calculates aggregated order metrics from valid rows, writes the results to JSON files, and stores run metadata for auditability.

This project is designed as a practical Data Engineering learning project. It focuses on clean Python structure, data validation, automated testing, type hints, logging, linting, formatting, and reproducible quality checks.

## Business Scenario

A company receives daily order exports from an operational system as CSV files.

The analytics and finance teams need reliable aggregated order metrics for reporting, operational monitoring, and future analytical use cases. This pipeline prepares metrics such as total orders, paid orders, cancelled orders, failed orders, total amount, paid amount, and average paid order amount.

## Pipeline Flow

```text
JSON contract -> preflight
                       |
                       v
CSV input -> SHA-256 -> extract -> transform -> load -> metrics JSON
                            |
                            -> rejected rows JSON
                            |
                            -> run metadata JSON + per-run history
```

Pipeline stages:

- `preflight` loads and validates the JSON data contract before the CSV is read.
- `extract` reads raw CSV records, validates them, and separates rejected rows.
- `transform` calculates aggregated order metrics.
- `load` writes calculated metrics, rejected rows, and run metadata to JSON files.
- `main` orchestrates the full pipeline execution.

## Input Data

The expected input file is:

```text
data/raw/orders.csv
```

Each row in the CSV file represents one order.

Required columns:

| Column | Type | Description |
|---|---|---|
| `order_id` | integer | Unique order identifier |
| `customer_id` | integer | Customer identifier |
| `order_date` | string | Order date in `YYYY-MM-DD` format |
| `amount` | float | Order amount |
| `status` | string | Order status |

Allowed `status` values:

```text
paid
cancelled
failed
```

Example input:

```csv
order_id,customer_id,order_date,amount,status
1,101,2026-09-01,250.50,paid
2,102,2026-09-01,99.90,paid
3,103,2026-09-02,180.00,cancelled
4,104,2026-09-02,320.10,paid
5,105,2026-09-03,15.00,failed
```

## Output Data

The pipeline writes aggregated metrics to:

```text
data/processed/order_metrics.json
```

The pipeline also writes rejected rows to:

```text
data/rejected/rejected_orders.json
```

Pipeline run metadata is written to:

```text
data/processed/run_metadata.json
```

Example metadata output:

```json
{
  "run_id": "7c4c0660-d679-41c5-97bb-f5275502d053",
  "status": "success",
  "started_at": "2026-09-08T10:15:30.123456+00:00",
  "finished_at": "2026-09-08T10:15:30.223456+00:00",
  "duration_seconds": 0.1,
  "input_path": "data/raw/orders.csv",
  "contract_path": "contracts/orders_v1.json",
  "metrics_output_path": "data/processed/order_metrics.json",
  "rejected_output_path": "data/rejected/rejected_orders.json",
  "max_error_rate": 0.05,
  "total_rows": 5,
  "valid_rows_count": 5,
  "rejected_rows_count": 0,
  "error_rate": 0.0,
  "error_type": null,
  "error_message": null,
  "input_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
}
```

Example output:

```json
{
  "orders_count": 5,
  "paid_orders_count": 3,
  "cancelled_orders_count": 1,
  "failed_orders_count": 1,
  "total_amount": 865.5,
  "paid_amount": 670.5,
  "average_paid_amount": 223.5
}
```

## Data Quality Checks

The extract layer validates input data before it is passed to the transform layer.

The pipeline checks that:

- the input path exists;
- the input path points to a file;
- the CSV file contains all required columns;
- `order_id` can be converted to an integer;
- `customer_id` can be converted to an integer;
- `order_id` is positive;
- `customer_id` is positive;
- `amount` can be converted to a float;
- `amount` is not negative;
- `status` is one of `paid`, `cancelled`, or `failed`.

If the CSV file is empty, the pipeline returns an empty order list and produces zero metrics.

`order_date` must be a valid ISO date in `YYYY-MM-DD` format. The pipeline validates it and stores it as a normalized ISO date string.

Row-level validation errors are written to the rejected rows output instead of being silently ignored. Each rejected row contains the original CSV line number, the raw row values, and the validation error message.

The pipeline uses `max_error_rate` to decide whether the run is still acceptable. For example, `0.05` means that up to 5% invalid rows are allowed. If the rejected rows share exceeds the configured threshold, the pipeline fails.

## Metrics

The transform layer calculates the following metrics:

| Metric | Description |
|---|---|
| `orders_count` | Total number of orders |
| `paid_orders_count` | Number of orders with status `paid` |
| `cancelled_orders_count` | Number of orders with status `cancelled` |
| `failed_orders_count` | Number of orders with status `failed` |
| `total_amount` | Sum of all order amounts |
| `paid_amount` | Sum of amounts for paid orders only |
| `average_paid_amount` | Average amount for paid orders |

If there are no paid orders, `average_paid_amount` is written as `null` in JSON.

## Project Structure

```text
file_pipeline/
  contracts/
    orders_v1.json
  data/
    raw/
      orders.csv
    processed/
      order_metrics.json
      run_metadata.json
      runs/
        <run_id>.json
    rejected/
      rejected_orders.json
  src/
    __init__.py
    data_contract.py
    extract.py
    transform.py
    load.py
    main.py
    schemas.py
  tests/
    test_extract.py
    test_transform.py
    test_load.py
    test_pipeline.py
  mypy.ini
  pytest.ini
  pyproject.toml
  requirements.txt
  readme.md
```

Responsibilities:

- `src/extract.py` reads and validates raw CSV data.
- `src/data_contract.py` loads and validates the JSON contract used by preflight.
- `src/transform.py` calculates order metrics.
- `src/load.py` writes metrics to a JSON file.
- `src/main.py` orchestrates the pipeline.
- `src/schemas.py` contains typed data contracts.
- `tests/test_extract.py` tests CSV reading and input validation.
- `tests/test_transform.py` tests metric calculation logic.
- `tests/test_load.py` tests JSON writing behavior.
- `tests/test_pipeline.py` tests the full pipeline flow.
- `tests/test_main.py` tests CLI argument parsing.
- `pytest.ini` configures pytest test discovery and output.
- `mypy.ini` configures static type checking.
- `pyproject.toml` configures Ruff linting and formatting.
- `requirements.txt` stores project dependencies.

## How To Run

Run all commands from the project root.

With default paths:

```powershell
python -m src.main
```

By default, the pipeline reads:

```text
contracts/orders_v1.json
data/raw/orders.csv
```

and writes:

```text
data/processed/order_metrics.json
data/rejected/rejected_orders.json
data/processed/run_metadata.json
```

With custom input, metrics output, rejected rows output, and error threshold:

```powershell
python -m src.main --contract contracts/orders_v1.json --input data/raw/orders.csv --output data/processed/custom_metrics.json --rejected-output data/rejected/custom_rejected_orders.json --metadata-output data/processed/custom_run_metadata.json --max-error-rate 0.05
```

CLI help:

```powershell
python -m src.main --help
```

CLI arguments:

- `--contract` defines the path to the JSON data contract.
- `--input` defines the path to the input orders CSV file.
- `--output` defines the path to the output metrics JSON file.
- `--rejected-output` defines the path to the rejected rows JSON file.
- `--metadata-output` defines the path to the pipeline run metadata JSON file.
- `--max-error-rate` defines the maximum allowed share of invalid rows, from `0` to `1`.

If CLI arguments are not provided, the pipeline uses default values from `src/config.py`.

Relative paths are resolved from the directory where the command is executed. For predictable behavior, run commands from the project root.
## How To Run Quality Checks

Run all quality checks from the project root:

```powershell
python -m ruff check .
python -m ruff format .
python -m mypy
python -m pytest
```

What these commands do:

- `ruff check` runs linting checks and detects unused imports, import ordering issues, style problems, outdated syntax, and some potential bugs.
- `ruff format` formats Python code according to the project style.
- `mypy` checks static type hints and typed data contracts.
- `pytest` runs unit and integration tests.

## Testing Strategy

The project includes both unit tests and an integration test.

Unit tests cover:

- JSON contract syntax and runtime structure validation;
- valid CSV extraction;
- missing input files;
- missing required columns;
- invalid numeric values;
- negative amounts;
- unsupported statuses;
- metric calculation for normal input;
- metric calculation for empty input;
- metric calculation without paid orders;
- JSON output creation;
- JSON content validation;
- parent directory creation;
- `None` serialization as JSON `null`.
- CLI argument parsing;
- rejected rows collection;
- run metadata creation;
- configurable error threshold validation.
- failed-run metadata and error classification;
- a successful rerun after the contract is fixed.

The integration test verifies the full flow:

```text
JSON contract -> load_data_contract -> CSV hash -> extract_orders -> calculate_metrics -> write_json -> outputs + run metadata history
```

## Type Hints And Data Contracts

The project uses type hints and `TypedDict` schemas to describe internal data contracts.

- `Order` describes a validated order record after extraction.
- `OrderStatus` restricts allowed order statuses to `paid`, `cancelled`, and `failed`.
- `RejectedRow` describes an invalid raw CSV row and its validation error.
- `ExtractResult` describes the extraction result: valid orders, rejected rows, row counts, and error rate.
- `Metrics` describes the output metrics structure.
- `PipelineRunMetadata` describes operational metadata for a pipeline run.

Type hints are checked with `mypy`. Runtime validation is still required because input CSV data comes from an external source and is read as raw text.

## Logging

The pipeline uses Python's built-in `logging` module.

The logs include:

- pipeline start and successful completion;
- project root path;
- contract JSON path;
- input CSV path;
- output JSON path;
- rejected rows JSON path;
- run metadata JSON path;
- maximum allowed error rate;
- CSV columns detected during extraction;
- number of total, valid, and rejected rows;
- JSON write operation;
- exception traceback when the pipeline fails.

## Error Handling

The pipeline uses a hybrid error handling strategy.

File-level and schema-level problems are fail-fast errors. Row-level data quality problems are quarantined into a rejected rows file, as long as the configured error threshold is not exceeded.

The pipeline fails if:

- the contract file does not exist;
- the contract is not valid JSON;
- the contract does not pass runtime structure validation;
- the input file does not exist;
- the input path is not a file;
- required columns are missing;
- the share of rejected rows is greater than `max_error_rate`;
- an unexpected error occurs during processing.

The pipeline rejects individual rows if:

- numeric fields cannot be converted;
- `order_id` or `customer_id` is not positive;
- `order_date` is not a valid ISO date;
- `amount` is negative;
- `status` contains an unsupported value.

Rejected rows are saved with the CSV line number and the original raw row, which makes debugging and data quality investigation easier.

## Version 1 Status

Version 1 is complete as a local Python ETL pipeline. It provides contract preflight validation, input hashing, row quarantine with an error threshold, metrics output, structured run metadata, per-run history, and automated quality checks.

If a run fails before extraction, row counts and `error_rate` are stored as `null` because those values were not measured. After the cause is fixed, a rerun receives a new `run_id`. The failed history entry is preserved, while `run_metadata.json` is updated with the latest run state.

## Current Limitations

Current limitations:

- only local CSV input is supported;
- output is written only to a local JSON file;
- each run overwrites the selected JSON output;
- fixed output paths do not contain `run_id`, so an old output cannot always be linked to one exact previous run;
- the contract path is recorded, but contract content is not identified by a hash;
- the JSON contract is a preflight gate, while row validation rules still come from `src.config`;
- history and latest metadata are written as two separate atomic file operations, not one transaction;
- results are not loaded into a database;
- the pipeline is not containerized;
- the pipeline is not scheduled by an orchestrator;
- there is no CI pipeline yet.

## Roadmap

Planned improvements:

- add PostgreSQL output and an explicit data model;
- add incremental and idempotent processing;
- package the pipeline with Docker;
- orchestrate the pipeline with Airflow;
- add dbt models and tests;
- add CI quality gates, operational metrics, and alerts;
- add schema evolution, backfill, and recovery scenarios;
- add an Oracle/OEBS CDC scenario when the source requirements justify it.

## Learning Goals

This project demonstrates the following Data Engineering fundamentals:

- local ETL pipeline structure;
- separation of responsibilities between extract, transform, load, and orchestration layers;
- input data validation;
- fail-fast error handling;
- typed internal data contracts;
- unit and integration testing;
- logging for observability;
- reproducible quality checks;
- basic production-readiness practices for Python data pipelines.
