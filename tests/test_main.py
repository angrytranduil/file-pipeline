from datetime import UTC, datetime
from pathlib import Path

from src.config import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_INPUT_PATH,
    DEFAULT_METADATA_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_REJECTED_ROWS_PATH,
    MAX_ERROR_RATE,
)
from src.main import build_run_metadata, parse_args
from src.schemas import ExtractResult


def test_parse_args_uses_default_paths():
    args = parse_args([])

    assert args.input == DEFAULT_INPUT_PATH
    assert args.output == DEFAULT_OUTPUT_PATH
    assert args.rejected_output == DEFAULT_REJECTED_ROWS_PATH
    assert args.metadata_output == DEFAULT_METADATA_PATH
    assert args.max_error_rate == MAX_ERROR_RATE
    assert args.contract == DEFAULT_CONTRACT_PATH


def test_parse_args_uses_custom_paths():
    args = parse_args(
        [
            "--input",
            "data/raw/custom_orders.csv",
            "--output",
            "data/processed/custom_metrics.json",
            "--rejected-output",
            "data/rejected/custom_rejected_orders.json",
            "--metadata-output",
            "data/processed/custom_run_metadata.json",
            "--max-error-rate",
            "0.2",
        ]
    )

    assert args.input == Path("data/raw/custom_orders.csv")
    assert args.output == Path("data/processed/custom_metrics.json")
    assert args.rejected_output == Path("data/rejected/custom_rejected_orders.json")
    assert args.metadata_output == Path("data/processed/custom_run_metadata.json")
    assert args.max_error_rate == 0.2


def test_parse_args_allows_contract_override_only():
    args = parse_args(["--contract", "data/rejected/custom_rejected.json"])

    assert args.input == DEFAULT_INPUT_PATH
    assert args.output == DEFAULT_OUTPUT_PATH
    assert args.rejected_output == DEFAULT_REJECTED_ROWS_PATH
    assert args.contract == Path("data/rejected/custom_rejected.json")
    assert args.metadata_output == DEFAULT_METADATA_PATH
    assert args.max_error_rate == MAX_ERROR_RATE


def test_parse_args_allows_input_override_only():
    args = parse_args(["--input", "data/raw/custom_orders.csv"])
    assert args.input == Path("data/raw/custom_orders.csv")
    assert args.output == DEFAULT_OUTPUT_PATH
    assert args.rejected_output == DEFAULT_REJECTED_ROWS_PATH
    assert args.metadata_output == DEFAULT_METADATA_PATH
    assert args.max_error_rate == MAX_ERROR_RATE


def test_parse_args_allows_output_override_only():
    args = parse_args(["--output", "data/processed/custom_metrics.json"])
    assert args.input == DEFAULT_INPUT_PATH
    assert args.output == Path("data/processed/custom_metrics.json")
    assert args.rejected_output == DEFAULT_REJECTED_ROWS_PATH
    assert args.metadata_output == DEFAULT_METADATA_PATH
    assert args.max_error_rate == MAX_ERROR_RATE


def test_parse_args_allows_rejected_output_override_only():
    args = parse_args(["--rejected-output", "data/rejected/custom_rejected.json"])

    assert args.input == DEFAULT_INPUT_PATH
    assert args.output == DEFAULT_OUTPUT_PATH
    assert args.rejected_output == Path("data/rejected/custom_rejected.json")
    assert args.metadata_output == DEFAULT_METADATA_PATH
    assert args.max_error_rate == MAX_ERROR_RATE


def test_parse_args_allows_metadata_output_override_only():
    args = parse_args(["--metadata-output", "data/processed/custom_metadata.json"])

    assert args.input == DEFAULT_INPUT_PATH
    assert args.output == DEFAULT_OUTPUT_PATH
    assert args.rejected_output == DEFAULT_REJECTED_ROWS_PATH
    assert args.metadata_output == Path("data/processed/custom_metadata.json")
    assert args.max_error_rate == MAX_ERROR_RATE


