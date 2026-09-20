import json
from pathlib import Path
from typing import cast

from src.exceptions import DataContractValidationError
from src.schemas import DataContract

SUPPORTED_FIELD_TYPES: set[str] = {
    "integer",
    "float",
    "date",
    "string",
}


def validate_contract_field(
    field_name: str,
    field_contract: object,
) -> None:
    if not isinstance(field_contract, dict):
        raise DataContractValidationError(
            f"contract.fields.{field_name} must be a dictionary"
        )

    field_type = field_contract.get("type")

    if not isinstance(field_type, str) or not field_type.strip():
        raise DataContractValidationError(
            f"contract.fields.{field_name}.type must be a non-empty string"
        )

    if field_type not in SUPPORTED_FIELD_TYPES:
        raise DataContractValidationError(
            f"contract.fields.{field_name}.type is not supported: {field_type}"
        )

    for boolean_key in ("required", "nullable"):
        boolean_value = field_contract.get(boolean_key)

        if type(boolean_value) is not bool:
            raise DataContractValidationError(
                f"contract.fields.{field_name}.{boolean_key} must be a boolean"
            )

    description = field_contract.get("description")

    if not isinstance(description, str) or not description.strip():
        raise DataContractValidationError(
            f"contract.fields.{field_name}.description must be a non-empty string"
        )

    if "minimum" in field_contract:
        minimum = field_contract["minimum"]
        if type(minimum) not in (int, float):
            raise DataContractValidationError(
                f"contract.fields.{field_name}.minimum must be a number"
            )

    if "is_finite" in field_contract:
        is_finite = field_contract["is_finite"]
        if not isinstance(is_finite, bool):
            raise DataContractValidationError(
                f"contract.fields.{field_name}.is_finite must be a boolean"
            )

    if "format" in field_contract:
        field_format = field_contract["format"]
        if not isinstance(field_format, str) or field_format.strip() == "":
            raise DataContractValidationError(
                f"contract.fields.{field_name}.format must be a non-empty string"
            )

    if "allowed_statuses" in field_contract:
        allowed_statuses = field_contract["allowed_statuses"]
        if not isinstance(allowed_statuses, list) or not allowed_statuses:
            raise DataContractValidationError(
                f"contract.fields.{field_name}.allowed_statuses "
                "must be a non-empty list"
            )

        for status in allowed_statuses:
            if not isinstance(status, str) or not status.strip():
                raise DataContractValidationError(
                    f"contract.fields.{field_name}.allowed_statuses "
                    "must contain non-empty strings"
                )


def load_data_contract(path: str | Path) -> DataContract:
    contract_path = Path(path)

    with contract_path.open(encoding="utf-8") as file:
        raw_contract: object = json.load(file)

    if not isinstance(raw_contract, dict):
        raise DataContractValidationError("data contract must be a JSON object")

    version = raw_contract.get("version")

    if type(version) is not int:
        raise DataContractValidationError("contract.version must be an integer")

    if version < 1:
        raise DataContractValidationError("contract.version must be positive")

    name = raw_contract.get("name")

    if not isinstance(name, str) or name.strip() == "":
        raise DataContractValidationError("contract.name must be a non-empty string")

    contract_format = raw_contract.get("format")

    if not isinstance(contract_format, str) or contract_format.strip() == "":
        raise DataContractValidationError("contract.format must be a non-empty string")

    encoding = raw_contract.get("encoding")

    if not isinstance(encoding, str) or encoding.strip() == "":
        raise DataContractValidationError(
            "contract.encoding must be a non-empty string"
        )

    allow_extra_fields = raw_contract.get("allow_extra_fields")

    if type(allow_extra_fields) is not bool:
        raise DataContractValidationError("contract.allow_extra_fields must be boolean")

    fields = raw_contract.get("fields")

    if not isinstance(fields, dict):
        raise DataContractValidationError("contract.fields must be a dictionary")

    if fields == {}:
        raise DataContractValidationError(
            "contract.fields must be a non-empty dictionary"
        )

    for field_name, field_contract in fields.items():
        if not isinstance(field_name, str) or not field_name.strip():
            raise DataContractValidationError(
                "contract field name must be a non-empty string"
            )
        validate_contract_field(field_name, field_contract)

    return cast(DataContract, raw_contract)
