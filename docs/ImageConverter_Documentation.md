# ImageConverter Developer Documentation — v3

**Project:** Object detection and segmentation  
**Module:** `ImageConverter`  
**Primary purpose:** Convert microscopy images, especially DM3/DM4 files loaded through HyperSpy, into image formats suitable for object detection, segmentation, ROI export, image cleaning, selected-image patch export, and later measurement workflows.

This version documents the latest workflow updates:

- full-folder batch conversion,
- selected-image conversion,
- selected-image conversion into a converted-output subfolder,
- updating `image_registration.csv` for a selected converted-image subfolder,
- `current`, `.`, and `./` path support,
- optional subfolder conversion confirmation,
- continued use of stable image IDs,
- overwrite checking,
- existing CSV loading and updating,
- real-time registration CSV updates.

---

## 1. High-Level Design

`ImageConverter` is designed around one central principle:

> Every converted image should remain traceable to the original microscopy image.

For each original source image, the converter can record:

- source image name,
- source image full path,
- source image shape,
- source image height and width,
- source pixel size,
- source pixel-size unit,
- converted image name,
- converted image full path,
- converted image shape,
- converted image height and width,
- converted pixel size,
- converted pixel-size unit,
- whether converted output preserves original resolution,
- conversion status,
- stable source image ID,
- last updated timestamp.

The converter supports several related workflows:

```text
Workflow A:
Original folder
    -> batch convert all images
    -> output folder
    -> image_registration.csv

Workflow B:
Original folder
    -> later select only a few source images
    -> keep_original_resolution=True
    -> same output folder
    -> same image_registration.csv updated

Workflow C:
Original folder
    -> select a few source images
    -> convert them into a subfolder inside the converted-output folder
    -> generate/update a local image_registration.csv in that subfolder

Workflow D:
Converted-output folder
    -> manually move/copy selected converted images into a subfolder
    -> click-select that subfolder
    -> update/create image_registration.csv for that selected subfolder
```

This design is useful for microscopy image workflows because a user may first convert a whole dataset, then later focus only on selected images for high-resolution patches, ROI export, image cleaning, or segmentation dataset preparation.

---

## 2. Main Features

The current version supports:

1. Loading supported images with HyperSpy.
2. Loading a single image or multiple images.
3. Batch loading from an input directory.
4. Optional recursive loading from subfolders.
5. Asking the user whether to include subfolder images.
6. Converting selected source images only.
7. Converting selected source images into an output subfolder.
8. Updating a registration CSV for a selected converted-image subfolder.
9. Stable image ID generation.
10. Output overwrite checking.
11. `Yes`, `No`, `Yes to all`, and `No to all` decisions.
12. Automatic brightness/contrast adjustment.
13. RGB-to-grayscale conversion.
14. Resizing to a target output size.
15. Original-resolution patch export using `keep_original_resolution=True`.
16. Real-time registration CSV update.
17. Existing registration CSV loading.
18. Manual registration support.
19. Pixel-size unit conversion with `autoscale()`.
20. `current`, `.`, and `./` path shortcuts.

---

## 3. Supported Formats

### 3.1 Supported input formats

```python
self.supported_input_formats = ('dm3','dm4','tif','png','jpg','jpeg','gif')
```

Supported input files:

```text
.dm3
.dm4
.tif
.png
.jpg
.jpeg
.gif
```

### 3.2 Supported output formats

```python
self.supported_output_formats = ('tif','png','jpg','jpeg','gif')
```

Supported output files:

```text
.tif
.png
.jpg
.jpeg
.gif
```

If the user passes an unsupported output format, the constructor raises:

```python
ValueError
```

---

## 4. Dependencies

The code uses:

```python
import csv
import hashlib
import ast
import hyperspy.api as hs
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
```

| Package | Purpose |
|---|---|
| `csv` | Write and read registration CSV files. |
| `hashlib` | Generate stable source image IDs. |
| `ast` | Parse tuple-like shape strings from CSV. |
| `hyperspy.api` | Load microscopy images, especially DM3/DM4. |
| `numpy` | Array processing, contrast adjustment, grayscale conversion. |
| `tkinter` | Folder selection and user confirmation dialogs. |
| `PIL.Image` | Create, resize, and save image files. |
| `pathlib.Path` | Cross-platform path handling. |
| `typing` | Type hints. |
| `datetime` | Timestamp registration updates. |

