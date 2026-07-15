# MakeMasks Usage Guide

## Overview

`MakeMasks` converts AnyLabeling JSON annotations into either:

1. instance masks for image analysis or segmentation training; or
2. COCO-format JSON annotations for object detection and instance segmentation.

Supported area-based shape types:

```text
polygon
rectangle
circle
```

Unsupported non-area shape types are skipped:

```text
point
line
linestrip
```

Instance mask values are assigned consecutively:

```text
0 = background
1 = object 1
2 = object 2
...
n = object n
```

A single 2D instance mask cannot preserve multiple object IDs at the same overlapping pixel. When two objects overlap, the object drawn later overwrites the earlier object in the overlap.

COCO annotations store each object independently, so overlapping objects remain separate annotations.

---

## Import

```python
import numpy as np

from make_masks_simplified import MakeMasks
```

Rename the import module if your Python file uses a different filename.

---

## Create a `MakeMasks` Object

```python
mask_maker = MakeMasks(
    input_dir=r"C:\data\annotations",
    output_dir=r"C:\data\outputs",
    output_folder_name="masks",
    default_image_shape=(512, 512),
)
```

### Constructor Parameters

- `input_dir`: folder containing AnyLabeling JSON files.
- `output_dir`: folder used for masks and COCO files.
- `output_folder_name`: name of the mask subfolder created inside `output_dir`.
- `default_image_shape`: default image shape as `(height, width)`.

When `input_dir` or `output_dir` is not provided, the current working directory is used.

### Example: Use the Current Directory

```python
mask_maker = MakeMasks(
    default_image_shape=(512, 512)
)
```

The default mask folder will be:

```text
./masks
```

---

# Core Mask Methods

## 1. `load_anylabeling_json()`

### Purpose

`load_anylabeling_json()` loads one AnyLabeling JSON annotation file and returns the decoded JSON content as a Python dictionary.

### Signature

```python
data = mask_maker.load_anylabeling_json(json_path)
```

### Parameters

- `json_path`: path to one AnyLabeling JSON file.

### Return Value

```python
Dict[str, Any]
```

### Example

```python
json_path = r"C:\data\annotations\sample.json"

data = mask_maker.load_anylabeling_json(json_path)

print(data.keys())
print("Number of shapes:", len(data.get("shapes", [])))
```

---

## 2. `create_instance_mask_from_json()`

### Purpose

`create_instance_mask_from_json()` converts loaded AnyLabeling annotation data into one 2D instance mask.

Object IDs are assigned in annotation order:

```text
first valid object  -> 1
second valid object -> 2
third valid object  -> 3
```

Invalid or unsupported shapes are skipped.

### Signature

```python
mask = mask_maker.create_instance_mask_from_json(
    data,
    image_shape=None,
)
```

### Parameters

- `data`: loaded AnyLabeling JSON dictionary.
- `image_shape`: optional shape as `(height, width)`. When omitted, `default_image_shape` is used.

### Return Value

```python
np.ndarray
```

The returned mask has:

```text
dtype: int32
shape: (height, width)
```

### Example: Use the Default Image Shape

```python
data = mask_maker.load_anylabeling_json(
    r"C:\data\annotations\sample.json"
)

mask = mask_maker.create_instance_mask_from_json(data)

print("Mask shape:", mask.shape)
print("Object IDs:", np.unique(mask))
print("Highest object ID:", mask.max())
```

### Example: Override the Image Shape

```python
mask = mask_maker.create_instance_mask_from_json(
    data,
    image_shape=(768, 1024),
)
```

The image shape must always be written as:

```text
(height, width)
```

### Overlapping Objects

If two objects overlap, the object drawn later replaces the earlier object only in the overlapping pixels.

Use COCO output when every overlapping object must remain independently available for training.

---

## 3. `save_mask()`

### Purpose

`save_mask()` saves one instance mask to disk.

Supported formats:

```text
.png
.tif
.tiff
.npy
```

PNG and TIFF masks are saved as `uint16`.

NPY preserves the NumPy array directly and is recommended when the mask may contain more than 65,535 instance IDs.

### Signature

```python
saved_path = mask_maker.save_mask(
    mask,
    save_path,
)
```

### Parameters

- `mask`: instance mask as a NumPy array.
- `save_path`: complete output path including the file extension.

### Return Value

```python
Path
```

### Example: Save as PNG

```python
saved_path = mask_maker.save_mask(
    mask,
    r"C:\data\outputs\masks\sample_mask.png",
)

print(saved_path)
```

