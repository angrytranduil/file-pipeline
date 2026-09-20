from study.encoding_lab import analyze_text_payload
import pytest
import hashlib
from typing import get_type_hints
from src.schemas import PayloadFingerprint

def test_analyze_text_payload_raw_hash_is_different_in_diff_encoding():
    text = "name,city\nИван,Москва\n"
    plain_payload = text.encode("utf-8")
    bom_payload = text.encode("utf-8-sig")
    crlf_payload = text.replace("\n", "\r\n").encode("utf-8")

    plain_fingerprint = analyze_text_payload(plain_payload)
    bom_fingerprint = analyze_text_payload(bom_payload)
    crlf_fingerprint = analyze_text_payload(crlf_payload)


    assert (plain_fingerprint["raw_sha256"] != crlf_fingerprint["raw_sha256"] 
            and bom_fingerprint["raw_sha256"]  != plain_fingerprint["raw_sha256"] 
            and bom_fingerprint["raw_sha256"]  != crlf_fingerprint["raw_sha256"] )

    


def test_analyze_text_payload_three_different_encoding_normalized_hash_is_the_same_for_diff_encoding():
    text = "name,city\nИван,Москва\n"
    plain_payload = text.encode("utf-8")
    bom_payload = text.encode("utf-8-sig")
    crlf_payload = text.replace("\n", "\r\n").encode("utf-8")

    plain_fingerprint = analyze_text_payload(plain_payload)
    bom_fingerprint = analyze_text_payload(bom_payload)
    crlf_fingerprint = analyze_text_payload(crlf_payload)


    assert (plain_fingerprint["normalized_sha256"] == crlf_fingerprint["normalized_sha256"] 
                    and bom_fingerprint["normalized_sha256"]  == plain_fingerprint["normalized_sha256"] 
                     )




def test_analyze_text_payload_russian_text_bytes_and_symb_length_is_different():
    text = "name,city\nИван,Москва\n"
    plain_payload = text.encode("utf-8")
    bom_payload = text.encode("utf-8-sig")
    crlf_payload = text.replace("\n", "\r\n").encode("utf-8")

    plain_fingerprint = analyze_text_payload(plain_payload)
    bom_fingerprint = analyze_text_payload(bom_payload)
    crlf_fingerprint = analyze_text_payload(crlf_payload)


    assert (plain_fingerprint["character_count"] != plain_fingerprint["raw_size_bytes"] 
                and bom_fingerprint["character_count"]  != bom_fingerprint["raw_size_bytes"] 
                and crlf_fingerprint["character_count"]  != crlf_fingerprint["raw_size_bytes"] )
    
        
def test_analyze_text_payload_wrong_utf_8():
    payload = b"\xff"

    with pytest.raises(UnicodeDecodeError):
        analyze_text_payload(payload)

@pytest.mark.parametrize(
        ("field","hash"),
        [
           pytest.param("normalized_sha256", "b57bbf595ab10ced32b1749f420e55c7182a5eb90ec9f271a7bb254c73919f99"),
           pytest.param("raw_sha256", "31a44fc2d59e86dfa7d531b5c844826c5669acb1484176c38453d3813c0fcd56"),
        ]
)
def test_analyze_text_payload_hash_is_correct(field,
                                                         hash):
    text = "name,city\nИван,Москва\n"
    payload = text.encode("utf-8-sig")      
    fingerprint = analyze_text_payload(payload)

    assert fingerprint[field] == hash
    #\xef\xbb\xbf


def test_analyze_text_payload_raw_size_bytes_is_correct():
    text = "name,city\nИван,Москва\n"
    payload = text.encode("utf-8-sig")
    raw_size_bytes = len(payload)

    fingerprint = analyze_text_payload(payload)

    assert fingerprint["raw_size_bytes"]  == raw_size_bytes


def test_analyze_text_payload_eol_is_cleared():

    text = "name,city\rИван,Москва"
    payload = text.encode("utf-8-sig")
    fingerprint = analyze_text_payload(payload)

    text2 = "name,city\r\nИван,Москва"
    payload2 = text2.encode("utf-8-sig")
    fingerprint2 = analyze_text_payload(payload2)

    assert fingerprint["normalized_sha256"] == fingerprint2["normalized_sha256"]
    


def test_analyze_text_payload_bom_is_cleared():
    text = "name,city\nИван,Москва"
    payload = text.encode("utf-8-sig")
    fingerprint = analyze_text_payload(payload)

    text2 = "name,city\nИван,Москва"
    payload2 = text2.encode("utf-8")
    fingerprint2 = analyze_text_payload(payload2)

    assert fingerprint["character_count"] == fingerprint2["character_count"]



def test_analyze_text_payload_no_extra_fields():
    text = "name,city\nИван,Москва"
    payload = text.encode("utf-8-sig")
    expected_fields = set(get_type_hints(PayloadFingerprint).keys())
    fingerprint = analyze_text_payload(payload)
    actual_fields = set(fingerprint.keys())

    assert actual_fields == expected_fields


def test_analyze_text_payload_empty_payload():
    
    payload = b""
    fingerprint = analyze_text_payload(payload)
    expected_hash = hashlib.sha256(b"").hexdigest()

    assert fingerprint["character_count"] == 0
    assert fingerprint["raw_size_bytes"] == 0
    assert fingerprint["raw_sha256"] == expected_hash
    assert fingerprint["normalized_sha256"] == expected_hash
    