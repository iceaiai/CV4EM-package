"""Create binary masks from a folder of images."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from .segmentation import segment_images


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".gif"}


def find_images(input_dir: Path, recursive: bool = True) -> Iterable[Path]:
    pattern = "**/*" if recursive else "*"
    for path in sorted(input_dir.glob(pattern)):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def make_masks(
    input_dir: str | Path,
    output_dir: str | Path,
    threshold: int | None = None,
    invert: bool = False,
    recursive: bool = True,
) -> list[Path]:
    """Generate masks from images in ``input_dir``."""

    source_dir = Path(input_dir)
    if not source_dir.exists():
        raise FileNotFoundError(source_dir)
    images = list(find_images(source_dir, recursive=recursive))
    return segment_images(images, output_dir, threshold=threshold, invert=invert)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create threshold masks from image files.")
    parser.add_argument("input_dir", help="Folder containing source images.")
    parser.add_argument("output_dir", help="Folder where masks will be written.")
    parser.add_argument("--threshold", type=int, default=None, help="Intensity threshold. Defaults to Otsu/mean.")
    parser.add_argument("--invert", action="store_true", help="Mask pixels below the threshold instead of above.")
    parser.add_argument("--no-recursive", action="store_true", help="Only read images directly in input_dir.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    outputs = make_masks(
        args.input_dir,
        args.output_dir,
        threshold=args.threshold,
        invert=args.invert,
        recursive=not args.no_recursive,
    )
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
