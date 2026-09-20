import json

from src.load import write_json


def test_write_json_creates_file(tmp_path):
    file_path = tmp_path / "metrics.json"
    data = {
        "orders_count": 5,
        "average_paid_amount": 223.5,
    }

    write_json(file_path, data)

    assert file_path.is_file()


def test_write_json_writes_expected_data(tmp_path):
    file_path = tmp_path / "metrics.json"
    data = {
        "orders_count": 5,
        "average_paid_amount": 223.5,
    }
    write_json(file_path, data)

    with file_path.open("r", encoding="utf-8") as file:
        actual_data = json.load(file)

    assert actual_data == data


def test_write_json_creates_parent_directory(tmp_path):
    file_path = tmp_path / "processed" / "metrics.json"
    data = {
        "orders_count": 5,
        "average_paid_amount": 223.5,
    }

    write_json(file_path, data)

    assert file_path.parent.is_dir()
    assert file_path.is_file()


def test_write_json_preserves_none_value(tmp_path):
    file_path = tmp_path / "metrics.json"
    data = {
        "orders_count": 0,
        "average_paid_amount": None,
    }

    write_json(file_path, data)

    with file_path.open("r", encoding="utf-8") as file:
        actual_data = json.load(file)

    assert actual_data["average_paid_amount"] is None
