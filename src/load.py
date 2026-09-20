import json
import logging
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

logger = logging.getLogger(__name__)


def write_json(path: str | Path, data: object) -> None:
    path = Path(path)
    logger.info("Writing JSON to %s", path)

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        temporary_path.replace(path)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise

    logger.info("JSON written successfully to %s", path)


if __name__ == "__main__":
    metrics = {
        "orders_count": 5,
        "paid_orders_count": 3,
        "cancelled_orders_count": 1,
        "failed_orders_count": 1,
        "total_amount": 865.5,
        "paid_amount": 670.5,
        "average_paid_amount": 223.5,
    }

    output_path = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "processed"
        / "order_metrics.json"
    )

    write_json(output_path, metrics)
