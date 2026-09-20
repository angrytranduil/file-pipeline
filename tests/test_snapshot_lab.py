import hashlib
from pathlib import Path

import pytest

from study.snapshot_lab import create_input_snapshot


def test_snapshot_preserves_captured_version(tmp_path: Path) -> None:
    source_path = tmp_path / "orders.csv"
    snapshot_root = tmp_path / "snapshots"
    run_id = "run-001"
    version_a = b"order_id,amount\n1,100\n"
    version_b = b"order_id,amount\n1,999\n"

    source_path.write_bytes(version_a)

    snapshot = create_input_snapshot(
        source_path=source_path,
        snapshot_root=snapshot_root,
        run_id=run_id,
    )

    source_path.write_bytes(version_b)

    snapshot_path = Path(snapshot["snapshot_path"])
    run_directory = snapshot_root / run_id

    assert source_path.read_bytes() == version_b
    assert snapshot_path == run_directory / source_path.name
    assert snapshot_path.is_file()
    assert snapshot_path.read_bytes() == version_a
    assert snapshot["sha256"] == hashlib.sha256(version_a).hexdigest()
    assert list(run_directory.glob("*.part")) == []


def test_existing_run_id_does_not_overwrite_snapshot(tmp_path: Path) -> None:
    source_path = tmp_path / "orders.csv"
    snapshot_root = tmp_path / "snapshots"
    run_id = "run-001"
    version_a = b"order_id,amount\n1,100\n"
    version_b = b"order_id,amount\n1,999\n"

    source_path.write_bytes(version_a)
    first_snapshot = create_input_snapshot(
        source_path=source_path,
        snapshot_root=snapshot_root,
        run_id=run_id,
    )

    source_path.write_bytes(version_b)

    with pytest.raises(FileExistsError):
        create_input_snapshot(
            source_path=source_path,
            snapshot_root=snapshot_root,
            run_id=run_id,
        )

    snapshot_path = Path(first_snapshot["snapshot_path"])

    assert source_path.read_bytes() == version_b
    assert snapshot_path.read_bytes() == version_a
