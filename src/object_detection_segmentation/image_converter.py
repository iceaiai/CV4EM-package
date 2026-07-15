"""Small image conversion utility for microscopy images."""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Iterable, Optional, Sequence, Union

import numpy as np
from PIL import Image

try:
    import hyperspy.api as hs
except Exception:  # pragma: no cover - depends on optional local install
    hs = None

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:  # pragma: no cover - GUI is optional
    tk = None
    filedialog = None
    messagebox = None


PathLike = Union[str, Path]


class ImageConverter:
    """Convert dm3, dm4, tif, png, jpg, jpeg, or gif files to image files.

    The class can be used interactively with folder dialogs or directly from a
    script/notebook by passing input and output paths.
    """

    supported_input_formats = ("dm3", "dm4", "tif", "tiff", "png", "jpg", "jpeg", "gif")
    supported_output_formats = ("tif", "tiff", "png", "jpg", "jpeg", "gif")

    def __init__(
        self,
        select_input_dir: bool = True,
        select_output_dir: bool = True,
        output_format: str = "png",
        output_size: tuple[int, int] = (512, 512),
        input_path: Optional[PathLike] = None,
        output_path: Optional[PathLike] = None,
        include_subfolders: bool = True,
    ) -> None:
        self.select_input_dir = select_input_dir
        self.select_output_dir = select_output_dir
        self.output_format = output_format.lower().lstrip(".")
        self.output_size = output_size
        self.input_path = Path(input_path).expanduser().resolve() if input_path else None
        self.output_path = Path(output_path).expanduser().resolve() if output_path else None
        self.include_subfolders = include_subfolders

        if self.output_format not in self.supported_output_formats:
            raise ValueError(f"Unsupported output format: {self.output_format}")

    def _ask_directory(self, title: str) -> Path:
        if tk is None or filedialog is None:
            raise RuntimeError("tkinter is not available; pass input_path/output_path directly.")

        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askdirectory(title=title, initialdir=".")
        root.destroy()
        if not selected:
            raise RuntimeError(f"No folder selected for: {title}")
        return Path(selected).resolve()

    def _prepare_input_path(self) -> Path:
        if self.input_path is not None:
            return self.input_path
        if self.select_input_dir:
            self.input_path = self._ask_directory("Please choose the input directory.")
        else:
            self.input_path = Path(".").resolve()
        return self.input_path

    def _prepare_output_path(self) -> Path:
        input_path = self._prepare_input_path()
        if self.output_path is not None:
            self.output_path.mkdir(parents=True, exist_ok=True)
            return self.output_path

        default_output = input_path.parent / "converted_images" / input_path.stem
        if self.select_output_dir and default_output.exists() and any(default_output.iterdir()):
            use_default = True
            if tk is not None and messagebox is not None:
                root = tk.Tk()
                root.withdraw()
                use_default = messagebox.askyesno(
                    title="Output folder exists",
                    message=(
                        f"The folder:\n{default_output}\n"
                        "already exists and is not empty.\n\n"
                        "Click Yes to reuse it, or No to choose a different output folder."
                    ),
                )
                root.destroy()
            if not use_default:
                self.output_path = self._ask_directory("Please choose another output directory.")
                return self.output_path

        self.output_path = default_output
        self.output_path.mkdir(parents=True, exist_ok=True)
        return self.output_path

    def iter_input_files(self) -> Iterable[Path]:
        input_path = self._prepare_input_path()
        if input_path.is_file():
            candidates: Sequence[Path] = [input_path]
        elif self.include_subfolders:
            candidates = sorted(p for p in input_path.rglob("*") if p.is_file())
        else:
            candidates = sorted(p for p in input_path.iterdir() if p.is_file())

        for path in candidates:
            if path.suffix.lower().lstrip(".") in self.supported_input_formats:
                yield path

    def _load_array(self, path: Path) -> np.ndarray:
        suffix = path.suffix.lower().lstrip(".")
        if suffix in {"dm3", "dm4"}:
            if hs is None:
                raise RuntimeError("HyperSpy is required to read dm3/dm4 files.")
            signal = hs.load(path)
            data = signal[0].data if isinstance(signal, list) else signal.data
            return np.asarray(data)
        return np.asarray(Image.open(path))

    @staticmethod
    def _to_uint8(data: np.ndarray) -> np.ndarray:
        if data.ndim == 3 and data.shape[-1] in {3, 4}:
            data = data[..., :3]
        data = np.asarray(data, dtype=float)
        finite = np.isfinite(data)
        if not finite.any():
            return np.zeros(data.shape[:2], dtype=np.uint8)

        data = np.where(finite, data, 0)
        data -= data.min()
        data_max = data.max()
        if data_max > 0:
            data /= data_max
        return (data * 255).astype(np.uint8)

    def _output_file(self, source: Path) -> Path:
        output_root = self._prepare_output_path()
        input_root = self._prepare_input_path()
        stem = f"{source.stem}_{secrets.token_hex(5)}"

        if input_root.is_dir() and source.parent != input_root:
            relative_parent = source.parent.relative_to(input_root)
            output_dir = output_root / relative_parent
        else:
            output_dir = output_root
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f"{stem}.{self.output_format}"

    def convert_file(self, path: PathLike) -> Path:
        source = Path(path).expanduser().resolve()
        image = Image.fromarray(self._to_uint8(self._load_array(source)))
        image = image.resize(self.output_size, resample=Image.BILINEAR)
        output_file = self._output_file(source)
        image.save(output_file)
        return output_file

    def convert_to_image(self, input_data: Optional[Union[PathLike, Sequence[PathLike]]] = None) -> list[Path]:
        if input_data is None:
            sources = list(self.iter_input_files())
        elif isinstance(input_data, (str, Path)):
            sources = [Path(input_data)]
        else:
            sources = [Path(item) for item in input_data]

        outputs = [self.convert_file(source) for source in sources]
        for source, output in zip(sources, outputs):
            print(f"[OK] {source} -> {output}")
        return outputs


# Backward-compatible alias used by older notebooks.
image_converter = ImageConverter
