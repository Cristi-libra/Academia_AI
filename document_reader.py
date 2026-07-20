"""
Document reader for uploaded files.

Extracts plain text from the file types a student is likely to submit
(PDF, Word, and any text-based format) so the professor can read and
evaluate them. Binary/unknown types are reported gracefully instead of
crashing.
"""

import io
import os

# Extensii tratate direct ca text simplu (cod, date, markdown etc.).
TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".json", ".csv", ".log", ".ini", ".cfg",
    ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".h",
    ".xml", ".yml", ".yaml", ".sql", ".sh", ".bat",
}

MAX_CHARS = 20000  # nu inundăm contextul modelului cu un document uriaș


def _truncate(text: str) -> str:
    if len(text) > MAX_CHARS:
        return text[:MAX_CHARS] + f"\n\n[Document truncated at {MAX_CHARS} characters.]"
    return text


def _read_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return "[Could not read PDF: the 'pypdf' package is not installed.]"
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages).strip()
    except Exception as error:
        return f"[Could not read PDF: {error}]"


def _read_docx(data: bytes) -> str:
    try:
        import docx
    except ImportError:
        return "[Could not read DOCX: the 'python-docx' package is not installed.]"
    try:
        document = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in document.paragraphs).strip()
    except Exception as error:
        return f"[Could not read DOCX: {error}]"


def _read_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return data.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    return ""


def extract_text(filename: str, data: bytes) -> str:
    """
    Extract readable text from an uploaded file.

    Parameters:
        filename (str): original name, used to pick the extractor by extension.
        data (bytes): raw file content.

    Returns:
        str: the extracted text (truncated), or a clear message if the file
             type is not supported / could not be read.
    """
    extension = os.path.splitext(filename)[1].lower()

    if extension == ".pdf":
        text = _read_pdf(data)
    elif extension in (".docx",):
        text = _read_docx(data)
    elif extension in TEXT_EXTENSIONS:
        text = _read_text(data)
    else:
        # Ultimă încercare: poate e text fără extensie cunoscută.
        text = _read_text(data)
        if not text:
            return (
                f"[The file '{filename}' has an unsupported type "
                f"('{extension or 'no extension'}') and could not be read as text.]"
            )

    if not text.strip():
        return f"[The file '{filename}' appears to be empty or has no extractable text.]"

    return _truncate(text)
