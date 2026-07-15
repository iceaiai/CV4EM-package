# Segmentation Utilities Usage Guide

## Overview

`segmentation_simplified.py` provides utilities for:

1. segmenting particles with Otsu thresholding;
2. converting SAM3 predictions into consecutive-ID instance masks;
3. comparing predictions with a reference mask;
4. visualizing Otsu and SAM3 results;
5. loading and saving instance masks.

All instance masks use:

```text
0 = background
1 = object 1
2 = object 2
3 = object 3
...
n = object n
```

The binary metrics compare the total foreground region only. They do not match individual predicted objects to individual reference objects.

---

## Import

```python
from segmentation_simplified import (
    calculate_binary_metrics,
    count_instances,
    instance_mask_to_rgb,
    load_instance_mask,
    print_segmentation_summary,
    sam3_output_to_result,
    save_instance_mask,
    segment_with_otsu,
    show_instance_mask,
    show_otsu_result,
    show_sam3_result,
)
```

Common additional imports:

```python
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
```

---

# Reference Instance Masks

A reference instance mask can be obtained in two common ways.

## Load an Existing Mask

```python
reference_mask = load_instance_mask(
    "reference_mask.png"
)
```

Supported formats:

```text
.png
.tif
.tiff
.npy
```

## Create a Mask from AnyLabeling JSON

Use the separate `MakeMasks` module:

```python
from make_masks_simplified import MakeMasks


mask_maker = MakeMasks(
    input_dir=".",
    output_dir=".",
    default_image_shape=(512, 512),
)

annotation_data = mask_maker.load_anylabeling_json(
    "annotation.json"
)

reference_mask = mask_maker.create_instance_mask_from_json(
    annotation_data,
    image_shape=(512, 512),
)
```

---

# Core Segmentation Functions

## 1. `segment_with_otsu()`

### Purpose

`segment_with_otsu()` segments a processed 2D grayscale image with Otsu thresholding.

It can use either:

- connected components; or
- watershed separation.

### Signature

```python
result = segment_with_otsu(
    image,
    particle_color="black",
    min_size=50,
    fill_holes=False,
    use_watershed=False,
    min_distance=8,
)
```

### Parameters

- `image`: processed 2D grayscale image as a PIL image or NumPy array.
- `particle_color`: `"black"` or `"white"`.
- `min_size`: remove connected foreground regions smaller than this number of pixels.
- `fill_holes`: fill small holes inside foreground regions.
- `use_watershed`: separate touching particles with watershed.
- `min_distance`: minimum peak distance used to create watershed markers.

### Choosing `particle_color`

Use:

```python
particle_color="white"
```

when particles are brighter than the background.

This is common for STEM-HAADF images.

Use:

```python
particle_color="black"
```

when particles are darker than the background.

This is common for conventional bright-field TEM images.

Always choose the value from the actual displayed image because contrast may be inverted during acquisition or processing.

### Return Value

The function returns a dictionary:

```python
{
    "method": "Otsu + Connected Components",
    "binary_mask": ...,
    "instance_mask": ...,
    "parameters": {
        "particle_color": ...,
        "foreground_type": ...,
        "threshold_value": ...,
        "min_size": ...,
        "fill_holes": ...,
        "use_watershed": ...,
        "min_distance": ...,
    },
}
```

The returned `instance_mask` has:

```text
dtype: int32
0: background
1, 2, 3, ...: particle IDs
```

### Example: Bright Particles on a Dark Background

```python
image = Image.open("stem_haadf_image.tif")

otsu_result = segment_with_otsu(
    image,
    particle_color="white",
    min_size=30,
    fill_holes=False,
    use_watershed=False,
)
```

### Example: Dark Particles on a Bright Background

```python
image = Image.open("bright_field_tem.tif")

otsu_result = segment_with_otsu(
    image,
    particle_color="black",
    min_size=30,
    fill_holes=False,
    use_watershed=False,
)
```

### Example: Separate Touching Particles with Watershed

```python
otsu_result = segment_with_otsu(
    image,
    particle_color="black",
    min_size=30,
    fill_holes=True,
    use_watershed=True,
    min_distance=8,
)
```

A smaller `min_distance` usually creates more watershed markers and may split particles more aggressively.

A larger `min_distance` usually creates fewer markers and may merge nearby particles.

### Access the Results

```python
binary_mask = otsu_result["binary_mask"]
instance_mask = otsu_result["instance_mask"]

print("Method:", otsu_result["method"])
print("Objects:", count_instances(instance_mask))
print("Threshold:", otsu_result["parameters"]["threshold_value"])
```

---

## 2. `sam3_output_to_result()`

### Purpose

`sam3_output_to_result()` converts raw SAM3 predictions into the same instance-mask format used by Otsu.

SAM3 predictions are processed from highest to lowest confidence.

