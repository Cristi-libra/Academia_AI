"""
Per-user file tools.

Expose the files a user uploaded through the web UI so the professor can
list them and read their content on demand - instead of the user pasting
everything. Reading supports PDF / DOCX / any text format (via
document_reader), and files are scoped per user so nobody can read
someone else's uploads.
"""

import os

try:
    from .tool import Tool
except ImportError:
    from tool import Tool

try:
    import config
    from document_reader import extract_text
except ImportError:
    from .. import config
    from ..document_reader import extract_text


def _user_dir(user_id: str) -> str:
    return os.path.join(config.UPLOADS_DIR, user_id)


def make_file_tools(user_id: str):
    """Return list/read tools bound (via closure) to one user's upload folder."""
    directory = _user_dir(user_id)

    def list_uploaded_files() -> str:
        if not os.path.isdir(directory):
            return "No files uploaded yet."
        files = [
            f for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ]
        if not files:
            return "No files uploaded yet."
        return "Uploaded files:\n" + "\n".join(f"- {f}" for f in files)

    def read_uploaded_file(filename: str) -> str:
        safe = os.path.basename(filename or "")
        path = os.path.join(directory, safe)
        if not os.path.isfile(path):
            return (
                f"File '{safe}' not found. Call list_uploaded_files to see "
                "the available files."
            )
        with open(path, "rb") as f:
            data = f.read()
        return extract_text(safe, data)

    list_tool = Tool(
        name="list_uploaded_files",
        description=(
            "Lists the files the current user uploaded through the UI. Call it "
            "before read_uploaded_file when the user refers to 'the file' / 'my "
            "document' without naming it exactly."
        ),
        parameters={"type": "object", "properties": {}},
        callback=list_uploaded_files,
    )

    read_tool = Tool(
        name="read_uploaded_file",
        description=(
            "Reads the text content of a file the current user uploaded (PDF, "
            "DOCX, code, notes, etc.). Use this to read or evaluate an uploaded "
            "document instead of asking the user to paste its content."
        ),
        parameters={
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Exact name of the uploaded file to read.",
                }
            },
            "required": ["filename"],
        },
        callback=read_uploaded_file,
    )

    return [list_tool, read_tool]
