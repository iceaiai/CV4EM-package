# ImageConverter Usage Guide

## Overview

`ImageConverter` loads microscopy or standard image files, converts them into a selected image format and dimension, and records the original and converted image information in `image_registration.csv`.

`auto_brightness_contrast()` and `autoscale()` are standalone utility functions. They can be imported and used without creating an `ImageConverter` object, while `ImageConverter` also uses the same functions internally.

Examples of supported input formats:

```text
dm3, dm4, tif, png, jpg, jpeg, gif
```

Exaples of supported output formats:

```text
tif, png, jpg, jpeg, gif
```

The registration CSV contains six columns:

```text
original_image_name
original_dim
original_size
converted_image_name
converted_dim
converted_size
```

Image names retain their file extensions, and pixel sizes retain their units. For example:

```text
Au cube A41-6k-5.dm4    (2048, 2048)    0.26541nm    0b152bdcf0.png    (512, 512)    1.06164nm
```

## Import

```python
from pathlib import Path

import hyperspy.api as hs
import numpy as np

from image_converter_with_standalone_utilities import (
    ImageConverter,
    auto_brightness_contrast,
    autoscale,
)
```

## Create an ImageConverter Object

Create the converter before using any core method.

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=r'C:\data\raw_images',
    output_path=r'C:\data\converted_images',
    output_format='png',
    output_size=(512, 512),
    pixel_size_unit='nm',
    include_subfolders=True
)
```

Important constructor settings:

- `select_input_dir=True` opens a dialog for choosing the input folder.
- `select_input_dir=False` uses `input_path`.
- `select_output_dir=True` opens a dialog for choosing the output folder.
- `select_output_dir=False` uses `output_path` or creates the default converted-image folder.
- `output_format` sets the converted image extension.
- `output_size` sets the converted image dimension.
- `pixel_size_unit` sets the physical unit written to the registration CSV.
- `include_subfolders` controls whether images in subfolders are included.

---

# Core Methods

## 1. `image_loader()`

### Purpose

`image_loader()` is the first core method in the image-processing workflow. It identifies the requested source files, loads them with HyperSpy, and returns each source path together with its loaded HyperSpy signal. You should use this method to load images for other scripts.

It can load images from:

1. `self.selected_files`;
2. `self.input_data`;
3. the full `self.input_path` directory.

The method does not convert, resize, save, or register images. Those operations are performed by `convert_to_image()`.

### Signature

```python
loaded_images = image.image_loader()
```

### Return Value

```python
List[Tuple[Path, HyperSpySignal]]
```

Each item contains:

```python
(source_image_path, loaded_hyperspy_signal)
```

### Example: Load All Images from a Directory

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=r'C:\data\raw_images',
    output_path=r'C:\data\converted_images',
    include_subfolders=True
)

loaded_images = image.image_loader()

for image_path, image_signal in loaded_images:
    print(image_path)
    print(image_signal.data.shape)
```

### Example: Select the Input and Output Directories Interactively

When `input_path` and `output_path` are not provided, keep the default directory-selection settings. Calling `image_loader()` opens a dialog for selecting the input directory and then a dialog for selecting the output directory.

```python
image = ImageConverter()

loaded_images = image.image_loader()

for image_path, image_signal in loaded_images:
    print(image_path)
    print(image_signal.data.shape)
```

In this example:

1. Select the folder containing the source images when the input-directory dialog opens.
2. Select the folder for the converted images and `image_registration.csv` when the output-directory dialog opens.
3. If supported images are found in subfolders, the program may ask whether those images should also be loaded.

### Example: Load One Image

When calling `image_loader()` directly, assign the input request to the object first.

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=r'C:\data\raw_images',
    output_path=r'C:\data\converted_images'
)

image.input_data = 'Au cube A41-6k-5.dm4'
loaded_images = image.image_loader()