When predicted masks overlap, the higher-confidence prediction keeps the overlapping pixels.

### Expected SAM3 Output

The input mapping must contain:

```python
sam3_output = {
    "masks": ...,
}
```

It may also contain:

```python
sam3_output = {
    "masks": ...,
    "scores": ...,
    "boxes": ...,
}
```

Accepted mask shapes include:

```text
(number_of_predictions, height, width)
(number_of_predictions, 1, height, width)
(height, width)
```

### Signature

```python
sam3_result = sam3_output_to_result(
    sam3_output,
    mask_threshold=0.5,
    min_size=0,
    fill_holes=False,
    hole_area_threshold=50,
)
```

### Parameters

- `output`: raw SAM3 prediction mapping.
- `mask_threshold`: threshold used when masks contain probabilities instead of Boolean values.
- `min_size`: remove predicted regions smaller than this number of pixels.
- `fill_holes`: fill small holes within each predicted object.
- `hole_area_threshold`: maximum hole area to fill.

### Return Value

```python
{
    "method": "SAM3",
    "binary_mask": ...,
    "instance_mask": ...,
    "kept_indices": ...,
    "sam3_output": ...,
    "parameters": {
        "mask_threshold": ...,
        "min_size": ...,
        "fill_holes": ...,
        "hole_area_threshold": ...,
        "input_predictions": ...,
        "kept_predictions": ...,
    },
}
```

### Example: Default Post-Processing

```python
sam3_result = sam3_output_to_result(
    sam3_output
)
```

### Example: Remove Small Predictions and Fill Holes

```python
sam3_result = sam3_output_to_result(
    sam3_output,
    mask_threshold=0.5,
    min_size=30,
    fill_holes=True,
    hole_area_threshold=30,
)
```

### Access the Results

```python
sam3_instance_mask = sam3_result["instance_mask"]

print("Input predictions:", sam3_result["parameters"]["input_predictions"])
print("Kept predictions:", sam3_result["parameters"]["kept_predictions"])
print("Kept indices:", sam3_result["kept_indices"])
```

---

## 3. `calculate_binary_metrics()`

### Purpose

`calculate_binary_metrics()` compares the total predicted foreground area with the total reference foreground area.

It calculates:

```text
IoU
Dice
Precision
Recall
Predicted area
Reference area
```

Individual object IDs are not matched.

For example, object `1` in the prediction is not directly compared with object `1` in the reference mask.

### Signature

```python
metrics = calculate_binary_metrics(
    pred_mask,
    reference_mask,
)
```

### Parameters

- `pred_mask`: predicted 2D instance mask.
- `reference_mask`: reference 2D instance mask.

The masks must have identical dimensions.

### Return Value

```python
{
    "IoU": ...,
    "Dice": ...,
    "Precision": ...,
    "Recall": ...,
    "Predicted area": ...,
    "Reference area": ...,
}
```

### Example

```python
metrics = calculate_binary_metrics(
    otsu_result["instance_mask"],
    reference_mask,
)

for metric_name, value in metrics.items():
    print(metric_name, value)
```

### Compare Otsu and SAM3

```python
otsu_metrics = calculate_binary_metrics(
    otsu_result["instance_mask"],
    reference_mask,
)

sam3_metrics = calculate_binary_metrics(
    sam3_result["instance_mask"],
    reference_mask,
)

print("Otsu IoU:", otsu_metrics["IoU"])
print("SAM3 IoU:", sam3_metrics["IoU"])
```

---

# Core Visualization Functions

## 4. `instance_mask_to_rgb()`

### Purpose

`instance_mask_to_rgb()` converts a 2D instance mask into an RGB image for display.

The background is white. Each object receives a color from a Matplotlib color map.

### Signature

```python
rgb_mask = instance_mask_to_rgb(
    mask,
    cmap_name="tab20",
    show_boundaries=True,
    boundary_color=(0, 0, 0),
)
```

### Parameters

- `mask`: 2D instance mask.
- `cmap_name`: Matplotlib color-map name.
- `show_boundaries`: draw object boundaries when `True`.
- `boundary_color`: RGB boundary color using values from `0.0` to `1.0`.

### Return Value

```python
np.ndarray
```

The returned array has shape:

```text
(height, width, 3)
```

### Example

```python
rgb_mask = instance_mask_to_rgb(
    reference_mask,
    cmap_name="tab20",
    show_boundaries=True,
)

plt.imshow(rgb_mask)
plt.axis("off")
plt.show()
```

### Example: Red Boundaries

```python
rgb_mask = instance_mask_to_rgb(
    reference_mask,
    boundary_color=(1, 0, 0),
)
```

---

## 5. `show_instance_mask()`

### Purpose

`show_instance_mask()` displays an instance mask on an existing Matplotlib axis.