def test_parse_args_allows_max_error_rate_override_only():
    args = parse_args(["--max-error-rate", "0.15"])

    assert args.input == DEFAULT_INPUT_PATH
    assert args.output == DEFAULT_OUTPUT_PATH
    assert args.rejected_output == DEFAULT_REJECTED_ROWS_PATH
    assert args.metadata_output == DEFAULT_METADATA_PATH
    assert args.max_error_rate == 0.15


def test_build_run_metadata_returns_success_metadata():
    started_at = datetime(2026, 9, 8, 10, 0, 0, tzinfo=UTC)
    finished_at = datetime(2026, 9, 8, 10, 0, 2, tzinfo=UTC)
    extract_result: ExtractResult = {
        "orders": [
            {
                "order_id": 1,
                "customer_id": 101,
                "order_date": "2026-09-08",
                "amount": 100.0,
                "status": "paid",
            },
            {
                "order_id": 2,
                "customer_id": 102,
                "order_date": "2026-09-08",
                "amount": 50.0,
                "status": "cancelled",
            },
        ],
        "rejected_rows": [
            {
                "line_number": 4,
                "row": {
                    "order_id": "bad_id",
                    "customer_id": "103",
                    "order_date": "2026-09-08",
                    "amount": "75.0",
                    "status": "paid",
                },
                "error": "invalid order_id",
            }
        ],
        "total_rows": 3,
        "valid_rows_count": 2,
        "rejected_rows_count": 1,
        "error_rate": 1 / 3,
    }
    run_id = "test-run-id"
    metadata = build_run_metadata(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        status="success",
        input_path=DEFAULT_INPUT_PATH,
        contract_path=DEFAULT_CONTRACT_PATH,
        metrics_output_path=DEFAULT_OUTPUT_PATH,
        rejected_output_path=DEFAULT_REJECTED_ROWS_PATH,
        max_error_rate=MAX_ERROR_RATE,
        extract_result=extract_result,
        error_message=None,
        error_type=None,
        input_sha256="test-sha256",
    )

    assert metadata["run_id"] == run_id
    assert metadata["status"] == "success"
    assert metadata["started_at"] == started_at.isoformat()
    assert metadata["finished_at"] == finished_at.isoformat()
    assert metadata["duration_seconds"] == 2.0
    assert metadata["input_path"] == str(DEFAULT_INPUT_PATH)
    assert metadata["contract_path"] == str(DEFAULT_CONTRACT_PATH)
    assert metadata["metrics_output_path"] == str(DEFAULT_OUTPUT_PATH)
    assert metadata["rejected_output_path"] == str(DEFAULT_REJECTED_ROWS_PATH)
    assert metadata["max_error_rate"] == MAX_ERROR_RATE
    assert metadata["total_rows"] == 3
    assert metadata["valid_rows_count"] == 2
    assert metadata["rejected_rows_count"] == 1
    assert metadata["error_rate"] == 1 / 3
    assert metadata["error_message"] is None
    assert metadata["error_type"] is None
    assert metadata["input_sha256"] == "test-sha256"


def test_build_run_metadata_returns_running_metadata():
    started_at = datetime(2026, 9, 8, 10, 0, 0, tzinfo=UTC)

    metadata = build_run_metadata(
        run_id="test-running-id",
        started_at=started_at,
        finished_at=None,
        status="running",
        input_path=DEFAULT_INPUT_PATH,
        contract_path=DEFAULT_CONTRACT_PATH,
        metrics_output_path=DEFAULT_OUTPUT_PATH,
        rejected_output_path=DEFAULT_REJECTED_ROWS_PATH,
        max_error_rate=MAX_ERROR_RATE,
        extract_result=None,
        error_message=None,
        error_type=None,
        input_sha256=None,
    )

    assert metadata["run_id"] == "test-running-id"
    assert metadata["status"] == "running"
    assert metadata["started_at"] == started_at.isoformat()
    assert metadata["finished_at"] is None
    assert metadata["duration_seconds"] is None
    assert metadata["contract_path"] == str(DEFAULT_CONTRACT_PATH)
    assert metadata["total_rows"] is None
    assert metadata["valid_rows_count"] is None
    assert metadata["rejected_rows_count"] is None
    assert metadata["error_rate"] is None
    assert metadata["error_message"] is None
    assert metadata["error_type"] is None
    assert metadata["input_sha256"] is None