Recommended environment:

```powershell
conda activate image_segmentation
python -c "import hyperspy.api as hs; print('hyperspy ok')"
```

---

## 5. Recommended Project Structure

```text
project_root/
    ImageConverter.py
    Unittest/
        test_image_converter.py
        test_images/
            1.dm3
            2.dm3
            ...
        test_output_converter/
            ...
```

Recommended formal converter filename:

```text
ImageConverter.py
```

Run tests:

```powershell
conda activate image_segmentation
python -m unittest discover -s Unittest -p "test_*.py" -v
```

---

## 6. Path Handling

### 6.1 Explicit paths

The recommended robust workflow is to explicitly provide both `input_path` and `output_path`:

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=r"C:\work\Lyu\Image segmentation\raw_folder",
    output_path=r"C:\work\Lyu\Image segmentation\converted_images\raw_folder"
)
```

This avoids ambiguity and keeps the registration CSV in the correct output folder.

### 6.2 `current`, `.`, and `./`

The updated version supports current-directory shortcuts.

These values are treated as the current working directory:

```text
current
.
./
```

Example:

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path="current",
    output_path="./"
)
```

Expected behavior:

```text
input_path  -> current working directory
output_path -> current working directory
```

This is useful when the user wants to run the converter directly inside the folder containing the images and does not want to create or select a separate output folder.

---

## 7. Common Workflows

### 7.1 Batch convert all images from one original folder

```python
from ImageConverter import ImageConverter

image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=r"C:\work\Lyu\Image segmentation\raw_folder",
    output_path=r"C:\work\Lyu\Image segmentation\converted_images\raw_folder",
    output_format="png",
    output_size=(512, 512),
    pixel_size_unit="nm"
)

image.convert_to_image(
    keep_original_resolution=False,
    auto_brightness_contrast=True,
    include_subfolders=True
)
```

Expected behavior:

1. Supported images are collected from `input_path`.
2. If `include_subfolders=True`, images inside subfolders are also collected.
3. Converted images are written under `output_path`.
4. Subfolder structure is preserved.
5. `image_registration.csv` is written to `output_path`.
6. The CSV is updated after every saved, overwritten, or skipped image.

Expected output:

```text
converted_images/
    raw_folder/
        image_registration.csv
        image1_<source_id>.png
        image2_<source_id>.png
        subfolder/
            image3_<source_id>.png
```

### 7.2 Batch convert only top-level images, not subfolder images

```python
image.convert_to_image(
    include_subfolders=False
)
```

Expected behavior:

Only images directly inside `input_path` are converted.

Example:

```text
raw_folder/
    A.dm3
    B.dm3
    subfolder/
        C.dm3
```

Converted:

```text
A.dm3
B.dm3
```

Not converted:

```text
subfolder/C.dm3
```

### 7.3 Ask whether to include subfolder images

```python
image.convert_to_image(
    include_subfolders=None
)
```

Expected behavior:

- The converter first detects whether subfolders contain supported images.
- If subfolder images are found, the user is asked whether to include them.
- Top-level images can still be converted.
- If the user chooses not to include subfolders, subfolder images are skipped.

This is useful when an input folder contains both direct images and nested folders.

### 7.4 Use current directory as both input and output

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path="current",
    output_path="current",
    output_format="png",
    output_size=(512, 512)
)

image.convert_to_image(
    include_subfolders=None
)
```

Expected behavior:

- The current working directory is used as input.
- Converted images are written into the same current directory.
- `image_registration.csv` is written into the current directory.
- Existing converted images trigger overwrite checking.

Use this mode carefully because source and converted files are in the same folder.

### 7.5 Select only a few original images and export original-resolution patches

Use this when you already converted a full folder, but later want to select only a few original images for `keep_original_resolution=True`.

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=r"C:\work\Lyu\Image segmentation\raw_folder",
    output_path=r"C:\work\Lyu\Image segmentation\converted_images\raw_folder",
    output_format="png",
    output_size=(512, 512),
    pixel_size_unit="nm"
)

image.convert_selected_images(
    selected_files=["1.dm3", "2.dm3"],
    keep_original_resolution=True
)
```

Expected behavior:

1. Only `1.dm3` and `2.dm3` are loaded.
2. The existing `image_registration.csv` in `output_path` is loaded.
3. Patch images are created if the source images can be split into square patches.
4. New patch records are appended or updated.
5. Existing batch-conversion records remain in the same CSV.

### 7.6 Select images using relative paths

```python
image.convert_selected_images(
    selected_files=["subfolder/B.dm3"],
    keep_original_resolution=True
)
```

Input:

```text
raw_folder/
    A.dm3
    subfolder/
        B.dm3
```

Expected output:

```text
converted_images/
    raw_folder/
        subfolder/
            B_<source_id>_resized/
                <source_id>_r000_c000.png
                <source_id>_r000_c001.png
```

### 7.7 Select images using wildcard patterns

```python
image.convert_selected_images(
    selected_files=["*.dm3"],
    keep_original_resolution=True
)
```

or:

```python
image.convert_selected_images(
    selected_files=["subfolder/*.dm3"],
    keep_original_resolution=True
)
```

Expected behavior:

- Matching files are searched relative to `input_path`.
- Only supported file formats are accepted.
- Duplicate matched paths are removed.

### 7.8 Select images using absolute paths

```python
image.convert_selected_images(
    selected_files=[
        r"C:\work\Lyu\Image segmentation\raw_folder\1.dm3",
        r"C:\work\Lyu\Image segmentation\raw_folder\subfolder\2.dm3"
    ],
    keep_original_resolution=True
)
```

Expected behavior:

- Absolute source image paths are used directly.
- Output still goes to the configured `output_path`.
- If selected files are under `input_path`, relative subfolder structure is preserved.

---

## 8. New Workflow: Put Selected Converted Images into an Output Subfolder

There are two related cases.

### 8.1 Case A: Convert selected source images directly into an output subfolder

Use:

```python
image.convert_selected_images_to_subfolder(
    selected_files=["1.dm3", "2.dm3"],
    output_subfolder="selected_keep_resolution",
    keep_original_resolution=True
)
```

Full example:

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=r"C:\work\Lyu\Image segmentation\raw_folder",
    output_path=r"C:\work\Lyu\Image segmentation\converted_images\raw_folder",
    output_format="png",
    output_size=(512, 512)
)

image.convert_selected_images_to_subfolder(
    selected_files=["1.dm3", "2.dm3"],
    output_subfolder="selected_keep_resolution",
    keep_original_resolution=True
)
```

Expected output:

```text
converted_images/
    raw_folder/
        image_registration.csv
        selected_keep_resolution/
            image_registration.csv
            1_<source_id>_resized/
                <source_id>_r000_c000.png
                <source_id>_r000_c001.png
            2_<source_id>_resized/
                <source_id>_r000_c000.png
                <source_id>_r000_c001.png
```

Expected behavior:

1. Selected source images are loaded from `input_path`.
2. Output is directed into `output_path / output_subfolder`.
3. Converted images or patches are saved there.
4. A local `image_registration.csv` is created in the subfolder.
5. The main registration can still be preserved in the master output folder if configured.

This is useful when you want a clean subset folder for segmentation, manual review, or model training.

### 8.2 Case B: Manually copied selected converted images into a subfolder and need to update CSV

Sometimes the user may manually pick images from a converted-output folder and place them into a subfolder.

Example:

```text
converted_images/
    raw_folder/
        image_registration.csv
        A_<id>.png
        B_<id>.png
        C_<id>.png
        selected_for_training/
            A_<id>.png
            C_<id>.png
```

Now the selected subfolder needs its own `image_registration.csv`.

Use:

```python
image.update_registration_csv_for_selected_output_folder()
```

This method asks the user to click-select the folder.

Example:

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    output_path=r"C:\work\Lyu\Image segmentation\converted_images\raw_folder"
)

image.update_registration_csv_for_selected_output_folder()
```

Expected behavior:

1. A folder-selection dialog opens.
2. The user selects:

```text
converted_images/raw_folder/selected_for_training/
```

3. The method finds the master registration CSV in the parent output folder.
4. It scans converted image files inside the selected folder.
5. It matches selected converted images to records in the master registration CSV.
6. It writes a new local CSV:

```text
converted_images/raw_folder/selected_for_training/image_registration.csv
```

This local CSV should contain only the images inside the selected folder.

### 8.3 Directly pass selected folder without dialog

