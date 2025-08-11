"""
Adapted from Oterm's image picker to a general manifest file picker for SAGE.

Changes:
- Removed image preview logic; supports any file type (txt, csv, json, pdf, docx, xlsx, etc.).
- Defaults to opening the user's Downloads folder (fallback to Documents or Home).
- Reads the selected file's text content (with format-specific parsing where applicable)
  and returns it directly to the caller.
- Used together with prompt.py so that selecting a file sends its contents
  straight into the chat for immediate model processing.
"""

from pathlib import Path
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import DirectoryTree, Input, Label

# File reading libraries
import fitz       # PyMuPDF for PDF
import docx       # python-docx for Word
import openpyxl   # for Excel

MAX_CHARS = 20000  # keep under your context budget

# Prompt Engineering
def _truncate_for_model(text: str, limit: int = MAX_CHARS) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    return text[:limit], True

def _build_manifest_prompt(filename: str, body: str, truncated: bool) -> str:
    note = "\n\n[Note: Input truncated for initial pass.]" if truncated else ""
    return (
        "You are assisting an export‑compliance analyst. Read the manifest text and produce a concise, factual output.\n"
        "Extract these if present (use 'N/A' when missing):\n"
        "• Origin country  • Destination country  • Shipper / Consignee / End‑user\n"
        "• Items/models (e.g., GPU names)  • Quantities  • HS/ECCN codes  • Dates / PO / Invoice #\n"
        "Then provide a 2–3 sentence summary of what this document is about.\n"
        "Do not speculate or advise—just extract and summarize.\n\n"
        f"--- BEGIN MANIFEST: {filename} ---\n{body}\n--- END MANIFEST ---"
        f"{note}"
    )

def get_default_pick_dir() -> Path:
    """Return a sensible default folder for file picker."""
    home = Path.home()
    for sub in ("Downloads", "Documents"):
        p = home / sub
        if p.exists():
            return p
    return home

DEFAULT_ROOT = get_default_pick_dir()

def load_manifest_text(path: Path) -> str:
    """Load text from a manifest file depending on type."""
    suffix = path.suffix.lower()
    if suffix in (".txt", ".csv", ".json"):
        return path.read_text(encoding="utf-8", errors="ignore")
    elif suffix == ".pdf":
        doc = fitz.open(path)
        return "\n".join(page.get_text() for page in doc)
    elif suffix == ".docx":
        d = docx.Document(path)
        return "\n".join(p.text for p in d.paragraphs)
    elif suffix in (".xlsx", ".xlsm"):
        wb = openpyxl.load_workbook(path, read_only=True)
        text_chunks = []
        for sheet in wb:
            for row in sheet.iter_rows(values_only=True):
                text_chunks.append("\t".join(str(cell or "") for cell in row))
        return "\n".join(text_chunks)
    else:
        return f"[Unsupported file type: {suffix}]"

class ImageSelect(ModalScreen[str]):
    """
    NOTE: Retained original class name for Oterm imports.
    This is now a generic manifest file picker.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def action_cancel(self) -> None:
        self.dismiss("")

    async def on_mount(self) -> None:
        dt = self.query_one(DirectoryTree)
        dt.show_guides = False
        dt.path = DEFAULT_ROOT
        dt.focus()

    @on(DirectoryTree.FileSelected)
    async def on_file_selected(self, ev: DirectoryTree.FileSelected) -> None:
        """When a file is picked, read text, wrap with instructions, and send to chat."""
        try:
            raw = load_manifest_text(ev.path)
            body, truncated = _truncate_for_model(raw)            # uses MAX_CHARS guard
            content = _build_manifest_prompt(ev.path.name, body, truncated)
        except Exception as e:
            content = f"[Error reading file '{ev.path.name}': {e}]"
        self.dismiss({ # Return filename and hidden content
            "filename": ev.path.name,
            "hidden": content,    
        })


    @on(Input.Changed)
    async def on_root_changed(self, ev: Input.Changed) -> None:
        """Handle changes in root path input box."""
        dt = self.query_one(DirectoryTree)
        path = Path(ev.value)
        if not path.exists() or not path.is_dir():
            return
        dt.path = path

    def compose(self) -> ComposeResult:
        """UI layout for file picker."""
        with Container(id="manifest-select-container", classes="screen-container full-height"):
            with Horizontal():
                with Vertical(id="manifest-directory-tree"):
                    yield Label("Select a manifest for analysis:", classes="title")
                    yield Label("Root:")
                    yield Input(DEFAULT_ROOT.as_posix())
                    yield DirectoryTree(DEFAULT_ROOT.as_posix())
