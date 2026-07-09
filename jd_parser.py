"""
jd_parser.py
------------
Extracts text from an uploaded Job Description, which may be either a
.txt file or a .pdf file.
"""

import re

import fitz  # PyMuPDF

from pdf_parser import PDFParsingError


def extract_jd_text(file) -> str:
    """
    Extract text from an uploaded Job Description file (.txt or .pdf).

    Returns "" if the file has an unsupported extension (shouldn't happen
    given the file_uploader's `type` restriction, but handled defensively).

    Raises:
        PDFParsingError: if a .pdf JD is corrupted, empty, or has no
        extractable text (same error type used by pdf_parser.py, so
        app.py only needs one except clause for both resume and JD parsing).
    """
    try:
        file.seek(0)
    except (AttributeError, ValueError):
        pass

    filename = (file.name or "").lower()

    if filename.endswith(".txt"):
        raw_bytes = file.read()
        if not raw_bytes:
            raise PDFParsingError("The uploaded Job Description file is empty.")

        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Fall back gracefully for JD files saved with a different
            # encoding (e.g. Windows-1252 from Notepad/Word) instead of
            # crashing the app.
            text = raw_bytes.decode("latin-1", errors="ignore")

        return text.strip()

    if filename.endswith(".pdf"):
        raw_bytes = file.read()
        if not raw_bytes:
            raise PDFParsingError("The uploaded Job Description PDF is empty.")

        try:
            doc = fitz.open(stream=raw_bytes, filetype="pdf")
        except Exception as exc:
            raise PDFParsingError(
                "The Job Description PDF could not be opened. It may be "
                "corrupted or password-protected."
            ) from exc

        if doc.page_count == 0:
            doc.close()
            raise PDFParsingError("The Job Description PDF has no pages.")

        text_parts = [page.get_text() for page in doc]
        doc.close()

        text = "".join(text_parts)
        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = text.strip()

        if not text:
            raise PDFParsingError(
                "No readable text could be extracted from the Job Description "
                "PDF. It may be a scanned/image-only document."
            )

        return text

    # Unsupported extension — return empty string, callers decide how to
    # message this (the file_uploader already restricts allowed types).
    return ""