image_path, image_signal = loaded_images[0]
print(image_path)
print(image_signal.data.shape)
```

### When to Use It Directly

Use `image_loader()` directly when you need to inspect HyperSpy signals or verify the source images before conversion. For normal conversion, call `convert_to_image()`, which calls `image_loader()` internally.

---

## 2. `convert_to_image()`

### Purpose

`convert_to_image()` is the main conversion method. It calls `image_loader()` and then:

1. reads the image data;
2. converts RGB data to grayscale when needed;
3. reads the original pixel size and unit from the HyperSpy metadata;
4. adjusts brightness and contrast with the standalone `auto_brightness_contrast()` function;
5. resizes the image or creates original-resolution patches;
6. saves the converted image with its output file extension;
7. updates `image_registration.csv`.

### Signature

```python
image.convert_to_image(
    input_data=None,
    selected_files=None,
    keep_original_resolution=False,
    output_path=None,
    load_existing_registration=True,
    include_subfolders=None,
    auto_brightness_contrast=True,
    auto_contrast_lower_percentile=0.5,
    auto_contrast_upper_percentile=99.5
)
```

### Input Priority

The method chooses the input source in this order:

1. `selected_files`;
2. `input_data`;
3. all supported images in `input_path`.

### Main Parameters

- `input_data`: a file name, file path, or HyperSpy-supported wildcard pattern.
- `selected_files`: one selected file, a list or tuple of files, or a wildcard pattern relative to `input_path`.
- `keep_original_resolution=False`: resize the image to `output_size`.
- `keep_original_resolution=True`: split a qualifying square image into patches while retaining the original pixel size.
- `output_path`: override the output directory for the current conversion.
- `load_existing_registration=True`: load the existing registration CSV before adding or updating records.
- `include_subfolders`: include or exclude images from subfolders during directory conversion.
- `auto_brightness_contrast=True`: apply percentile-based automatic contrast adjustment.
- `auto_contrast_lower_percentile`: lower intensity percentile mapped to black.
- `auto_contrast_upper_percentile`: upper intensity percentile mapped to white.

### Return Value

The method returns `None`. Converted images and `image_registration.csv` are written to the output directory.

### Example Use

```python
image = ImageConverter()
input_data = '*.jpg'
image.convert_to_image(input_data)
```

### Example: Convert All Images in a Directory

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=r'C:\data\raw_images',
    output_path=r'C:\data\converted_images',
    output_format='png',
    output_size=(512, 512),
    pixel_size_unit='nm'
)

image.convert_to_image(
    include_subfolders=True,
    keep_original_resolution=False
)
```

### Example: Convert One DM4 Image

```python
image.convert_to_image(
    input_data='Au cube A41-6k-5.dm4',
    keep_original_resolution=False
)
```

### Example: Convert Selected Images

```python
image.convert_to_image(
    selected_files=[
        'Au cube A41-6k-5.dm4',
        'Au cube A19-5k-1.dm4'
    ],
    keep_original_resolution=False
)
```

### Example: Create Original-Resolution Patches

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=r'C:\data\raw_images',
    output_path=r'C:\data\converted_images',
    output_size=(512, 512)
)

image.convert_to_image(
    selected_files=['image1.dm4', 'image2.dm4'],
    keep_original_resolution=True
)
```

For example, a `2048 × 2048` square image with `output_size=(512, 512)` produces 16 patches. The patch pixel size remains equal to the original pixel size.

### Example: Change the Automatic Contrast Range

```python
image.convert_to_image(
    input_data='image.dm4',
    auto_brightness_contrast=True,
    auto_contrast_lower_percentile=1.0,
    auto_contrast_upper_percentile=99.0
)
```

### Convert Selected Images into a Subfolder

Create the destination subfolder and pass it through `output_path`.

```python
from pathlib import Path


selected_output_path = Path(image.output_path) / 'training' / 'Au_cubes'

image.convert_to_image(
    selected_files='Au cube*.dm4',
    keep_original_resolution=True,
    output_path=selected_output_path
)
```

This pattern can be adapted by changing `selected_files`, `output_path`, `output_size`, contrast settings, or `keep_original_resolution`.


---

## 3. `load_image_registration_csv()`

### Purpose

`load_image_registration_csv()` reads an existing registration CSV and stores the records in:

```python
image.image_registration
```

Each record contains:

```text
original_image_name
original_dim
original_size
converted_image_name
converted_dim
converted_size
```

File extensions and pixel-size units are preserved.

### Signature

```python
image.load_image_registration_csv(csv_path=None)
```

### Parameters

- `csv_path`: path to an existing registration CSV. When it is `None`, the current or default registration path is used.

### Return Value

The method returns `None`. Loaded records are stored in `image.image_registration`.

### Example: Load and Inspect Registration Records

```python
image.load_image_registration_csv(
    r'C:\data\converted_images\image_registration.csv'
)

for record in image.image_registration:
    print(record['original_image_name'])
    print(record['original_dim'])
    print(record['original_size'])
    print(record['converted_image_name'])
    print(record['converted_dim'])
    print(record['converted_size'])
