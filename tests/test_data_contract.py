import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from src.config import ALLOWED_STATUSES, PROJECT_ROOT, REQUIRED_COLUMNS
from src.data_contract import load_data_contract
from src.exceptions import DataContractValidationError
from src.schemas import DataContract


@pytest.fixture(scope="module")
def orders_contract() -> DataContract:
    contract_path = PROJECT_ROOT / "contracts" / "orders_v1.json"

    with contract_path.open(encoding="utf-8") as file:
        return cast(DataContract, json.load(file))


def test_data_contract_required_fields(
    orders_contract: DataContract,
) -> None:
    contract_fields = set(orders_contract["fields"])

    assert contract_fields == REQUIRED_COLUMNS


def test_allowed_statuses_from_contract(
    orders_contract: DataContract,
) -> None:
    statuses = set(orders_contract["fields"]["status"]["allowed_statuses"])

    assert statuses == ALLOWED_STATUSES


@pytest.mark.parametrize(
    "field_name",
    [
        "order_id",
        "customer_id",
        "order_date",
        "amount",
        "status",
    ],
)
def test_contract_fields_are_required_and_not_nullable(
    orders_contract: DataContract,
    field_name: str,
) -> None:
    field_contract = orders_contract["fields"][field_name]

    assert field_contract["required"] is True
    assert field_contract["nullable"] is False


@pytest.mark.parametrize(
    "field_name_with_min, minimum",
    [
        ("order_id", 1),
        ("customer_id", 1),
        ("amount", 0),
    ],
)
def test_contract_fields_with_minimum(
    orders_contract: DataContract,
    field_name_with_min: str,
    minimum: int,
) -> None:
    field_contract = orders_contract["fields"][field_name_with_min]

    assert field_contract["minimum"] == minimum


def test_contract_main_field_values(orders_contract: DataContract) -> None:
    assert orders_contract["version"] == 1
    assert orders_contract["format"] == "csv"
    assert orders_contract["encoding"] == "utf-8-sig"
    assert orders_contract["allow_extra_fields"] is True


@pytest.mark.parametrize(
    "field_name, expected_type",
    [
        ("order_id", "integer"),
        ("customer_id", "integer"),
        ("order_date", "date"),
        ("amount", "float"),
        ("status", "string"),
    ],
)
def test_contract_field_types_match(
    orders_contract: DataContract, field_name: str, expected_type: str
) -> None:
    field_contract = orders_contract["fields"][field_name]
    assert field_contract["type"] == expected_type


