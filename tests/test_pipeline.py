import json
from pathlib import Path
from uuid import UUID

import pytest

from src.config import DEFAULT_CONTRACT_PATH, MAX_ERROR_RATE
from src.exceptions import DataContractValidationError, DataQualityThresholdExceeded
from src.file_metadata import calculate_file_sha256
from src.main import run_pipeline


@pytest.fixture
def valid_contract_path(tmp_path: Path) -> Path:
    contract_path = tmp_path / "orders_v1.json"
    contract_contents = DEFAULT_CONTRACT_PATH.read_text(encoding="utf-8")
    contract_path.write_text(contract_contents, encoding="utf-8")
    return contract_path


def test_pipeline_fail_when_input_not_exists(
    tmp_path: Path,
    valid_contract_path: Path,
) -> None:
    input_path = tmp_path / "no_such_dir" / "orders.csv"
    output_path = tmp_path / "output.py"
    rejected_rows_path = tmp_path / "rejected.py"
    metadata_path = tmp_path / "metadata.py"

    with pytest.raises(FileNotFoundError):
        run_pipeline(
            input_path=input_path,
            output_path=output_path,
            rejected_output_path=rejected_rows_path,
            max_error_rate=MAX_ERROR_RATE,
            metadata_output_path=metadata_path,
            contract_path=valid_contract_path,
        )
    with metadata_path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)
        assert metadata["status"] == "failed"
        assert metadata["error_message"] is not None
        assert metadata["total_rows"] is None
        assert metadata["valid_rows_count"] is None
        assert metadata["rejected_rows_count"] is None
        assert metadata["error_rate"] is None
        assert metadata["input_sha256"] is None
        assert metadata["error_type"] == "FileNotFoundError"


def test_pipeline_processes_orders_csv_and_writes_metrics_json(
    tmp_path: Path,
    valid_contract_path: Path,
) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "order_metrics.json"
    rejected_output_path = tmp_path / "rejected_orders.json"
    metadata_output_path = tmp_path / "run_metadata.json"

    csv_contents = """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,250.50,paid
2,102,2026-09-01,99.90,paid
3,103,2026-09-02,180.00,cancelled
4,104,2026-09-02,320.10,paid
5,105,2026-09-03,15.00,failed"""
    input_path.write_text(csv_contents, encoding="utf-8")

    run_pipeline(
        input_path=input_path,
        output_path=output_path,
        rejected_output_path=rejected_output_path,
        max_error_rate=0.0,
        metadata_output_path=metadata_output_path,
        contract_path=valid_contract_path,
    )

    with output_path.open("r", encoding="utf-8") as file:
        actual_metrics = json.load(file)

    with rejected_output_path.open("r", encoding="utf-8") as file:
        rejected_rows = json.load(file)

    with metadata_output_path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    assert actual_metrics == {
        "orders_count": 5,
        "paid_orders_count": 3,
        "cancelled_orders_count": 1,
        "failed_orders_count": 1,
        "total_amount": 865.5,
        "paid_amount": 670.5,
        "average_paid_amount": 223.5,
    }
    assert rejected_rows == []
    assert metadata["status"] == "success"
    assert metadata["input_path"] == str(input_path)
    assert metadata["metrics_output_path"] == str(output_path)
    assert metadata["rejected_output_path"] == str(rejected_output_path)
    assert metadata["max_error_rate"] == 0.0
    assert metadata["total_rows"] == 5
    assert metadata["valid_rows_count"] == 5
    assert metadata["rejected_rows_count"] == 0
    assert metadata["error_rate"] == 0.0
    assert metadata["error_message"] is None
    assert metadata["input_sha256"] == calculate_file_sha256(input_path)
    assert metadata["duration_seconds"] >= 0
    assert str(UUID(metadata["run_id"])) == metadata["run_id"]
    assert metadata["finished_at"] >= metadata["started_at"]


