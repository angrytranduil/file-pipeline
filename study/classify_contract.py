import json
from pathlib import Path

from src.data_contract import load_data_contract
from src.exceptions import DataContractValidationError
from src.schemas import DataContract


def classify_contract_file(path: str | Path) -> str:
    try:
        load_data_contract(path)
    except FileNotFoundError:
        return "missing_file"
    except json.JSONDecodeError:
        return "invalid_json"
    except DataContractValidationError:
        return "invalid_contract"

    return "ok"


def load_contract_with_metrics(
    path: str | Path,
    metrics: dict[str, str | None],
) -> DataContract:

    try:
        data_contract = load_data_contract(path)
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        DataContractValidationError,
    ) as error:
        metrics["status"] = "failed"
        metrics["error_type"] = type(error).__name__
        metrics["error_message"] = str(error)
        raise
    else:
        return data_contract