def test_load_data_contract_rejects_non_integer_version(tmp_path) -> None:
    contract_path = tmp_path / "contract.json"
    contract_path.write_text(
        json.dumps(
            {
                "version": "one",
                "fields": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        DataContractValidationError,
        match=r"contract\.version must be an integer",
    ):
        load_data_contract(contract_path)


@pytest.mark.parametrize(
    ("field_name", "wrong_value", "expected_error"),
    [
        pytest.param(
            "allow_extra_fields",
            "true",
            r"contract\.allow_extra_fields must be boolean",
            id="allow-extra-fields-is-string",
        ),
        pytest.param(
            "version",
            0,
            r"contract\.version must be positive",
            id="version-is-zero",
        ),
        pytest.param(
            "fields",
            [],
            r"contract\.fields must be a dictionary",
            id="fields-is-list",
        ),
    ],
)
def test_load_data_contract_wrong_structure(
    orders_contract: DataContract,
    tmp_path: Path,
    field_name: str,
    wrong_value: Any,
    expected_error: str,
) -> None:
    wrong_contract = deepcopy(orders_contract)
    wrong_contract[field_name] = wrong_value

    contract_path = tmp_path / "data_contract.json"
    contract_path.write_text(
        json.dumps(wrong_contract),
        encoding="utf-8",
    )

    with pytest.raises(DataContractValidationError, match=expected_error):
        load_data_contract(contract_path)


def test_load_data_contract_rejects_list_root(
    tmp_path: Path,
) -> None:
    contract_path = tmp_path / "data_contract.json"
    contract_path.write_text(
        json.dumps([]),
        encoding="utf-8",
    )

    with pytest.raises(
        DataContractValidationError,
        match=r"data contract must be a JSON object",
    ):
        load_data_contract(contract_path)


def test_load_data_contract_returns_valid_contract(
    orders_contract: DataContract,
    tmp_path: Path,
) -> None:
    contract_path = tmp_path / "data_contract.json"
    contract_path.write_text(
        json.dumps(orders_contract),
        encoding="utf-8",
    )

    loaded_contract = load_data_contract(contract_path)

    assert loaded_contract == orders_contract


def test_load_data_contract_file_not_found(tmp_path: Path) -> None:
    contract_path = tmp_path / "missing_contract.json"

    with pytest.raises(FileNotFoundError):
        load_data_contract(contract_path)


def test_load_data_contract_invalid_json(tmp_path: Path) -> None:
    contract_path = tmp_path / "invalid_contract.json"

    contract_path.write_text(
        '{"name": "orders", "version": 1,',
        encoding="utf-8",
    )

    with pytest.raises(json.JSONDecodeError):
        load_data_contract(contract_path)


@pytest.mark.parametrize(
    ("field_name", "key", "wrong_value", "expected_error"),
    [
        pytest.param(
            "order_id",
            "type",
            123,
            ("contract.fields.order_id.type must be a non-empty string"),
            id="type-is-integer",
        ),
        pytest.param(
            "order_id",
            "type",
            "money",
            ("contract.fields.order_id.type is not supported: money"),
            id="type-is-unsupported",
        ),
        pytest.param(
            "order_id",
            "required",
            "true",
            ("contract.fields.order_id.required must be a boolean"),
            id="required-is-string",
        ),
        pytest.param(
            "order_id",
            "nullable",
            0,
            ("contract.fields.order_id.nullable must be a boolean"),
            id="nullable-is-integer",
        ),
        pytest.param(
            "order_id",
            "description",
            "   ",
            ("contract.fields.order_id.description must be a non-empty string"),
            id="description-is-blank",
        ),
        pytest.param(
            "order_id",
            "minimum",
            True,
            ("contract.fields.order_id.minimum must be a number"),
            id="minimum-is-boolean",
        ),
        pytest.param(
            "amount",
            "is_finite",
            "true",
            ("contract.fields.amount.is_finite must be a boolean"),
            id="is-finite-is-string",
        ),
        pytest.param(
            "order_date",
            "format",
            "",
            ("contract.fields.order_date.format must be a non-empty string"),
            id="format-is-empty",
        ),
        pytest.param(
            "status",
            "allowed_statuses",
            "paid",
            ("contract.fields.status.allowed_statuses must be a non-empty list"),
            id="allowed-statuses-is-string",
        ),
        pytest.param(
            "status",
            "allowed_statuses",
            [],
            ("contract.fields.status.allowed_statuses must be a non-empty list"),
            id="allowed-statuses-is-empty",
        ),
        pytest.param(
            "status",
            "allowed_statuses",
            ["paid", 123],
            ("contract.fields.status.allowed_statuses must contain non-empty strings"),
            id="allowed-statuses-contain-integer",
        ),
    ],
)
def test_load_data_contract_validation_rules(
    orders_contract: DataContract,
    tmp_path: Path,
    field_name: str,
    key: str,
    wrong_value: Any,
    expected_error: str,
) -> None:
    wrong_contract = cast(
        dict[str, Any],
        deepcopy(orders_contract),
    )

    wrong_contract["fields"][field_name][key] = wrong_value

    contract_path = tmp_path / "data_contract.json"
    contract_path.write_text(
        json.dumps(wrong_contract),
        encoding="utf-8",
    )

    with pytest.raises(DataContractValidationError) as error:
        load_data_contract(contract_path)

    assert str(error.value) == expected_error


def test_data_load_contracts_order_id_not_dict(
    orders_contract: DataContract, tmp_path: Path
):

    wrong_contract = cast(
        dict[str, Any],
        deepcopy(orders_contract),
    )

    wrong_contract["fields"]["order_id"] = "wrong"

    contract_path = tmp_path / "data_contract.json"
    contract_path.write_text(
        json.dumps(wrong_contract),
        encoding="utf-8",
    )

    with pytest.raises(DataContractValidationError) as error:
        load_data_contract(contract_path)

    assert str(error.value) == "contract.fields.order_id must be a dictionary"


def test_data_load_contracts_empty_field_name(
    orders_contract: DataContract, tmp_path: Path
):

    wrong_contract = cast(
        dict[str, Any],
        deepcopy(orders_contract),
    )

    wrong_contract["fields"][""] = {}

    contract_path = tmp_path / "data_contract.json"
    contract_path.write_text(
        json.dumps(wrong_contract),
        encoding="utf-8",
    )

    with pytest.raises(DataContractValidationError) as error:
        load_data_contract(contract_path)

    assert str(error.value) == "contract field name must be a non-empty string"


def test_load_data_contract_rejects_empty_fields_dict(
    orders_contract: DataContract, tmp_path: Path
) -> None:
    wrong_contract = deepcopy(orders_contract)
    wrong_contract["fields"] = {}
    json_path = tmp_path / "data_contract.json"
    json_path.write_text(
        json.dumps(wrong_contract),
        encoding="utf-8",
    )

    with pytest.raises(
        DataContractValidationError,
        match=r"contract\.fields must be a non-empty dictionary",
    ):
        load_data_contract(json_path)