```python
image.update_registration_csv_for_selected_output_folder(
    selected_folder=r"C:\work\Lyu\Image segmentation\converted_images\raw_folder\selected_for_training"
)
```

Expected behavior:

- No folder dialog appears.
- The selected folder is scanned directly.
- A local `image_registration.csv` is generated in that folder.

### 8.4 What happens if an image cannot be matched?

If a selected converted image cannot be matched to the master registration CSV, the method should still record it with a special status such as:

```text
unmatched_selected_folder
```

This helps the user identify images that are present in the selected subset but do not have a clear original-source registration record.

Possible reasons:

- The image was copied from somewhere else.
- The image was renamed.
- The master CSV was missing.
- The image was generated before the registration system was added.
- The stable ID cannot be extracted or matched.

---

## 9. Registration CSV

### 9.1 Master CSV

The master CSV is normally located at:

```python
self.output_path / "image_registration.csv"
```

Example:

```text
converted_images/raw_folder/image_registration.csv
```

The master CSV stores the full conversion history for the output folder.

### 9.2 Selected-subfolder CSV

A selected output subfolder can also have its own CSV:

```text
converted_images/raw_folder/selected_for_training/image_registration.csv
```

This CSV should contain only records relevant to images inside that subfolder.

This is useful for:

- segmentation training subsets,
- manual review subsets,
- selected keep-resolution outputs,
- image cleaning subsets,
- ROI export subsets.

### 9.3 Real-time update

During conversion, the registration CSV is updated after every saved, overwritten, or skipped output image.

This is important because if a long conversion stops early, already processed images still have registration records.

---

## 10. CSV Columns

The registration CSV contains:

| Column | Meaning |
|---|---|
| `registration_key` | Unique source-image key based on source folder and source filename. |
| `source_name` | Original source image filename. |
| `source_path` | Full resolved path to the original image. |
| `source_pixel_size_y` | Source pixel size in Y direction. |
| `source_pixel_size_x` | Source pixel size in X direction. |
| `source_pixel_unit` | Source pixel size unit. |
| `source_shape` | Shape of the original grayscale image data. |
| `source_image_height` | Source image height in pixels. |
| `source_image_width` | Source image width in pixels. |
| `converted_name` | Converted image filename. |
| `converted_path` | Full resolved path to the converted image. |
| `converted_pixel_size_y` | Converted pixel size in Y direction. |
| `converted_pixel_size_x` | Converted pixel size in X direction. |
| `converted_pixel_unit` | Converted pixel size unit. |
| `converted_shape` | Shape of the converted image. |
| `converted_image_height` | Converted image height in pixels. |
| `converted_image_width` | Converted image width in pixels. |
| `keep_original_resolution` | Whether output preserves original pixel size. |
| `status` | `saved`, `overwritten`, `skipped`, `manual`, or unmatched status. |
| `source_image_id` | Stable source ID generated from source path. |
| `last_updated` | Timestamp of this record. |

---

## 11. Core Public Methods

### 11.1 `__init__()`

```python
def __init__(
    self,
    select_input_dir=True,
    select_output_dir=True,
    output_format='png',
    output_size=(512,512),
    pixel_size_unit='nm',
    input_path: Optional[Union[str, Path]] = None,
    output_path: Optional[Union[str, Path]] = None
):
```

Creates an `ImageConverter` object and stores all configuration values.

| Parameter | Default | Meaning |
|---|---:|---|
| `select_input_dir` | `True` | Whether to use a GUI folder selector for input. |
| `select_output_dir` | `True` | Whether to use a GUI folder selector for output. |
| `output_format` | `'png'` | Output image format. |
| `output_size` | `(512,512)` | Output image size or patch size. |
| `pixel_size_unit` | `'nm'` | Preferred pixel-size unit. |
| `input_path` | `None` | Optional explicit input directory. Supports `current`, `.`, and `./`. |
| `output_path` | `None` | Optional explicit output directory. Supports `current`, `.`, and `./`. |

Important instance variables:

| Variable | Meaning |
|---|---|
| `self.input_path` | Source image folder. |
| `self.output_path` | Converted image output folder. |
| `self.selected_files` | Selected source images for partial conversion. |
| `self.image_registration` | In-memory registration dictionary. |
| `self.registration_csv_path` | Path to active registration CSV. |
| `self._overwrite_existing_files` | Temporary overwrite choice for output files. |
| `self._overwrite_registration_records` | Temporary overwrite choice for registration records. |

