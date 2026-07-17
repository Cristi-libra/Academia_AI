"""
Uploaded File Tools.

Lets the agent read files a specific user has uploaded through the web UI
(POST /upload in api.py) or the CLI ('upload <path>' command in main.py).

Unlike the other tools in this package, these are built per-user by
make_file_tools(user_id) instead of being module-level Tool instances -
each Agent needs its own pair of tools scoped to its own upload folder,
so one user can never read another user's files.
"""

import os

try:
    from .tool import Tool
except ImportError:
    from tool import Tool

try:
    from config import UPLOADS_DIR, UPLOAD_MAX_CHARS
except ImportError:
    from ..config import UPLOADS_DIR, UPLOAD_MAX_CHARS


def make_file_tools(user_id):
    """Build list_uploaded_files/read_uploaded_file tools scoped to one user."""
    user_dir = os.path.join(UPLOADS_DIR, user_id)

    def list_uploaded_files() -> str:
        """List the filenames this user has uploaded, so the agent knows what's available."""
        if not os.path.isdir(user_dir):
            return "No files uploaded yet."
        files = sorted(os.listdir(user_dir))
        if not files:
            return "No files uploaded yet."
        return "Uploaded files: " + ", ".join(files)

    def read_uploaded_file(filename: str) -> str:
        """
        Read the text content of a file this user uploaded.

        Parameters:
            filename (str): Exact filename, as returned by list_uploaded_files.

        Returns:
            str: The file's text content (truncated to UPLOAD_MAX_CHARS),
                 or an error message if the file doesn't exist.
        """
        safe_name = os.path.basename(filename)
        path = os.path.join(user_dir, safe_name)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except FileNotFoundError:
            return (
                f"File '{filename}' not found. "
                "Use list_uploaded_files to see what's available."
            )

        if len(content) > UPLOAD_MAX_CHARS:
            return (
                content[:UPLOAD_MAX_CHARS]
                + f"\n\n[Content truncated at {UPLOAD_MAX_CHARS} characters.]"
            )
        return content

    list_tool = Tool(
        name="list_uploaded_files",
        description=(
            "Lists the files the current user has uploaded through the UI. "
            "Call this before read_uploaded_file if you don't already know "
            "the exact filename, or when the user refers to 'the file I "
            "uploaded' without naming it."
        ),
        parameters={"type": "object", "properties": {}, "required": []},
        callback=list_uploaded_files,
    )

    read_tool = Tool(
        name="read_uploaded_file",
        description=(
            "Reads the text content of a file the current user uploaded "
            "(code, notes, documentation, etc.). Use this instead of asking "
            "the user to paste the content."
        ),
        parameters={
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Exact filename, as returned by list_uploaded_files."
                }
            },
            "required": ["filename"]
        },
        callback=read_uploaded_file,
    )

    return [list_tool, read_tool]
