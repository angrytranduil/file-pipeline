import pytest

from src.exceptions import DataQualityThresholdExceeded
from src.extract import extract_orders, read_orders, validate_positive_id


def test_validate_positive_id_accepts_positive_value():
    result = validate_positive_id(1, "order_id")

    assert result is None


@pytest.mark.parametrize("value", [0, -5])
def test_validate_positive_id_rejects_non_positive_value(value):
    with pytest.raises(ValueError, match="customer_id must be positive"):
        validate_positive_id(value, "customer_id")


def test_read_orders_from_valid_csv(tmp_path):
    file_path = tmp_path / "orders.csv"
    csv_content = """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,250.50,paid
2,102,2026-09-01,99.90,cancelled"""
    file_path.write_text(csv_content, encoding="utf-8")

    orders = read_orders(file_path)

    assert orders == [
        {
            "order_id": 1,
            "customer_id": 101,
            "order_date": "2026-09-01",
            "amount": 250.50,
            "status": "paid",
        },
        {
            "order_id": 2,
            "customer_id": 102,
            "order_date": "2026-09-01",
            "amount": 99.90,
            "status": "cancelled",
        },
    ]


def test_read_orders_raises_error_for_missing_file(tmp_path):
    file_path = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        read_orders(file_path)


def test_read_orders_raises_error_for_missing_required_column(tmp_path):
    csv_content = """order_id,customer_id,order_date,amount
1,101,2026-09-01,250.50"""
    file_path = tmp_path / "some.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(ValueError, match="missing required columns"):
        read_orders(file_path)


def test_read_orders_raises_error_for_invalid_amount(tmp_path):
    csv_content = """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,abc,paid"""
    file_path = tmp_path / "some.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid row at line 2"):
        read_orders(file_path)


@pytest.mark.parametrize(
    ("row", "expected_message"),
    [
        ("0,101,2026-09-01,10,paid", "order_id must be positive"),
        (
            "1,-101,2026-09-01,10,paid",
            "customer_id must be positive",
        ),
    ],
)
def test_read_orders_rejects_non_positive_identifiers(tmp_path, row, expected_message):
    file_path = tmp_path / "orders.csv"
    csv_content = f"""order_id,customer_id,order_date,amount,status
{row}"""
    file_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(ValueError, match=expected_message):
        read_orders(file_path)


def test_read_orders_raises_error_for_negative_amount(tmp_path):
    csv_content = """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,-10,paid"""
    file_path = tmp_path / "some.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(ValueError, match="amount must be a finite non-negative number"):
        read_orders(file_path)


@pytest.mark.parametrize("amount", ["nan", "inf", "-inf"])
def test_read_orders_rejects_non_finite_amount(tmp_path, amount):
    csv_content = f"""order_id,customer_id,order_date,amount,status
1,101,2026-09-01,{amount},paid"""
    file_path = tmp_path / "some.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(ValueError, match="amount must be a finite non-negative number"):
        read_orders(file_path)


def test_read_orders_raises_error_for_unknown_status(tmp_path):
    csv_content = """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,10,unknown"""
    file_path = tmp_path / "some.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(ValueError, match="invalid status"):
        read_orders(file_path)


def test_read_orders_raises_error_for_invalid_order_date(tmp_path):
    csv_content = """order_id,customer_id,order_date,amount,status
1,101,not-a-date,250.50,paid"""
    file_path = tmp_path / "some.csv"
    file_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid row at line 2"):
        read_orders(file_path)


def test_extract_orders_returns_valid_orders_without_rejections(tmp_path):
    file_path = tmp_path / "orders.csv"
    csv_content = """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,250.50,paid
2,102,2026-09-01,99.90,cancelled"""
    file_path.write_text(csv_content, encoding="utf-8")

    result = extract_orders(file_path, max_error_rate=0.0)

    assert result["total_rows"] == 2
    assert result["valid_rows_count"] == 2
    assert result["rejected_rows_count"] == 0
    assert result["error_rate"] == 0.0
    assert result["rejected_rows"] == []
    assert result["orders"] == [
        {
            "order_id": 1,
            "customer_id": 101,
            "order_date": "2026-09-01",
            "amount": 250.50,
            "status": "paid",
        },
        {
            "order_id": 2,
            "customer_id": 102,
            "order_date": "2026-09-01",
            "amount": 99.90,
            "status": "cancelled",
        },
    ]