### 11.2 `convert_to_image()`

```python
def convert_to_image(
    self,
    input_data=None,
    selected_files=None,
    keep_original_resolution=False,
    output_path: Optional[Union[str, Path]] = None,
    load_existing_registration: bool = True,
    auto_brightness_contrast=True,
    auto_contrast_lower_percentile=0.5,
    auto_contrast_upper_percentile=99.5,
    include_subfolders=None
):
```

Main conversion method.

Supports:

1. Full directory conversion.
2. Direct `input_data` conversion.
3. Selected-file conversion.
4. Optional subfolder inclusion.
5. Existing registration loading.
6. Real-time CSV updates.

Important parameters:

| Parameter | Meaning |
|---|---|
| `input_data` | Optional direct input pattern or data. Example: `'*.dm3'`. |
| `selected_files` | Specific source images to convert. |
| `keep_original_resolution` | If `True`, attempt to split source image into original-resolution patches. |
| `output_path` | Optional output directory override. |
| `load_existing_registration` | If `True`, load old CSV before adding new records. |
| `auto_brightness_contrast` | If `True`, use percentile-based contrast. |
| `auto_contrast_lower_percentile` | Lower percentile for contrast clipping. |
| `auto_contrast_upper_percentile` | Upper percentile for contrast clipping. |
| `include_subfolders` | `True`, `False`, or `None`. Controls whether subfolder images are converted. |

Expected result:

- Output image files are created.
- Existing output files trigger overwrite checking.
- Registration CSV is updated.
- If selected files are used, only those files are converted.
- If `include_subfolders=False`, nested images are skipped.
- If `include_subfolders=None`, user is asked whether to include nested images when detected.

### 11.3 `convert_selected_images()`

```python
def convert_selected_images(
    self,
    selected_files,
    keep_original_resolution: bool = True,
    output_path: Optional[Union[str, Path]] = None,
    load_existing_registration: bool = True,
    auto_brightness_contrast: bool = True,
    auto_contrast_lower_percentile: float = 0.5,
    auto_contrast_upper_percentile: float = 99.5
) -> None:
```

Convenience method for converting only selected source images.

Recommended when:

- the whole folder was already converted,
- the user later selects a few images,
- the user wants `keep_original_resolution=True`,
- the user wants to continue updating the same registration CSV.

### 11.4 `convert_selected_images_to_subfolder()`

Converts selected source images and places outputs into a named subfolder under the main output folder.

Example:

```python
image.convert_selected_images_to_subfolder(
    selected_files=["1.dm3", "2.dm3"],
    output_subfolder="selected_for_training",
    keep_original_resolution=True
)
```

Expected output:

```text
output_path/
    selected_for_training/
        image_registration.csv
        ...
```

Use this method when the selected outputs should be grouped into a separate converted subset folder.

### 11.5 `update_registration_csv_for_selected_output_folder()`

Creates or updates an `image_registration.csv` inside a user-selected converted-image folder.

This is designed for the case where the user manually picked converted images and copied them into a new folder.

Example:

```python
image.update_registration_csv_for_selected_output_folder()
```

Expected behavior:

1. User clicks and selects a folder.
2. The method scans images in that folder.
3. The method finds matching records from a master registration CSV.
4. A local CSV is written inside the selected folder.

Direct version:

```python
image.update_registration_csv_for_selected_output_folder(
    selected_folder=r"C:\path\to\converted\selected_for_training"
)
```

### 11.6 `load_image_registration_csv()`

Loads an existing registration CSV into memory.

Usually called automatically when:

```python
load_existing_registration=True
```

Manual use:

```python
image.load_image_registration_csv(
    r"C:\path\to\converted_images\raw_folder\image_registration.csv"
)
```

### 11.7 `export_image_registration_csv()`

Exports the current in-memory registration dictionary to CSV.

Normally writes to:

```python
self.output_path / "image_registration.csv"
```

Can also write to a custom path:

```python
image.export_image_registration_csv(
    r"C:\path\to\custom_registration.csv"
)
```

### 11.8 `manual_register_images()`

Manually register source/converted image metadata.

This is useful if:

- images were converted outside the converter,
- pixel size extraction failed,
- the user needs to manually correct metadata,
- a future GUI allows manual metadata editing.