```

A record has the following structure:

```python
{
    'original_image_name': 'Au cube A41-6k-5.dm4',
    'original_dim': (2048, 2048),
    'original_size': '0.26541nm',
    'converted_image_name': '0b152bdcf0.png',
    'converted_dim': (512, 512),
    'converted_size': '1.06164nm'
}
```

---

## 4. `export_image_registration_csv()`

### Purpose

`export_image_registration_csv()` writes the registration records currently stored in memory to a CSV file.

### Signature

```python
csv_path = image.export_image_registration_csv(csv_path=None)
```

### Parameters

- `csv_path`: optional destination path. When it is `None`, the current or default registration path is used.

### Return Value

The method returns a `Path` object for the exported CSV file.

### Example: Export to the Default Location

```python
csv_path = image.export_image_registration_csv()
print(csv_path)
```

### Example: Export to a Designated Location

```python
csv_path = image.export_image_registration_csv(
    r'C:\data\registrations\image_registration.csv'
)

print(f'Registration saved to: {csv_path}')
```

---

# Standalone Utility Functions

The following functions are separated from `ImageConverter`. Import them directly when image conversion, directory selection, registration, and file export are not needed.

## `auto_brightness_contrast()`

### Purpose

`auto_brightness_contrast()` maps image intensities to the 8-bit range from 0 to 255. Percentile-based limits reduce the effect of a small number of unusually dark or bright pixels.

Because it is a standalone function, it can be applied to any compatible NumPy image array without creating an `ImageConverter` object.

### Signature

```python
adjusted_image = auto_brightness_contrast(
    image_data,
    lower_percentile=0.5,
    upper_percentile=99.5
)
```

### Parameters

- `image_data`: NumPy image array.
- `lower_percentile`: percentile mapped to black (`0`).
- `upper_percentile`: percentile mapped to white (`255`).

### Return Value

The function returns a NumPy array with:

```text
dtype: uint8
range: 0–255
```

### Example: Adjust and Save a HyperSpy Image

```python
from PIL import Image

import hyperspy.api as hs
import numpy as np

from image_converter_with_standalone_utilities import auto_brightness_contrast


signal = hs.load('image.dm4')
image_data = np.array(signal.data)

adjusted_image = auto_brightness_contrast(
    image_data,
    lower_percentile=0.5,
    upper_percentile=99.5
)

Image.fromarray(adjusted_image).save('adjusted_image.png')
```

### Example: Use It in Another Image-Processing Function

```python
def prepare_model_input(image_data):
    return auto_brightness_contrast(
        image_data,
        lower_percentile=1.0,
        upper_percentile=99.0
    )
```

---

## `autoscale()`

### Purpose

`autoscale()` converts pixel-size values between supported physical units.

Because it is a standalone function, it can be used in measurement, image-analysis, or registration scripts without creating an `ImageConverter` object.

Supported units:

```text
angstrom
nm
um
m
```

### Signature

```python
converted_scale = autoscale(
    scale,
    from_unit='nm',
    to_unit='nm'
)
```

### Parameters

- `scale`: scalar, list, tuple, NumPy array, or `None`.
- `from_unit`: original unit.
- `to_unit`: target unit.

### Return Value

- A scalar input returns a float.
- A list or tuple returns a tuple.
- A NumPy array returns a NumPy array.
- `None` returns `None`.

### Autoscale Example

```python
from image_converter_with_standalone_utilities import autoscale


converted_scale = autoscale(
    (0.5, 0.5),
    from_unit='nm',
    to_unit='angstrom'
)

print(converted_scale)
```

Result:

```python
(5.0, 5.0)
```

### Example: Convert a Scalar

```python
converted_scale = autoscale(
    0.26541,
    from_unit='nm',
    to_unit='angstrom'
)

print(converted_scale)
```

Result:

```text
2.6541
```

### Example: Reuse It in a Measurement Function

```python
def pixel_size_in_angstrom(pixel_size_nm):
    return autoscale(
        pixel_size_nm,
        from_unit='nm',
        to_unit='angstrom'
    )
```

---


# Recommended Workflow

For most users, the workflow is:

```python
image = ImageConverter(
    select_input_dir=False,
    select_output_dir=False,
    input_path=r'C:\data\raw_images',
    output_path=r'C:\data\converted_images',
    output_format='png',
    output_size=(512, 512),
    pixel_size_unit='nm'
)

# Optional inspection step
loaded_images = image.image_loader()
for image_path, image_signal in loaded_images:
    print(image_path, image_signal.data.shape)

# Main conversion step
image.convert_to_image(
    include_subfolders=True,
    keep_original_resolution=False,
    auto_brightness_contrast=True
)
```

Call `image_loader()` directly when inspection is needed. Otherwise, call `convert_to_image()` directly because it automatically loads the requested images before processing them.

The standalone utility functions can be used independently:

```python
adjusted_image = auto_brightness_contrast(image_data)

pixel_size_angstrom = autoscale(
    (0.5, 0.5),
    from_unit='nm',
    to_unit='angstrom'
)
```
