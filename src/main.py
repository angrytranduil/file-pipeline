import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from src.config import (
    DEFAULT_CONTRACT_PATH,
    DEFAULT_INPUT_PATH,
    DEFAULT_METADATA_PATH,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_REJECTED_ROWS_PATH,
    MAX_ERROR_RATE,
    PROJECT_ROOT,
)
from src.data_contract import load_data_contract
from src.exceptions import DataQualityThresholdExceeded
from src.extract import extract_orders
from src.file_metadata import calculate_file_sha256
from src.load import write_json
from src.schemas import ExtractResult, PipelineRunMetadata, RunStatus
from src.transform import calculate_metrics

logger = logging.getLogger(__name__)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Process orders CSV and write aggregated metrics to JSON.")
    )

    parser.add_argument(
        "--contract",
        type=Path,
        default=DEFAULT_CONTRACT_PATH,
        help="Path to the contract JSON file",
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_PATH,
        help="Path to the input orders CSV file",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to the output metrics JSON file",
    )

    parser.add_argument(
        "--rejected-output",
        type=Path,
        default=DEFAULT_REJECTED_ROWS_PATH,
        help="Path to the output rejected rows JSON file",
    )

    parser.add_argument(
        "--metadata-output",
        type=Path,
        default=DEFAULT_METADATA_PATH,
        help="Path to the output pipeline run metadata JSON file",
    )

    parser.add_argument(
        "--max-error-rate",
        type=float,
        default=MAX_ERROR_RATE,
        help="Maximum allowed row-level error rate from 0 to 1",
    )

    return parser.parse_args(args)


def build_run_metadata(
    run_id: str,
    started_at: datetime,
    finished_at: datetime | None,
    status: RunStatus,
    input_path: Path,
    contract_path: Path,
    metrics_output_path: Path,
    rejected_output_path: Path,
    max_error_rate: float,
    extract_result: ExtractResult | None,
    error_message: str | None,
    error_type: str | None,
    input_sha256: str | None,
) -> PipelineRunMetadata:
    if finished_at is None:
        finished_at_iso = None
        duration_seconds = None
    else:
        finished_at_iso = finished_at.isoformat()
        duration_seconds = (finished_at - started_at).total_seconds()

    if extract_result is None:
        total_rows = None
        valid_rows_count = None
        rejected_rows_count = None
        error_rate = None
    else:
        total_rows = extract_result["total_rows"]
        valid_rows_count = extract_result["valid_rows_count"]
        rejected_rows_count = extract_result["rejected_rows_count"]
        error_rate = extract_result["error_rate"]

    return {
        "run_id": run_id,
        "status": status,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at_iso,
        "duration_seconds": duration_seconds,
        "input_path": str(input_path),
        "contract_path": str(contract_path),
        "metrics_output_path": str(metrics_output_path),
        "rejected_output_path": str(rejected_output_path),
        "max_error_rate": max_error_rate,
        "total_rows": total_rows,
        "valid_rows_count": valid_rows_count,
        "rejected_rows_count": rejected_rows_count,
        "error_rate": error_rate,
        "error_type": error_type,
        "error_message": error_message,
        "input_sha256": input_sha256,
    }


def write_run_metadata(
    metadata_output_path: Path,
    metadata: PipelineRunMetadata,
) -> None:
    history_path = metadata_output_path.parent / "runs" / f"{metadata['run_id']}.json"
    write_json(history_path, metadata)
    write_json(metadata_output_path, metadata)


def run_pipeline(
    input_path: Path,
    output_path: Path,
    rejected_output_path: Path,
    max_error_rate: float,
    metadata_output_path: Path,
    contract_path: Path,
) -> PipelineRunMetadata:
    started_at = datetime.now(UTC)
    run_id = str(uuid4())
    extract_result: ExtractResult | None = None
    input_sha256: str | None = None
    metadata = build_run_metadata(
        run_id=run_id,
        status="running",
        started_at=started_at,
        finished_at=None,
        input_path=input_path,
        contract_path=contract_path,
        metrics_output_path=output_path,
        rejected_output_path=rejected_output_path,
        max_error_rate=max_error_rate,
        extract_result=None,
        error_message=None,
        error_type=None,
        input_sha256=input_sha256,
    )
    write_run_metadata(metadata_output_path, metadata)

    try:
        load_data_contract(contract_path)
        input_sha256 = calculate_file_sha256(input_path)

        extract_result = extract_orders(input_path, max_error_rate=max_error_rate)
        write_json(rejected_output_path, extract_result["rejected_rows"])
        metrics = calculate_metrics(extract_result["orders"])
        write_json(output_path, metrics)

        finished_at = datetime.now(UTC)

        logger.info(
            "Data quality summary: total=%s, valid=%s, rejected=%s, error_rate=%.2f%%",
            extract_result["total_rows"],
            extract_result["valid_rows_count"],
            extract_result["rejected_rows_count"],
            extract_result["error_rate"] * 100,
        )

    except Exception as error:
        if isinstance(error, DataQualityThresholdExceeded):
            extract_result = error.extract_result
            write_json(rejected_output_path, extract_result["rejected_rows"])

        finished_at = datetime.now(UTC)
        metadata = build_run_metadata(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status="failed",
            input_path=input_path,
            contract_path=contract_path,
            metrics_output_path=output_path,
            rejected_output_path=rejected_output_path,
            max_error_rate=max_error_rate,
            extract_result=extract_result,
            error_message=str(error),
            error_type=type(error).__name__,
            input_sha256=input_sha256,
        )
        write_run_metadata(metadata_output_path, metadata)
        raise
    else:
        assert extract_result is not None
        metadata = build_run_metadata(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            status="success",
            input_path=input_path,
            contract_path=contract_path,
            metrics_output_path=output_path,
            rejected_output_path=rejected_output_path,
            max_error_rate=max_error_rate,
            extract_result=extract_result,
            error_message=None,
            error_type=None,
            input_sha256=input_sha256,
        )

        write_run_metadata(metadata_output_path, metadata)
        return metadata


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    args = parse_args()
    logger.info("Pipeline started")
    logger.info("Project root: %s", PROJECT_ROOT)
    logger.info("Contract JSON path: %s", args.contract)
    logger.info("Input CSV path: %s", args.input)
    logger.info("Output JSON path: %s", args.output)
    logger.info("Rejected rows JSON path: %s", args.rejected_output)
    logger.info("Run metadata JSON path: %s", args.metadata_output)
    logger.info("Maximum error rate: %.2f%%", args.max_error_rate * 100)

    try:
        run_pipeline(
            input_path=args.input,
            output_path=args.output,
            rejected_output_path=args.rejected_output,
            max_error_rate=args.max_error_rate,
            metadata_output_path=args.metadata_output,
            contract_path=args.contract,
        )
    except FileNotFoundError, OSError, TypeError, ValueError:
        logger.exception("Pipeline failed")
        raise
    else:
        logger.info("Pipeline finished successfully")


if __name__ == "__main__":
    main()