### Example: Save as NPY

```python
saved_path = mask_maker.save_mask(
    mask,
    r"C:\data\outputs\masks\sample_mask.npy",
)
```

The parent folder is created automatically when it does not already exist.

---

## 4. `save_all_masks()`

### Purpose

`save_all_masks()` finds every `.json` file directly inside `input_dir`, converts each one into an instance mask, and saves the results in the mask output folder.

It does not search subfolders recursively.

### Signature

```python
saved_files = mask_maker.save_all_masks(
    image_shape=None,
    output_format="png",
    save_npy=True,
    overwrite=True,
)
```

### Parameters

- `image_shape`: optional `(height, width)` override for all JSON files.
- `output_format`: `png`, `tif`, `tiff`, or `npy`.
- `save_npy`: also save an NPY copy when the main format is not already NPY.
- `overwrite`: overwrite existing files when `True`.

### Return Value

A dictionary keyed by the original JSON filename:

```python
{
    "sample.json": {
        "mask_path": Path(...),
        "num_objects": 5,
        "mask_shape": (512, 512),
        "npy_path": Path(...),
    }
}
```

### Example: Save PNG and NPY Masks

```python
mask_maker = MakeMasks(
    input_dir=r"C:\data\annotations",
    output_dir=r"C:\data\outputs",
    default_image_shape=(512, 512),
)

saved_files = mask_maker.save_all_masks(
    output_format="png",
    save_npy=True,
    overwrite=True,
)

for json_name, record in saved_files.items():
    print(json_name)
    print("Mask:", record["mask_path"])
    print("Number of objects:", record["num_objects"])
    print("Mask shape:", record["mask_shape"])
    print("NPY:", record.get("npy_path"))
```

### Example: Save Only TIFF Masks

```python
saved_files = mask_maker.save_all_masks(
    image_shape=(768, 1024),
    output_format="tif",
    save_npy=False,
    overwrite=False,
)
```

### Example: Save Only NPY Masks

```python
saved_files = mask_maker.save_all_masks(
    output_format="npy",
    save_npy=False,
)
```

When no JSON files are found in `input_dir`, the method raises `FileNotFoundError`.

---

## 5. `show_instance_mask()`

### Purpose

`show_instance_mask()` displays an instance mask with a categorical color map and object-ID color bar.

### Signature

```python
mask_maker.show_instance_mask(
    mask,
    title="Instance Mask",
)
```

### Return Value

The method returns `None` and displays a Matplotlib figure.

### Example

```python
mask_maker.show_instance_mask(
    mask,
    title="Au Nanoparticle Instances",
)
```

This method is intended for visualization only. It does not modify or save the mask.

---

# Core COCO Methods

## 6. `convert_one_json_to_coco()`

### Purpose

`convert_one_json_to_coco()` converts one AnyLabeling JSON file into a complete COCO-format dataset containing one image record and all valid object annotations.

Each object is stored separately, so overlapping objects are preserved.

Rectangles are converted into four-point polygons.

Circles are approximated using multiple polygon points.

### Signature

```python
coco_data = mask_maker.convert_one_json_to_coco(
    json_path,
    image_file_name=None,
    image_shape=None,
    category_name="nanostructure",
    category_id=1,
    circle_points=36,
    save_path=None,
)
```

### Parameters

- `json_path`: path to one AnyLabeling JSON file.
- `image_file_name`: corresponding image filename written to COCO.
- `image_shape`: image shape as `(height, width)`.
- `category_name`: COCO category name.
- `category_id`: integer COCO category ID.
- `circle_points`: number of polygon vertices used to approximate each circle.
- `save_path`: optional output COCO JSON path.

When `image_file_name` is omitted, the method first uses `imagePath` from the AnyLabeling JSON. If it is unavailable, `<json_stem>.png` is used.

When `save_path` is omitted, the output is saved as:

```text
output_dir/coco_annotations/<json_stem>_coco.json
```

### Return Value

```python
Dict[str, Any]
```

The dictionary contains:

```text
images
annotations
categories
```

### Example

```python
coco_data = mask_maker.convert_one_json_to_coco(
    json_path=r"C:\data\annotations\sample.json",
    image_file_name="sample.png",
    image_shape=(512, 512),
    category_name="nanostructure",
    category_id=1,
    circle_points=36,
    save_path=r"C:\data\outputs\coco\sample_coco.json",
)

print("Images:", len(coco_data["images"]))
print("Annotations:", len(coco_data["annotations"]))
print("Categories:", coco_data["categories"])
```

