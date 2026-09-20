import hashlib
from pathlib import Path

from study.study_schema import FileFingerprint


def calculate_file_fingerprint(
    path: str | Path,
    chunk_size: int = 1024 * 1024,
) -> FileFingerprint:
    
    if chunk_size <= 0:
        raise ValueError("chunk_size should be positive number")
    
    size_bytes = 0     
    sha256 = hashlib.sha256()
    
    with Path(path).open("rb") as file:
        while chunk := file.read(chunk_size):            
            size_bytes += len(chunk)
            sha256.update(chunk)
   
         
    return {"sha256": sha256.hexdigest(),
            "size_bytes": size_bytes}
  

