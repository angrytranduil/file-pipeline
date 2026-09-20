import hashlib

import pytest

from study.exam_1 import calculate_file_fingerprint


@pytest.mark.parametrize(
    ("content"),
    [ pytest.param(
            b"hello",
            ),
      pytest.param(
                b"",
                ),
    pytest.param(bytes([0, 255, 128, 10]),
                ),
    ]
        )
def test_calculate_file_fingerprint_byte_size(tmp_path,
                                              content: bytes                                              
                                            ):
    file_path = tmp_path / "content.bin"
    file_path.write_bytes(content)
    fingerprint = calculate_file_fingerprint(file_path)
    assert len(content) == fingerprint["size_bytes"]
    assert hashlib.sha256(content).hexdigest() == fingerprint["sha256"]

def test_calculate_file_fingerprint_sha_256_matching(tmp_path):
    bstring = b"hello"    
    
    file_path = tmp_path / "hello.bin"
    file_path.write_bytes(bstring)
    test_dict = calculate_file_fingerprint(file_path)

    hello_sha_256 = hashlib.sha256(bstring).hexdigest()

    assert test_dict["sha256"] == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"



def test_calculate_file_fingerprint_calculated_hash_matching_with_full_content_hash(tmp_path):
    content = b"fly me to the moon, let me play among the stars"
    file_path = tmp_path / "content.bin"
    file_path.write_bytes(content)
    fingerprint = calculate_file_fingerprint(file_path,3)
    assert fingerprint["size_bytes"] == len(content)
    assert fingerprint["sha256"] == hashlib.sha256(content).hexdigest()


def test_calculate_file_fingerprint_hash_matches_for_same_content(tmp_path):
    content = b"fly me to the moon, let me play among the stars"
    first_file = tmp_path / "content1.bin"
    second_file = tmp_path / "content2.bin"
    first_file.write_bytes(content)
    second_file.write_bytes(content)
    first_fingerptrint = calculate_file_fingerprint(first_file)
    second_fingerptrint= calculate_file_fingerprint(second_file)

    assert first_fingerptrint== second_fingerptrint


def test_calculate_file_fingerprint_hash_not_matching_when_changing_one_byte(tmp_path):
        content1 = b"hello"
        content2 = b"Hello"
        first_file = tmp_path / "content1.bin"
        second_file = tmp_path / "content2.bin"
        first_file.write_bytes(content1)
        second_file.write_bytes(content2)
        first_fingerptrint = calculate_file_fingerprint(first_file)
        second_fingerptrint= calculate_file_fingerprint(second_file)
    
        assert first_fingerptrint["sha256"] != second_fingerptrint["sha256"]
        assert first_fingerptrint["size_bytes"] == second_fingerptrint["size_bytes"]

@pytest.mark.parametrize(
    ("chunk_size"),
    [ pytest.param(
            0,
            ),
      pytest.param(
                -1,
                ),
    
    ]
        )
def test_calculate_file_fingerprint_check_wrong_chunk_size(tmp_path,
                                                           chunk_size):
    content = b"fly me to the moon, let me play among the stars"
    file_path = tmp_path / "content.bin"
    file_path.write_bytes(content)
    with pytest.raises(ValueError) as exc_info:
        calculate_file_fingerprint(file_path,chunk_size)

    assert str(exc_info.value) == "chunk_size should be positive number"


def test_calculate_file_fingerprint_path_not_exist(tmp_path):
     file_path = tmp_path / "content.bin"
     with pytest.raises(FileNotFoundError):
          calculate_file_fingerprint(file_path)


