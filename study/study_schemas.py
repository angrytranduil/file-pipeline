from typing import TypedDict


class InputSnapshot(TypedDict):
    source_path: str
    snapshot_path: str
    sha256: str
    size_bytes: int