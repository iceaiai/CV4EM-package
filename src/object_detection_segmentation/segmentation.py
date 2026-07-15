"""Threshold-based segmentation helpers for microscopy images."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional, Union

import numpy as np
from PIL import Image


PathLike = Union[str, Path]


def load_grayscale_image(path: PathLike) -> np.ndarray:
    """Load an image as a grayscale uint8 array."""

    image = Image.open(path).convert("L")
    return np.asarray(image, dtype=np.uint8)


def normalize_uint8(image: np.ndarray) -> np.ndarray:
    """Normalize numeric image data to uint8."""

    data = np.asarray(image, dtype=float)
    finite = np.isfinite(data)
    if not finite.any():
        return np.zeros(data.shape, dtype=np.uint8)

    data = np.where(finite, data, 0)
    data -= data.min()
    data_max = data.max()
    if data_max > 0:
        data /= data_max
    return (data * 255).astype(np.uint8)


def threshold_mask(
    image: Union[np.ndarray, PathLike],
    threshold: Optional[int] = None,
    invert: bool = False,
) -> np.ndarray:
    """Create a binary mask from an image.

    If ``threshold`` is omitted, Otsu's method is used when scikit-image is
    installed; otherwise the mean intensity is used as a simple fallback.
    """

    data = load_grayscale_image(image) if isinstance(image, (str, Path)) else normalize_uint8(image)
    if threshold is None:
        try:
            from skimage.filters import threshold_otsu

            threshold = int(threshold_otsu(data))
        except Exception:
            threshold = int(data.mean())

    mask = data < threshold if invert else data > threshold
    return (mask.astype(np.uint8) * 255)


def save_mask(mask: np.ndarray, output_path: PathLike) -> Path:
    """Save a binary mask and return its path."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(mask.astype(np.uint8)).save(output)
    return output


def segment_images(
    image_paths: Iterable[PathLike],
    output_dir: PathLike,
    threshold: Optional[int] = None,
    invert: bool = False,
    suffix: str = "_mask",
) -> list[Path]:
    """Create threshold masks for a collection of images."""

    output_root = Path(output_dir)
    outputs: list[Path] = []
    for image_path in image_paths:
        source = Path(image_path)
        mask = threshold_mask(source, threshold=threshold, invert=invert)
        outputs.append(save_mask(mask, output_root / f"{source.stem}{suffix}.png"))
    return outputs
