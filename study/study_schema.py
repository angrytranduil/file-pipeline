from typing import TypedDict


class FileFingerprint(TypedDict):
    sha256: str
    size_bytes: int 