Example:

```python
image.manual_register_images([
    {
        "source_name": "raw_image.dm4",
        "source_pixel_size": (0.5, 0.5),
        "source_pixel_unit": "nm",
        "source_path": r"C:\data\raw_image.dm4",
        "converted_name": "raw_image_abc123.png",
        "converted_pixel_size": (1.0, 1.0),
        "converted_pixel_unit": "nm",
        "converted_path": r"C:\data\converted\raw_image_abc123.png",
        "source_shape": (1024, 1024),
        "converted_shape": (512, 512),
        "keep_original_resolution": False,
        "status": "manual"
    }
])
```

### 11.9 `autoscale()`

Convert pixel-size scale values between units.

Supported normalized units:

```text
angstrom
nm
um
m
```

Example:

```python
image.autoscale((1.0, 2.0), from_unit="um", to_unit="nm")
```

Expected:

```python
(1000.0, 2000.0)
```

### 11.10 `auto_brightness_contrast()`

Automatically adjust image brightness and contrast using percentile-based clipping.

Default percentiles:

```python
lower_percentile = 0.5
upper_percentile = 99.5
```

Algorithm:

```python
lower_limit = np.percentile(finite_values, lower_percentile)
upper_limit = np.percentile(finite_values, upper_percentile)
adjusted_data = (image_data - lower_limit) / (upper_limit - lower_limit)
adjusted_data = np.clip(adjusted_data, 0, 1)
output = (255 * adjusted_data).astype(np.uint8)
```

---

## 12. Important Internal Helper Methods

### 12.1 `_resolve_path_alias()`

Expected purpose:

Normalize path aliases:

```text
current -> Path(".").resolve()
.       -> Path(".").resolve()
./      -> Path(".").resolve()
```

This helper makes path behavior consistent for `input_path`, `output_path`, and method-level path arguments.

### 12.2 `_ask_include_subfolders()`

Expected purpose:

Ask the user whether images inside subfolders should be converted.

Return:

```python
True
```

or:

```python
False
```

Used when:

```python
include_subfolders=None
```

and supported images are detected inside subfolders.

### 12.3 `_collect_image_file_paths_from_directory()`

Purpose:

Collect image paths from `self.input_path`.

Updated behavior:

- collects top-level images,
- detects subfolder images,
- includes or excludes subfolder images based on `include_subfolders`,
- asks user when `include_subfolders=None`,
- skips files under `self.output_path` to avoid reprocessing converted outputs.

### 12.4 `_resolve_selected_file_paths()`

Purpose:

Convert `selected_files` into full validated image paths.

Supports:

- one string,
- one `Path`,
- list/tuple,
- relative paths,
- absolute paths,
- wildcard patterns.

Validation:

- file must exist,
- file must be supported format,
- duplicates are removed.

### 12.5 `_get_destination_dir_for_source()`

Purpose:

Find correct output directory for each source image.

If the source image is under `input_path`, the relative subfolder structure is preserved under `output_path`.

### 12.6 `_save_image_with_overwrite_check()`

Purpose:

Save a PIL image after checking whether the output file already exists.

Return status:

```text
saved
overwritten
skipped
```

This status is written into CSV.

### 12.7 `_register_converted_image()`

Purpose:

Add or update one converted image record under one source image registration record.

If the converted path already exists, the existing record is updated instead of duplicated.

### 12.8 `_write_selected_folder_registration_csv()`

Expected purpose:

Write a local `image_registration.csv` for a selected converted-image subfolder.

This is used by:

```python
update_registration_csv_for_selected_output_folder()
```

---

## 13. Overwrite Checking

When a converted output file already exists, the converter asks:

```text
Do you want to overwrite it?
```

Available choices:

| Choice | Behavior |
|---|---|
| `Yes` | Overwrite this file only. |
| `No` | Skip this file only. |
| `Yes to all` | Overwrite all duplicate files in current run. |
| `No to all` | Skip all duplicate files in current run. |

The result is recorded as:

```text
saved
overwritten
skipped
```

---

## 14. Pixel Size and Image Size Logic

### 14.1 Source image shape

Source image shape is derived from the processed grayscale image before resizing:

```python
original_shape = self._get_image_shape(image_data)
```

Usually:

```python
(height, width)
```

### 14.2 Resized image pixel size