def test_pipeline_writes_metrics_and_rejected_rows_for_invalid_input_rows(
    tmp_path: Path,
    valid_contract_path: Path,
) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "order_metrics.json"
    rejected_output_path = tmp_path / "rejected_orders.json"
    metadata_output_path = tmp_path / "run_metadata.json"

    csv_contents = """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,250.50,paid
2,102,2026-09-01,abc,paid
3,103,2026-09-02,180.00,cancelled"""
    input_path.write_text(csv_contents, encoding="utf-8")

    run_pipeline(
        input_path=input_path,
        output_path=output_path,
        rejected_output_path=rejected_output_path,
        max_error_rate=0.5,
        metadata_output_path=metadata_output_path,
        contract_path=valid_contract_path,
    )

    with output_path.open("r", encoding="utf-8") as file:
        actual_metrics = json.load(file)

    with rejected_output_path.open("r", encoding="utf-8") as file:
        rejected_rows = json.load(file)

    with metadata_output_path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    assert actual_metrics == {
        "orders_count": 2,
        "paid_orders_count": 1,
        "cancelled_orders_count": 1,
        "failed_orders_count": 0,
        "total_amount": 430.5,
        "paid_amount": 250.5,
        "average_paid_amount": 250.5,
    }
    assert rejected_rows == [
        {
            "line_number": 3,
            "row": {
                "order_id": "2",
                "customer_id": "102",
                "order_date": "2026-09-01",
                "amount": "abc",
                "status": "paid",
            },
            "error": "could not convert string to float: 'abc'",
        }
    ]
    assert metadata["status"] == "success"
    assert metadata["total_rows"] == 3
    assert metadata["valid_rows_count"] == 2
    assert metadata["rejected_rows_count"] == 1
    assert metadata["error_rate"] == 1 / 3
    assert metadata["error_message"] is None
    assert metadata["input_sha256"] == calculate_file_sha256(input_path)


def test_pipeline_records_input_sha256_when_quality_threshold_is_exceeded(
    tmp_path: Path,
    valid_contract_path: Path,
) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "order_metrics.json"
    rejected_output_path = tmp_path / "rejected_orders.json"
    metadata_output_path = tmp_path / "run_metadata.json"
    input_path.write_text(
        """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,invalid,paid""",
        encoding="utf-8",
    )

    with pytest.raises(DataQualityThresholdExceeded):
        run_pipeline(
            input_path=input_path,
            output_path=output_path,
            rejected_output_path=rejected_output_path,
            max_error_rate=0.0,
            metadata_output_path=metadata_output_path,
            contract_path=valid_contract_path,
        )

    with metadata_output_path.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    assert metadata["status"] == "failed"
    assert metadata["input_sha256"] == calculate_file_sha256(input_path)
    assert metadata["error_type"] == "DataQualityThresholdExceeded"


def test_pipeline_records_invalid_json_contract_failure(tmp_path: Path) -> None:
    input_path = tmp_path / "orders.csv"
    contract_path = tmp_path / "invalid_contract.json"
    output_path = tmp_path / "order_metrics.json"
    rejected_output_path = tmp_path / "rejected_orders.json"
    metadata_output_path = tmp_path / "run_metadata.json"

    input_path.write_text(
        """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,100.00,paid""",
        encoding="utf-8",
    )

    contract_path.write_text(
        '{"fields"',
        encoding="utf-8",
    )

    with pytest.raises(json.JSONDecodeError) as exc_info:
        run_pipeline(
            input_path=input_path,
            output_path=output_path,
            rejected_output_path=rejected_output_path,
            max_error_rate=0.0,
            metadata_output_path=metadata_output_path,
            contract_path=contract_path,
        )

    with metadata_output_path.open(encoding="utf-8") as file:
        metadata = json.load(file)

    history_directory = metadata_output_path.parent / "runs"
    history_paths = list(history_directory.glob("*.json"))

    assert metadata["status"] == "failed"
    assert metadata["contract_path"] == str(contract_path)
    assert metadata["error_type"] == "JSONDecodeError"
    assert metadata["error_message"] == str(exc_info.value)
    assert metadata["input_sha256"] is None
    assert metadata["total_rows"] is None
    assert metadata["valid_rows_count"] is None
    assert metadata["rejected_rows_count"] is None
    assert metadata["error_rate"] is None
    assert not output_path.exists()
    assert not rejected_output_path.exists()
    assert len(history_paths) == 1

    with history_paths[0].open(encoding="utf-8") as file:
        history_metadata = json.load(file)

    # History и latest должны описывать один запуск.
    assert history_metadata["run_id"] == metadata["run_id"]
    assert history_metadata["status"] == metadata["status"]


