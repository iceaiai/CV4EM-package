# Object Detection and Segmentation for Nanostructures

This project organizes microscopy image conversion, mask generation, segmentation experiments, and model-ready segmentation dataset preparation.

## Quick start

```bash
pip install -r requirement.txt
```

Core package code lives in `src/object_detection_segmentation`.

- `image_converter.py`: convert microscopy image files to normalized image outputs.
- `segmentation.py`: threshold-based segmentation helpers.
- `make_masks.py`: batch mask generation from image folders.

See `docs/project_overview.md` for the data lifecycle and folder conventions. Additional documents are in `docs/Documents`.
