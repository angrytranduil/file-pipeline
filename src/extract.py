import csv
import logging
from collections.abc import Sequence
from datetime import date
from math import isfinite
from pathlib import Path
from typing import cast

from src.config import ALLOWED_STATUSES, DEFAULT_INPUT_PATH, REQUIRED_COLUMNS
from src.exceptions import DataQualityThresholdExceeded
from src.schemas import ExtractResult, Order, OrderStatus, RawOrderRow, RejectedRow

logger = logging.getLogger(__name__)


def validate_positive_id(value: int, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def require_value(row: RawOrderRow, column: str) -> str:
    value = row.get(column)
    if value is None or not value.strip():
        raise ValueError(f"{column} is required")

    return value.strip()


def parse_order_row(row: RawOrderRow) -> Order:
    order_id = int(require_value(row, "order_id"))
    customer_id = int(require_value(row, "customer_id"))
    validate_positive_id(order_id, "order_id")
    validate_positive_id(customer_id, "customer_id")

    amount = float(require_value(row, "amount"))
    order_date = date.fromisoformat(require_value(row, "order_date")).isoformat()
    status = require_value(row, "status")

    if not isfinite(amount) or amount < 0:
        raise ValueError("amount must be a finite non-negative number")

    if status not in ALLOWED_STATUSES:
        raise ValueError(f"invalid status: {status}")

    status = cast(OrderStatus, status)

    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "order_date": order_date,
        "amount": amount,
        "status": status,
    }


def validate_input_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")


def validate_required_columns(fieldnames: Sequence[str] | None) -> None:
    if fieldnames is None:
        return

    missing_columns = REQUIRED_COLUMNS - set(fieldnames)

    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {missing_columns}")

    if len(fieldnames) != len(set(fieldnames)):
        raise ValueError("CSV contains duplicate columns")


def calculate_error_rate(rejected_rows_count: int, total_rows: int) -> float:
    if total_rows == 0:
        return 0.0

    return rejected_rows_count / total_rows


def validate_max_error_rate(max_error_rate: float) -> None:
    if not 0 <= max_error_rate <= 1:
        raise ValueError("max_error_rate must be between 0 and 1")


def read_orders(path: str | Path) -> list[Order]:
    path = Path(path)
    logger.info("Reading orders from %s", path)

    validate_input_file(path)

    orders: list[Order] = []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        logger.info("CSV columns: %s", reader.fieldnames)

        if reader.fieldnames is None:
            logger.info("CSV file is empty: %s", path)
            return orders

        validate_required_columns(reader.fieldnames)

        for line_number, row in enumerate(reader, start=2):
            try:
                orders.append(parse_order_row(row))
            except (ValueError, TypeError) as error:
                raise ValueError(
                    f"Invalid row at line {line_number}: {row}. Error: {error}"
                ) from error

    logger.info("Read %s valid orders", len(orders))
    return orders


def extract_orders(path: str | Path, max_error_rate: float) -> ExtractResult:
    path = Path(path)
    logger.info("Extracting orders from %s", path)

    validate_max_error_rate(max_error_rate)
    validate_input_file(path)

    orders: list[Order] = []
    rejected_rows: list[RejectedRow] = []
    total_rows = 0

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        logger.info("CSV columns: %s", reader.fieldnames)

        if reader.fieldnames is None:
            logger.info("CSV file is empty: %s", path)
            return {
                "orders": [],
                "rejected_rows": [],
                "total_rows": 0,
                "valid_rows_count": 0,
                "rejected_rows_count": 0,
                "error_rate": 0.0,
            }

        validate_required_columns(reader.fieldnames)

        for line_number, row in enumerate(reader, start=2):
            total_rows += 1

            try:
                orders.append(parse_order_row(row))
            except (ValueError, TypeError) as error:
                rejected_rows.append(
                    {
                        "line_number": line_number,
                        "row": row,
                        "error": str(error),
                    }
                )

    rejected_rows_count = len(rejected_rows)
    valid_rows_count = len(orders)
    error_rate = calculate_error_rate(rejected_rows_count, total_rows)

    extract_result: ExtractResult = {
        "orders": orders,
        "rejected_rows": rejected_rows,
        "total_rows": total_rows,
        "valid_rows_count": valid_rows_count,
        "rejected_rows_count": rejected_rows_count,
        "error_rate": error_rate,
    }

    if error_rate > max_error_rate:
        raise DataQualityThresholdExceeded(
            error_rate=error_rate,
            max_error_rate=max_error_rate,
            extract_result=extract_result,
        )

    logger.info(
        "Extracted %s valid orders and %s rejected rows from %s total rows",
        valid_rows_count,
        rejected_rows_count,
        total_rows,
    )

    return extract_result


if __name__ == "__main__":
    print(read_orders(DEFAULT_INPUT_PATH))