### Signature

```python
show_instance_mask(
    mask,
    ax,
    title,
    cmap_name="tab20",
    show_boundaries=True,
)
```

### Parameters

- `mask`: 2D instance mask.
- `ax`: existing Matplotlib axis.
- `title`: panel title.
- `cmap_name`: Matplotlib color map.
- `show_boundaries`: display object boundaries when `True`.

### Return Value

The function returns `None`.

### Example

```python
figure, axis = plt.subplots(figsize=(6, 6))

show_instance_mask(
    reference_mask,
    axis,
    title="Reference Instance Mask",
    cmap_name="tab20",
    show_boundaries=True,
)

plt.show()
```

---

## 6. `show_otsu_result()`

### Purpose

`show_otsu_result()` displays four panels:

1. original image;
2. reference instance mask;
3. Otsu binary mask;
4. Otsu instance mask.

It also prints a segmentation summary and returns the binary metrics.

### Signature

```python
metrics = show_otsu_result(
    image,
    reference_mask,
    result,
    title,
    cmap_name="tab20",
    show_boundaries=True,
)
```

### Parameters

- `image`: original grayscale or RGB image.
- `reference_mask`: reference instance mask.
- `result`: dictionary returned by `segment_with_otsu()`.
- `title`: overall figure and summary title.
- `cmap_name`: instance-mask color map.
- `show_boundaries`: display object boundaries.

### Return Value

```python
dict[str, float | int]
```

### Example

```python
otsu_metrics = show_otsu_result(
    image,
    reference_mask,
    otsu_result,
    title="Particle Segmentation with Otsu",
    cmap_name="tab20",
    show_boundaries=True,
)
```

---

## 7. `show_sam3_result()`

### Purpose

`show_sam3_result()` displays four panels:

1. original image;
2. reference mask;
3. SAM3 prediction overlays, IDs, boxes, and confidence scores;
4. final SAM3 instance mask.

The function accepts either:

- raw SAM3 output; or
- a processed result from `sam3_output_to_result()`.

### Signature

```python
sam3_result = show_sam3_result(
    image,
    reference_mask,
    output,
    title,
    cmap_name="tab20",
)
```

### Return Value

The returned dictionary contains the processed SAM3 result plus:

```python
sam3_result["metrics"]
```

### Example: Raw SAM3 Output

```python
sam3_result = show_sam3_result(
    image,
    reference_mask,
    sam3_output,
    title="Particle Segmentation with SAM3",
    cmap_name="tab20",
)
```

In this case, default SAM3 post-processing is applied automatically.

### Example: Custom SAM3 Post-Processing

```python
sam3_result = sam3_output_to_result(
    sam3_output,
    mask_threshold=0.5,
    min_size=30,
    fill_holes=True,
    hole_area_threshold=30,
)

sam3_result = show_sam3_result(
    image,
    reference_mask,
    sam3_result,
    title="Particle Segmentation with SAM3",
    cmap_name="tab20",
)
```

---

## 8. `print_segmentation_summary()`

### Purpose

`print_segmentation_summary()` prints:

- method name;
- number of reference objects;
- number of detected objects;
- segmentation parameters;
- IoU, Dice, Precision, Recall, and areas.

### Signature

```python
print_segmentation_summary(
    title,
    result,
    reference_mask,
    metrics=None,
)
```

### Parameters

- `title`: summary title.
- `result`: Otsu or processed SAM3 result.
- `reference_mask`: reference instance mask.
- `metrics`: optional metrics dictionary.

When `metrics` is omitted, the function calculates the metrics automatically.

### Example

```python
print_segmentation_summary(
    title="Otsu Evaluation",
    result=otsu_result,
    reference_mask=reference_mask,
)
```

### Example: Reuse Existing Metrics

```python
metrics = calculate_binary_metrics(
    otsu_result["instance_mask"],
    reference_mask,
)

print_segmentation_summary(
    title="Otsu Evaluation",
    result=otsu_result,
    reference_mask=reference_mask,
    metrics=metrics,
)
```

---

## 9. `count_instances()`

### Purpose

`count_instances()` counts the unique nonzero object IDs in an instance mask.

### Signature

```python
number_of_objects = count_instances(mask)
```

### Return Value

```python
int
```

### Example

```python
number_of_reference_objects = count_instances(
    reference_mask
)

number_of_otsu_objects = count_instances(
    otsu_result["instance_mask"]
)

print("Reference:", number_of_reference_objects)
print("Otsu:", number_of_otsu_objects)
```

The function counts unique IDs, not the maximum mask value.

---

# Mask Input and Output Functions

## 10. `load_instance_mask()`

### Purpose

`load_instance_mask()` loads an existing 2D instance mask.

Supported formats:

```text
.png
.tif
.tiff
.npy
```