### Example: Use Default Output Settings

```python
coco_data = mask_maker.convert_one_json_to_coco(
    r"C:\data\annotations\sample.json"
)
```

---

## 7. `save_all_as_coco()`

### Purpose

`save_all_as_coco()` converts every JSON file directly inside `input_dir` into one combined COCO dataset.

The output contains:

- one `images` record for each JSON file;
- one independent `annotations` record for each valid object;
- one category definition.

### Signature

```python
coco_dataset = mask_maker.save_all_as_coco(
    image_shape=None,
    category_name="nanostructure",
    category_id=1,
    image_extension=".png",
    circle_points=36,
    save_path=None,
)
```

### Parameters

- `image_shape`: shape applied to all images as `(height, width)`.
- `category_name`: shared COCO category name.
- `category_id`: shared category ID.
- `image_extension`: fallback image extension when `imagePath` is missing.
- `circle_points`: polygon vertices used to approximate circles.
- `save_path`: optional combined COCO JSON path.

When `save_path` is omitted, the output is saved as:

```text
output_dir/coco_annotations.json
```

### Return Value

```python
Dict[str, Any]
```

### Example

```python
mask_maker = MakeMasks(
    input_dir=r"C:\data\annotations",
    output_dir=r"C:\data\outputs",
    default_image_shape=(512, 512),
)

coco_dataset = mask_maker.save_all_as_coco(
    image_shape=(512, 512),
    category_name="nanostructure",
    category_id=1,
    image_extension=".png",
    circle_points=36,
    save_path=r"C:\data\outputs\coco_annotations.json",
)

print("Number of images:", len(coco_dataset["images"]))
print(
    "Number of annotations:",
    len(coco_dataset["annotations"]),
)
print("Categories:", coco_dataset["categories"])
```

### Example: Use the Default Save Path

```python
coco_dataset = mask_maker.save_all_as_coco()
```

---

# Recommended Workflows

## Workflow 1: Convert All JSON Files to Instance Masks

```python
from make_masks_simplified import MakeMasks


mask_maker = MakeMasks(
    input_dir=r"C:\data\annotations",
    output_dir=r"C:\data\outputs",
    default_image_shape=(512, 512),
)

saved_files = mask_maker.save_all_masks(
    output_format="png",
    save_npy=True,
    overwrite=True,
)

print(saved_files)
```

---

## Workflow 2: Inspect One Mask Before Batch Conversion

```python
import numpy as np

from make_masks_simplified import MakeMasks


mask_maker = MakeMasks(
    input_dir=r"C:\data\annotations",
    output_dir=r"C:\data\outputs",
    default_image_shape=(512, 512),
)

data = mask_maker.load_anylabeling_json(
    r"C:\data\annotations\sample.json"
)

mask = mask_maker.create_instance_mask_from_json(data)

print("Shape:", mask.shape)
print("IDs:", np.unique(mask))

mask_maker.show_instance_mask(
    mask,
    title="Sample Instance Mask",
)

mask_maker.save_mask(
    mask,
    r"C:\data\outputs\masks\sample_mask.png",
)
```

---

## Workflow 3: Build One COCO Dataset from All JSON Files

```python
from make_masks_simplified import MakeMasks


mask_maker = MakeMasks(
    input_dir=r"C:\data\annotations",
    output_dir=r"C:\data\outputs",
    default_image_shape=(512, 512),
)

coco_dataset = mask_maker.save_all_as_coco(
    category_name="nanostructure",
    category_id=1,
    image_extension=".png",
    circle_points=36,
)

print("Images:", len(coco_dataset["images"]))
print("Annotations:", len(coco_dataset["annotations"]))
```

---

# Important Notes

## Image Shape

Always provide image shape as:

```text
(height, width)
```

For example:

```python
image_shape=(768, 1024)
```

means:

```text
height = 768
width  = 1024
```

## Instance Masks and Overlap

A 2D mask stores only one value per pixel. It cannot preserve two object IDs at the same pixel.

Use instance masks when a single visible ID per pixel is acceptable.

Use COCO annotations when overlapping objects must remain independent.

## Circle Conversion in COCO

COCO polygon segmentation does not have a native circle primitive. Each circle is approximated by a polygon.

For example:

```python
circle_points=36
```

uses 36 vertices per circle.

A larger value creates a smoother approximation but increases annotation size.