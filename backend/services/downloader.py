"""
PDF Downloader Service
Download PDFs with sha256 verification and versioning
"""
from __future__ import annotations
import os
import hashlib
import requests
import fitz  # PyMuPDF
from typing import Tuple, Optional

STORAGE_DIR = os.environ.get("STORAGE_DIR", "./storage")


def ensure_dirs():
    """Ensure storage directory exists"""
    os.makedirs(STORAGE_DIR, exist_ok=True)


def sha256_stream_to_file(
    url: str, 
    dest_path: str, 
    timeout: int = 120
) -> Tuple[str, int, Optional[str], Optional[str]]:
    """
    Download file from URL, stream to disk, compute SHA256.
    Returns: (sha256, bytes_written, etag, last_modified)
    """
    h = hashlib.sha256()
    bytes_written = 0
    
    r = requests.get(
        url, 
        stream=True, 
        timeout=timeout, 
        headers={"User-Agent": "JEA-TPE/1.0"}
    )
    r.raise_for_status()
    
    etag = r.headers.get("ETag")
    last_mod = r.headers.get("Last-Modified")
    
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            f.write(chunk)
            h.update(chunk)
            bytes_written += len(chunk)
            
    return h.hexdigest(), bytes_written, etag, last_mod


def sha256_from_bytes(data: bytes) -> str:
    """Compute SHA256 from bytes"""
    return hashlib.sha256(data).hexdigest()


def count_pdf_pages(path: str) -> int:
    """Count pages in PDF using PyMuPDF"""
    doc = fitz.open(path)
    n = doc.page_count
    doc.close()
    return n


def get_storage_path(
    year: int, 
    paper_no: int, 
    language: str, 
    version: int
) -> str:
    """Generate storage path for PDF"""
    ensure_dirs()
    return os.path.join(
        STORAGE_DIR, 
        f"jea_{year}_p{paper_no}_{language}_v{version}.pdf"
    )
