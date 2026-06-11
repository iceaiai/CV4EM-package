# Project Overview

This project supports a reproducible workflow for object detection and segmentation of nanostructures in electron microscopy images.

## Data lifecycle

Raw microscopy files are stored under data/raw and should be treated as immutable. Converted images generated from raw files belong under data/converted_images. Images selected for manual annotation should be copied into data/selected_for_annotation, while AnyLabeling JSON files belong under data/annotations/anylabeling.

Masks generated from annotation JSON files are stored under data/masks/generated. Cleaned masks and cleaned images are stored as new versions under data/masks/cleaned and data/cleaned; raw, generated, and source files should not be overwritten.

External datasets are separated into data/external/original for exact downloaded data and data/external/standardized for project-compatible reformats. Final train/val/test segmentation datasets belong under data/datasets/segmentation and should be generated from manifests instead of being manually mixed with raw data.

## Metadata registries

Registry CSV files under data/metadata record relationships among raw images, converted images, selected annotation images, annotation JSON files, generated masks, cleaned data, external data, and final datasets. These files make the workflow reproducible and help repair paths or trace lineage after migrations.

## Folder roles

- src/object_detection_segmentation: reusable Python package code.
- scripts: executable workflow entry points for batch processing.
- 
otebooks: interactive development and analysis notebooks.
- 	ests: unit tests, small test images, and test outputs.
- outputs: generated figures, reports, and model outputs.
- rchive: legacy code, old outputs, old selected images, and migration logs.