### Signature

```python
mask = load_instance_mask(mask_path)
```

### Validation

The mask must:

- be two-dimensional;
- contain only finite values;
- contain nonnegative integer labels.

### Return Value

```python
np.ndarray
```

The returned mask has:

```text
dtype: int32
```

### Examples

```python
reference_mask = load_instance_mask(
    "reference_mask.png"
)
```

```python
reference_mask = load_instance_mask(
    "reference_mask.tif"
)
```

```python
reference_mask = load_instance_mask(
    "reference_mask.npy"
)
```

---

## 11. `save_instance_mask()`

### Purpose

`save_instance_mask()` saves a 2D instance mask as an NPY file.

If the supplied path does not end in `.npy`, the suffix is changed automatically.

The parent folder is created automatically.

### Signature

```python
saved_path = save_instance_mask(
    mask,
    output_path,
)
```

### Return Value

```python
Path
```

### Example

```python
saved_path = save_instance_mask(
    otsu_result["instance_mask"],
    "results/otsu_instance_mask.npy",
)

print(saved_path)
```

### Example Without an Extension

```python
saved_path = save_instance_mask(
    sam3_result["instance_mask"],
    "results/sam3_instance_mask",
)
```

The saved file will be:

```text
results/sam3_instance_mask.npy
```

---

# Recommended Workflows

## Workflow 1: Otsu Segmentation and Evaluation

```python
from PIL import Image

from segmentation_simplified import (
    load_instance_mask,
    save_instance_mask,
    segment_with_otsu,
    show_otsu_result,
)


image = Image.open("particle_image.tif")

reference_mask = load_instance_mask(
    "reference_mask.npy"
)

otsu_result = segment_with_otsu(
    image,
    particle_color="black",
    min_size=30,
    fill_holes=False,
    use_watershed=True,
    min_distance=8,
)

otsu_metrics = show_otsu_result(
    image,
    reference_mask,
    otsu_result,
    title="Particle Segmentation with Otsu",
)

save_instance_mask(
    otsu_result["instance_mask"],
    "results/otsu_instance_mask.npy",
)
```

---

## Workflow 2: SAM3 Segmentation and Evaluation

```python
from segmentation_simplified import (
    load_instance_mask,
    sam3_output_to_result,
    save_instance_mask,
    show_sam3_result,
)


reference_mask = load_instance_mask(
    "reference_mask.npy"
)

sam3_result = sam3_output_to_result(
    sam3_output,
    mask_threshold=0.5,
    min_size=30,
    fill_holes=True,
    hole_area_threshold=30,
)

sam3_result = show_sam3_result(
    image,
    reference_mask,
    sam3_result,
    title="Particle Segmentation with SAM3",
)

save_instance_mask(
    sam3_result["instance_mask"],
    "results/sam3_instance_mask.npy",
)
```

---

## Workflow 3: Compare Otsu and SAM3

```python
from segmentation_simplified import (
    calculate_binary_metrics,
    sam3_output_to_result,
    segment_with_otsu,
)


otsu_result = segment_with_otsu(
    image,
    particle_color="black",
    min_size=30,
    use_watershed=True,
)

sam3_result = sam3_output_to_result(
    sam3_output,
    min_size=30,
)

otsu_metrics = calculate_binary_metrics(
    otsu_result["instance_mask"],
    reference_mask,
)

sam3_metrics = calculate_binary_metrics(
    sam3_result["instance_mask"],
    reference_mask,
)

print("Otsu IoU:", otsu_metrics["IoU"])
print("SAM3 IoU:", sam3_metrics["IoU"])

print("Otsu Dice:", otsu_metrics["Dice"])
print("SAM3 Dice:", sam3_metrics["Dice"])
```

---

# Important Notes

## The Input Image Must Be Processed Before Otsu Segmentation

`segment_with_otsu()` expects a 2D grayscale image.

RGB images must be converted to grayscale before segmentation.

For example:

```python
image = Image.open("particle_image.png").convert("L")
```

## Binary Metrics Do Not Measure Instance Matching

The current metrics compare:

```text
all predicted foreground pixels
versus
all reference foreground pixels
```

They do not calculate:

- object-to-object IoU;
- matched true-positive instances;
- false-positive particle count;
- false-negative particle count;
- average precision.

## SAM3 Overlap Handling

SAM3 predictions are sorted from highest to lowest confidence.

The higher-confidence object receives overlapping pixels first. Lower-confidence objects keep only unoccupied pixels.

## Otsu Watershed Parameters

`min_size` controls small-region removal.

`min_distance` controls the spacing between watershed markers.

Both parameters may require adjustment for different magnifications, particle sizes, and image resolutions.

## Private Helper Functions

Functions beginning with `_` are internal implementation helpers.

Normal users should use only the public functions documented above.
