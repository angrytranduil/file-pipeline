import hashlib
from src.schemas import PayloadFingerprint



def analyze_text_payload(payload: bytes) -> PayloadFingerprint:
    raw_sha256 = hashlib.sha256(payload).hexdigest()
    normalized_text = payload.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    normalized_sha256 = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    character_count = len(normalized_text)
    raw_size_bytes = len(payload)

    return {"raw_size_bytes": raw_size_bytes,
            "character_count": character_count,
            "raw_sha256": raw_sha256,
            "normalized_sha256": normalized_sha256}


if __name__ == "__main__":
    text = "name,city\nИван,Москва\n"
    payload = text.encode("utf-8-sig")
    raw_sha_256 = hashlib.sha256(payload).hexdigest()
    normalized_text = payload.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    normalized_sha256 = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()
    print(payload) 
    print(raw_sha_256)       
    print(normalized_sha256)    
    print("\r".encode("utf-8"))