"""
pdf_parser.py
-------------
Extracts text from an uploaded resume PDF using PyMuPDF (fitz).

Raises a single, specific PDFParsingError for every failure mode so the
calling code (app.py) can catch it and show one friendly message, instead
of letting raw PyMuPDF/Python exceptions reach the user.
"""

import fitz  # PyMuPDF


class PDFParsingError(Exception):
    """Raised when a PDF cannot be opened or contains no extractable text."""


def extract_text(pdf_file) -> str:
    """
    Extract text from an uploaded PDF (a Streamlit UploadedFile).

    Raises:
        PDFParsingError: if the file is corrupted, empty (0 pages), or
        contains no extractable text (e.g. a scanned/image-only PDF).
    """
    try:
        pdf_file.seek(0)
    except (AttributeError, ValueError):
        # Some file-like objects may not support seek; safe to ignore.
        pass

    try:
        raw_bytes = pdf_file.read()
    except Exception as exc:
        raise PDFParsingError(f"Could not read the uploaded file: {exc}") from exc

    if not raw_bytes:
        raise PDFParsingError("The uploaded PDF appears to be empty (0 bytes).")

    try:
        doc = fitz.open(stream=raw_bytes, filetype="pdf")
    except Exception as exc:
        raise PDFParsingError(
            "This PDF could not be opened. It may be corrupted, "
            "password-protected, or not a valid PDF file."
        ) from exc

    if doc.page_count == 0:
        doc.close()
        raise PDFParsingError("The uploaded PDF has no pages.")

    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()

    full_text = "".join(text_parts).strip()

    if not full_text:
        raise PDFParsingError(
            "No readable text could be extracted from this PDF. It may be a "
            "scanned/image-only document. Please upload a text-based PDF, "
            "or an OCR'd version of this file."
        )

    return full_text