def test_extract_orders_collects_rejected_rows(tmp_path):
    file_path = tmp_path / "orders.csv"
    csv_content = """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,250.50,paid
2,102,2026-09-01,abc,paid
3,103,2026-09-01,100.00,cancelled"""
    file_path.write_text(csv_content, encoding="utf-8")

    result = extract_orders(file_path, max_error_rate=0.5)

    assert result["total_rows"] == 3
    assert result["valid_rows_count"] == 2
    assert result["rejected_rows_count"] == 1
    assert result["error_rate"] == 1 / 3
    assert len(result["orders"]) == 2
    assert result["rejected_rows"][0]["line_number"] == 3
    assert result["rejected_rows"][0]["row"] == {
        "order_id": "2",
        "customer_id": "102",
        "order_date": "2026-09-01",
        "amount": "abc",
        "status": "paid",
    }
    assert "could not convert string to float" in result["rejected_rows"][0]["error"]


def test_extract_orders_raises_error_when_error_rate_exceeds_threshold(tmp_path):
    file_path = tmp_path / "orders.csv"
    csv_content = """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,250.50,paid
2,102,2026-09-01,abc,paid
3,103,2026-09-01,100.00,cancelled"""
    file_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(
        DataQualityThresholdExceeded, match="exceeds maximum allowed"
    ) as exc_info:
        extract_orders(file_path, max_error_rate=0.1)

    assert exc_info.value.extract_result["total_rows"] == 3
    assert exc_info.value.extract_result["valid_rows_count"] == 2
    assert exc_info.value.extract_result["rejected_rows_count"] == 1


def test_extract_orders_rejects_row_with_missing_value(tmp_path):
    file_path = tmp_path / "orders.csv"
    csv_content = """order_id,customer_id,order_date,amount,status
1,101,2026-09-01,250.50"""
    file_path.write_text(csv_content, encoding="utf-8")

    result = extract_orders(file_path, max_error_rate=1.0)

    assert result["total_rows"] == 1
    assert result["valid_rows_count"] == 0
    assert result["rejected_rows_count"] == 1
    assert "status is required" in result["rejected_rows"][0]["error"]


def test_read_orders_raises_error_for_duplicate_columns(tmp_path):
    file_path = tmp_path / "orders.csv"
    csv_content = """order_id,customer_id,order_date,amount,status,status
1,101,2026-09-01,250.50,paid,paid"""
    file_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate columns"):
        read_orders(file_path)


def test_extract_orders_returns_empty_result_for_empty_csv(tmp_path):
    file_path = tmp_path / "orders.csv"
    csv_content = "order_id,customer_id,order_date,amount,status\n"
    file_path.write_text(csv_content, encoding="utf-8")

    result = extract_orders(file_path, max_error_rate=0.0)

    assert result == {
        "orders": [],
        "rejected_rows": [],
        "total_rows": 0,
        "valid_rows_count": 0,
        "rejected_rows_count": 0,
        "error_rate": 0.0,
    }


def test_extract_orders_raises_error_for_negative_max_error_rate(tmp_path):
    file_path = tmp_path / "orders.csv"
    csv_content = "order_id,customer_id,order_date,amount,status\n"
    file_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(ValueError, match="max_error_rate must be between 0 and 1"):
        extract_orders(file_path, max_error_rate=-0.1)


def test_extract_orders_raises_error_for_max_error_rate_greater_than_one(tmp_path):
    file_path = tmp_path / "orders.csv"
    csv_content = "order_id,customer_id,order_date,amount,status\n"
    file_path.write_text(csv_content, encoding="utf-8")

    with pytest.raises(ValueError, match="max_error_rate must be between 0 and 1"):
        extract_orders(file_path, max_error_rate=1.1)