def test_pipeline_records_missing_contract_failure(tmp_path: Path) -> None:
    input_path = tmp_path / "orders.csv"
    contract_path = tmp_path / "missing_contract.json"
    output_path = tmp_path / "order_metrics.json"
    rejected_output_path = tmp_path / "rejected_orders.json"
    metadata_output_path = tmp_path / "run_metadata.json"
    input_path.write_text(
        """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,100.00,paid""",
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError) as exc_info:
        run_pipeline(
            input_path=input_path,
            output_path=output_path,
            rejected_output_path=rejected_output_path,
            max_error_rate=0.0,
            metadata_output_path=metadata_output_path,
            contract_path=contract_path,
        )

    with metadata_output_path.open(encoding="utf-8") as file:
        metadata = json.load(file)

    history_path = metadata_output_path.parent / "runs" / f"{metadata['run_id']}.json"
    with history_path.open(encoding="utf-8") as file:
        history_metadata = json.load(file)

    assert metadata["status"] == "failed"
    assert metadata["contract_path"] == str(contract_path)
    assert metadata["error_type"] == "FileNotFoundError"
    assert metadata["error_message"] == str(exc_info.value)
    assert metadata["input_sha256"] is None
    assert metadata["total_rows"] is None
    assert metadata["valid_rows_count"] is None
    assert metadata["rejected_rows_count"] is None
    assert metadata["error_rate"] is None
    assert not output_path.exists()
    assert not rejected_output_path.exists()
    assert history_metadata == metadata


def test_pipeline_validates_contract_before_reading_input(tmp_path: Path) -> None:
    input_path = tmp_path / "missing_orders.csv"
    contract_path = tmp_path / "invalid_contract.json"
    output_path = tmp_path / "order_metrics.json"
    rejected_output_path = tmp_path / "rejected_orders.json"
    metadata_output_path = tmp_path / "run_metadata.json"
    invalid_contract = json.loads(DEFAULT_CONTRACT_PATH.read_text(encoding="utf-8"))
    invalid_contract["fields"] = {}
    contract_path.write_text(json.dumps(invalid_contract), encoding="utf-8")

    with pytest.raises(DataContractValidationError) as exc_info:
        run_pipeline(
            input_path=input_path,
            output_path=output_path,
            rejected_output_path=rejected_output_path,
            max_error_rate=0.0,
            metadata_output_path=metadata_output_path,
            contract_path=contract_path,
        )

    with metadata_output_path.open(encoding="utf-8") as file:
        metadata = json.load(file)

    assert metadata["status"] == "failed"
    assert metadata["error_type"] == "DataContractValidationError"
    assert metadata["error_message"] == str(exc_info.value)
    assert metadata["input_sha256"] is None
    assert metadata["total_rows"] is None
    assert metadata["valid_rows_count"] is None
    assert metadata["rejected_rows_count"] is None
    assert metadata["error_rate"] is None
    assert not output_path.exists()
    assert not rejected_output_path.exists()


