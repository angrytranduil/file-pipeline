from study.study_schemas import InputSnapshot
from pathlib import Path
import hashlib
from contextlib import suppress


def create_input_snapshot(
    source_path: str | Path,
    snapshot_root: str | Path,
    run_id: str,
    chunk_size: int = 1024 * 1024,
) -> InputSnapshot:
    if chunk_size <= 0:
        raise ValueError("chunk_size should be positive integer")

    source_path = Path(source_path)
    snapshot_root = Path(snapshot_root)

    run_directory = snapshot_root / run_id
    destination_path = run_directory / f"{source_path.name}.part"
    snapshot_path = run_directory / source_path.name

    run_directory.mkdir(parents=True, exist_ok=False)

    sha256 = hashlib.sha256()
    size_bytes = 0

    try:
        with (
            source_path.open("rb") as source_file,
            destination_path.open("xb") as destination_file,
        ):
            while chunk := source_file.read(chunk_size):
                size_bytes += len(chunk)
                sha256.update(chunk)
                destination_file.write(chunk)

        destination_path.rename(snapshot_path)
    except Exception:
        with suppress(OSError):
            destination_path.unlink(missing_ok=True)

        with suppress(OSError):
            run_directory.rmdir()

        raise

    return InputSnapshot(
        source_path=str(source_path),
        snapshot_path=str(snapshot_path),
        size_bytes=size_bytes,
        sha256=sha256.hexdigest(),
    )