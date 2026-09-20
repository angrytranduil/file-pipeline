from collections.abc import Mapping
from typing import Literal, NotRequired, TypedDict

OrderStatus = Literal["paid", "cancelled", "failed"]
RunStatus = Literal["success", "failed", "running"]
RawOrderRow = Mapping[str, str | None]


class PayloadFingerprint(TypedDict):
    raw_size_bytes: int
    character_count: int
    raw_sha256: str
    normalized_sha256: str


class InputSnapshot(TypedDict):
    source_path: str
    snapshot_path: str
    sha256: str
    size_bytes: int


class ContractField(TypedDict):
    type: str
    required: bool
    nullable: bool
    description: str
    minimum: NotRequired[int | float]
    format: NotRequired[str]
    allowed_statuses: NotRequired[list[OrderStatus]]
    is_finite: NotRequired[bool]


class DataContract(TypedDict):
    name: str
    version: int
    format: str
    encoding: str
    allow_extra_fields: bool
    fields: dict[str, ContractField]


class RejectedRow(TypedDict):
    line_number: int
    row: RawOrderRow
    error: str


class Order(TypedDict):
    order_id: int
    customer_id: int
    order_date: str
    amount: float
    status: OrderStatus


class Metrics(TypedDict):
    orders_count: int
    paid_orders_count: int
    cancelled_orders_count: int
    failed_orders_count: int
    total_amount: float
    paid_amount: float
    average_paid_amount: float | None


class ExtractResult(TypedDict):
    orders: list[Order]
    rejected_rows: list[RejectedRow]
    total_rows: int
    valid_rows_count: int
    rejected_rows_count: int
    error_rate: float


class PipelineRunMetadata(TypedDict):
    run_id: str
    status: RunStatus
    started_at: str
    finished_at: str | None
    duration_seconds: float | None
    input_path: str
    snapshot_path: str | None
    contract_path: str
    metrics_output_path: str
    rejected_output_path: str
    max_error_rate: float
    total_rows: int | None
    valid_rows_count: int | None
    rejected_rows_count: int | None
    error_rate: float | None
    error_message: str | None
    error_type: str | None
    input_sha256: str | None
    input_size_bytes: int | None