def test_pipeline_succeeds_after_contract_is_fixed(
    tmp_path: Path,
    valid_contract_path: Path,
) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "order_metrics.json"
    rejected_output_path = tmp_path / "rejected_orders.json"
    metadata_output_path = tmp_path / "run_metadata.json"
    input_path.write_text(
        """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,100.00,paid""",
        encoding="utf-8",
    )
    valid_contract_contents = valid_contract_path.read_text(encoding="utf-8")
    valid_contract_path.write_text('{"fields"', encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        run_pipeline(
            input_path=input_path,
            output_path=output_path,
            rejected_output_path=rejected_output_path,
            max_error_rate=0.0,
            metadata_output_path=metadata_output_path,
            contract_path=valid_contract_path,
        )

    with metadata_output_path.open(encoding="utf-8") as file:
        failed_metadata = json.load(file)

    assert failed_metadata["status"] == "failed"
    assert failed_metadata["error_type"] == "JSONDecodeError"
    assert failed_metadata["input_sha256"] is None
    assert not output_path.exists()
    assert not rejected_output_path.exists()

    valid_contract_path.write_text(valid_contract_contents, encoding="utf-8")
    returned_metadata = run_pipeline(
        input_path=input_path,
        output_path=output_path,
        rejected_output_path=rejected_output_path,
        max_error_rate=0.0,
        metadata_output_path=metadata_output_path,
        contract_path=valid_contract_path,
    )

    with metadata_output_path.open(encoding="utf-8") as file:
        latest_metadata = json.load(file)

    failed_history_path = (
        metadata_output_path.parent / "runs" / f"{failed_metadata['run_id']}.json"
    )
    success_history_path = (
        metadata_output_path.parent / "runs" / f"{returned_metadata['run_id']}.json"
    )
    with failed_history_path.open(encoding="utf-8") as file:
        failed_history_metadata = json.load(file)
    with success_history_path.open(encoding="utf-8") as file:
        success_history_metadata = json.load(file)

    assert failed_metadata["run_id"] != returned_metadata["run_id"]
    assert failed_metadata["contract_path"] == returned_metadata["contract_path"]
    assert returned_metadata["status"] == "success"
    assert returned_metadata["error_type"] is None
    assert returned_metadata["error_message"] is None
    assert returned_metadata["input_sha256"] == calculate_file_sha256(input_path)
    assert latest_metadata == returned_metadata
    assert failed_history_metadata == failed_metadata
    assert success_history_metadata == returned_metadata
    assert len(list((metadata_output_path.parent / "runs").glob("*.json"))) == 2
    assert output_path.is_file()
    assert rejected_output_path.is_file()


def test_contract_preflight_failure_does_not_modify_existing_outputs(
    tmp_path: Path,
    valid_contract_path: Path,
) -> None:
    input_path = tmp_path / "orders.csv"
    output_path = tmp_path / "order_metrics.json"
    rejected_output_path = tmp_path / "rejected_orders.json"
    metadata_output_path = tmp_path / "run_metadata.json"
    input_path.write_text(
        """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,100.00,paid""",
        encoding="utf-8",
    )

    success_metadata = run_pipeline(
        input_path=input_path,
        output_path=output_path,
        rejected_output_path=rejected_output_path,
        max_error_rate=0.0,
        metadata_output_path=metadata_output_path,
        contract_path=valid_contract_path,
    )
    metrics_before_failure = output_path.read_bytes()
    rejected_rows_before_failure = rejected_output_path.read_bytes()
    valid_contract_path.write_text('{"fields"', encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        run_pipeline(
            input_path=input_path,
            output_path=output_path,
            rejected_output_path=rejected_output_path,
            max_error_rate=0.0,
            metadata_output_path=metadata_output_path,
            contract_path=valid_contract_path,
        )

    with metadata_output_path.open(encoding="utf-8") as file:
        failed_metadata = json.load(file)

    assert failed_metadata["run_id"] != success_metadata["run_id"]
    assert failed_metadata["status"] == "failed"
    assert failed_metadata["error_type"] == "JSONDecodeError"
    assert output_path.read_bytes() == metrics_before_failure
    assert rejected_output_path.read_bytes() == rejected_rows_before_failure
    assert len(list((metadata_output_path.parent / "runs").glob("*.json"))) == 2