If the image is resized, pixel size changes.

Formula:

```python
converted_pixel_size_y = original_pixel_size_y * original_height / target_height
converted_pixel_size_x = original_pixel_size_x * original_width / target_width
```

### 14.3 Patch image pixel size

If `keep_original_resolution=True` and the image is split into patches, pixel size remains the same:

```python
converted_pixel_size = source_pixel_size
```

because cropping does not change pixel size.

---

## 15. Important Design Note: Temporary Helper System

The current overwrite checking, registration checking, stable ID generation, CSV export/import, selected-folder CSV update, subfolder confirmation, and scale conversion helpers are still implemented inside `ImageConverter`.

This is acceptable at the current stage because:

- the converter is still evolving,
- selected-output-subfolder workflows were just added,
- ROI export has not been implemented yet,
- image cleaning has not been implemented yet,
- the final metadata schema may still change,
- the unit tests are still expanding.

However, as the program becomes larger, these helper systems should be separated into independent modules or packages.

Recommended future structure:

```text
project_root/
    ImageConverter.py
    image_registration/
        __init__.py
        registry.py
        csv_io.py
        selected_folder_csv.py
        duplicate_checker.py
        scale_utils.py
    image_processing/
        __init__.py
        contrast.py
        grayscale.py
        roi.py
        cleaning.py
```

Possible future responsibilities:

| Future module | Responsibility |
|---|---|
| `duplicate_checker.py` | Overwrite checking and duplicate handling. |
| `registry.py` | Registration dictionary and record updates. |
| `csv_io.py` | CSV import/export. |
| `selected_folder_csv.py` | CSV generation for selected converted-image folders. |
| `scale_utils.py` | Unit normalization and pixel-size conversion. |
| `contrast.py` | Auto brightness/contrast algorithms. |
| `roi.py` | Future ROI selection and export. |
| `cleaning.py` | Future image cleaning tools. |

Current recommendation:

> Keep the helper methods inside `ImageConverter` for now. Refactor only after ROI and image cleaning workflows reuse the same logic.

---

## 16. Recommended Figures to Add Later

### Figure 1. Full folder conversion

```text
raw_folder/
    A.dm3
    B.dm3
    subfolder/
        C.dm3

        |
        v

converted_images/raw_folder/
    image_registration.csv
    A_<id>.png
    B_<id>.png
    subfolder/
        C_<id>.png
```

### Figure 2. Subfolder confirmation

```text
raw_folder/
    A.dm3
    subfolder/
        B.dm3

Prompt:
    Include subfolder images?

Yes:
    A.dm3 and B.dm3 converted

No:
    only A.dm3 converted
```

### Figure 3. Selected source images to output subfolder

```text
raw_folder/
    A.dm3
    B.dm3
    C.dm3

select:
    A.dm3
    C.dm3

        |
        v

converted_images/raw_folder/selected_for_training/
    image_registration.csv
    A_<id>.png
    C_<id>.png
```

### Figure 4. Manual selected converted folder CSV update

```text
converted_images/raw_folder/
    image_registration.csv
    A_<id>.png
    B_<id>.png
    selected_subset/
        A_<id>.png

Run:
    update_registration_csv_for_selected_output_folder()

Result:
    selected_subset/image_registration.csv
```

### Figure 5. Keep original resolution patch output

```text
A.dm3
    |
    v
A_<id>_resized/
    <id>_r000_c000.png
    <id>_r000_c001.png
    <id>_r001_c000.png
    <id>_r001_c001.png
```

---

## 17. Recommended Unit Tests to Add

The previous tests already covered core conversion, stable ID, overwrite behavior, CSV generation, real DM3 loading, and patch export.

For this version, add tests for:

### 17.1 Current path alias

Test:

```python
ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path="current",
    output_path="./"
)
```

Expected:

```python
input_path == Path(".").resolve()
output_path == Path(".").resolve()
```

### 17.2 Subfolder include false

Create:

```text
test_images/
    A.dm3
    subfolder/
        B.dm3
```

Run:

```python
convert_to_image(include_subfolders=False)
```

Expected:

- `A.dm3` converted,
- `B.dm3` not converted.

### 17.3 Subfolder include true

Run:

```python
convert_to_image(include_subfolders=True)
```

Expected:

- both top-level and subfolder images converted,
- subfolder output structure preserved.

