import pytest

from src.file_metadata import calculate_file_sha256


def test_calculate_file_sha256_returns_expected_hash(tmp_path):
    path = tmp_path / "example.txt"
    path.write_bytes(b"hello")

    result = calculate_file_sha256(path)

    assert result == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_calculate_file_sha256_is_equal_for_equal_content(tmp_path):
    first_path = tmp_path / "first.txt"
    second_path = tmp_path / "second.txt"
    first_path.write_bytes(b"same content")
    second_path.write_bytes(b"same content")

    assert calculate_file_sha256(first_path) == calculate_file_sha256(second_path)


def test_calculate_file_sha256_changes_when_content_changes(tmp_path):
    path = tmp_path / "example.txt"
    path.write_bytes(b"before")
    hash_before = calculate_file_sha256(path)

    path.write_bytes(b"after")
    hash_after = calculate_file_sha256(path)

    assert hash_before != hash_after


def test_calculate_file_sha256_raises_for_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        calculate_file_sha256(tmp_path / "missing.txt")


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_calculate_file_sha256_rejects_non_positive_chunk_size(tmp_path, chunk_size):
    path = tmp_path / "example.txt"
    path.write_bytes(b"content")

    with pytest.raises(ValueError, match="chunk_size must be positive"):
        calculate_file_sha256(path, chunk_size=chunk_size)
