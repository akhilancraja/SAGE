"""
Adapted Oterm file picker for manifest browsing.

This version:
- Defaults to the user's Downloads (fallback: Documents/Home)
- Allows selecting any file type (txt, csv, json, pdf, etc.)
- Returns (Path, "") for non-image files so they can be processed as manifests
- Still supports images for preview if needed
"""
from base64 import b64encode
from io import BytesIO
from pathlib import Path

from pathlib import Path

def get_default_pick_dir() -> Path:
    home = Path.home()
    for sub in ("Downloads", "Documents"):
        p = home / sub
        if p.exists():
            return p
    return home

DEFAULT_ROOT = get_default_pick_dir()

import PIL.Image as PILImage
from PIL import UnidentifiedImageError
from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import DirectoryTree, Input, Label
from textual_image.widget import Image

# NOTE: Using DirectoryTree instead of ImageDirectoryTree so all files show
# from oterm.app.widgets.image import IMAGE_EXTENSIONS, ImageDirectoryTree
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}  # local set

class ImageSelect(ModalScreen[tuple[Path, str]]):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def action_cancel(self) -> None:
        self.dismiss()

    async def on_mount(self) -> None:
        dt = self.query_one(DirectoryTree)
        dt.show_guides = False
        dt.path = DEFAULT_ROOT # <- start in manifests/
        dt.focus()

    @on(DirectoryTree.FileSelected) # Patched
    async def on_image_selected(self, ev: DirectoryTree.FileSelected) -> None:
        suffix = ev.path.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            try:
                buffer = BytesIO()
                image = PILImage.open(ev.path)
                if image.mode != "RGB":
                    image = image.convert("RGB")
                image.save(buffer, format="JPEG")
                b64 = b64encode(buffer.getvalue()).decode("utf-8")
                self.dismiss((ev.path, b64))
            except UnidentifiedImageError:
                # fall back to path-only if somehow not an image
                self.dismiss((ev.path, ""))
        else:
           # NEW: for manifests (txt/csv/json/pdf/docx/etc.), return path only
            self.dismiss((ev.path, "")) 

    @on(DirectoryTree.NodeHighlighted)
    async def on_image_highlighted(self, ev: DirectoryTree.NodeHighlighted) -> None:
        path = ev.node.data.path  # type: ignore
        image_widget = self.query_one(Image)
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            try:
                image_widget.image = PILImage.open(path.as_posix())
            except UnidentifiedImageError:
                image_widget.image = None
        else:
            image_widget.image = None

    @on(Input.Changed)
    async def on_root_changed(self, ev: Input.Changed) -> None:
        dt = self.query_one(DirectoryTree)
        path = Path(ev.value)
        if not path.exists() or not path.is_dir():
            return
        dt.path = path

    def compose(self) -> ComposeResult:
        with Container(
            id="image-select-container", classes="screen-container full-height"):
            with Horizontal():
                with Vertical(id="image-directory-tree"):
                    yield Label("Select a manifest for analysis:", classes="title")
                    yield Label("Root:")
                    yield Input(DEFAULT_ROOT.as_posix())
                    yield DirectoryTree(DEFAULT_ROOT.as_posix())
                with Container(id="image-preview"):
                    yield Image(id="image")