### 17.4 Subfolder include prompt

Mock the prompt method to return `True` or `False`.

Expected:

- behavior follows mocked decision.

### 17.5 Convert selected images to output subfolder

Run:

```python
convert_selected_images_to_subfolder(
    selected_files=["A.dm3"],
    output_subfolder="selected"
)
```

Expected:

```text
output_path/selected/
    image_registration.csv
```

and selected output images exist.

### 17.6 Update selected output folder CSV

Prepare a master CSV and a selected folder containing copied converted images.

Run:

```python
update_registration_csv_for_selected_output_folder(selected_folder=...)
```

Expected:

```text
selected_folder/image_registration.csv
```

contains only selected image records.

### 17.7 Unmatched selected folder image

Put an image into selected folder that does not exist in master CSV.

Expected:

- local CSV still created,
- status is `unmatched_selected_folder`.

---

## 18. Troubleshooting

### 18.1 Converted images are written into the wrong folder

Likely cause:

- `output_path` was not explicitly set,
- `current` was used unintentionally,
- converter object was created from a different working directory.

Fix:

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=r"C:\path\to\raw_folder",
    output_path=r"C:\path\to\converted_images\raw_folder"
)
```

### 18.2 Subfolder images were converted but should not have been

Use:

```python
image.convert_to_image(include_subfolders=False)
```

### 18.3 Subfolder images were not converted

Use:

```python
image.convert_to_image(include_subfolders=True)
```

or:

```python
image.convert_to_image(include_subfolders=None)
```

and choose Yes when prompted.

### 18.4 Local selected-folder CSV is missing records

Possible causes:

- selected images were renamed,
- master CSV is missing,
- master CSV is in a different output folder,
- selected image filenames no longer contain stable IDs,
- copied images did not come from this converter.

Fix:

1. Confirm the master CSV exists.
2. Confirm `output_path` points to the folder containing the master CSV.
3. Re-run selected-folder CSV update.
4. Check rows with `unmatched_selected_folder`.

### 18.5 Old master CSV records disappeared

Possible causes:

- wrong output folder was used,
- `load_existing_registration=False`,
- a new CSV was written in a different location.

Fix:

```python
image.convert_to_image(
    load_existing_registration=True
)
```

and explicitly specify `output_path`.

---

## 19. Recommended README Example

```python
from ImageConverter import ImageConverter

raw_dir = r"C:\work\Lyu\Image segmentation\raw_folder"
out_dir = r"C:\work\Lyu\Image segmentation\converted_images\raw_folder"

# Step 1: batch convert all images.
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=raw_dir,
    output_path=out_dir,
    output_format="png",
    output_size=(512, 512),
    pixel_size_unit="nm"
)

image.convert_to_image(
    keep_original_resolution=False,
    auto_brightness_contrast=True,
    include_subfolders=None
)

# Step 2: later select a few original images for high-resolution patch export.
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=raw_dir,
    output_path=out_dir,
    output_format="png",
    output_size=(512, 512),
    pixel_size_unit="nm"
)

image.convert_selected_images(
    selected_files=["1.dm3", "2.dm3"],
    keep_original_resolution=True,
    load_existing_registration=True
)

# Step 3: convert selected images into a special subset folder.
image.convert_selected_images_to_subfolder(
    selected_files=["1.dm3", "2.dm3"],
    output_subfolder="selected_for_training",
    keep_original_resolution=True
)

# Step 4: if selected converted images were manually copied into a folder,
# generate/update a CSV for that selected converted folder.
image.update_registration_csv_for_selected_output_folder(
    selected_folder=r"C:\work\Lyu\Image segmentation\converted_images\raw_folder\selected_for_training"
)
```

---

## 20. Summary

The v3 `ImageConverter` workflow now supports realistic microscopy image preparation:

1. Convert a full folder.
2. Decide whether subfolder images should be included.
3. Use `current` / `./` for quick current-folder workflows.
4. Later select only a few original images for patch export.
5. Place selected outputs into a converted-output subfolder.
6. Generate a local registration CSV for that selected converted subfolder.
7. Preserve traceability through stable IDs and registration records.
8. Continue building toward future ROI and image-cleaning workflows.

The most important practical improvement is that selected datasets can now be organized into their own folders while still maintaining metadata traceability through `image_registration.csv`.
