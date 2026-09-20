from pathlib import Path

from src.schemas import OrderStatus

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH: Path = PROJECT_ROOT / "data" / "raw" / "orders.csv"
DEFAULT_OUTPUT_PATH: Path = PROJECT_ROOT / "data" / "processed" / "order_metrics.json"
DEFAULT_REJECTED_ROWS_PATH: Path = (
    PROJECT_ROOT / "data" / "rejected" / "rejected_orders.json"
)
DEFAULT_METADATA_PATH: Path = PROJECT_ROOT / "data" / "processed" / "run_metadata.json"

DEFAULT_CONTRACT_PATH: Path = PROJECT_ROOT / "contracts" / "orders_v1.json"

REQUIRED_COLUMNS: set[str] = {
    "order_id",
    "customer_id",
    "order_date",
    "amount",
    "status",
}

ALLOWED_STATUSES: set[OrderStatus] = {"paid", "cancelled", "failed"}
MAX_ERROR_RATE: float = 0.05
