import hashlib
from pathlib import Path


def calculate_file_sha256(
    path: str | Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    path = Path(path)
    hasher = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()
