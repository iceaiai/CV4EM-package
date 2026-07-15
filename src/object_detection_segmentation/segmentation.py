"""
Author: Mengkun Tian
----------------------
Utilities for comparing Otsu-based and SAM3-based particle segmentation.

A reference instance mask can be loaded from PNG, TIFF, or NPY, or generated
from an AnyLabeling JSON annotation with the external MakeMasks class.

All instance masks use:
    0 = background
    1, 2, 3, ... = individual objects
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from PIL import Image
from scipy import ndimage as ndi
from skimage import feature, filters, measure, morphology, segmentation
from skimage.segmentation import relabel_sequential


SUPPORTED_MASK_FORMATS = {".png", ".tif", ".tiff", ".npy"}


# =============================================================================
# CORE SEGMENTATION METHODS
# =============================================================================

def segment_with_otsu(
    image: Any,
    particle_color: str = "black",
    min_size: int = 50,
    fill_holes: bool = False,
    use_watershed: bool = False,
    min_distance: int = 8,
) -> dict[str, Any]:
    """
    Segment a processed 2D grayscale EM image using Otsu thresholding.

    particle_color:
        "white" = bright particles on a dark background.
        "black" = dark particles on a bright background.
    """
    gray = np.asarray(image)
    if gray.ndim != 2:
        raise ValueError("Otsu segmentation expects a 2D grayscale image.")
    if min_size < 0:
        raise ValueError("min_size must be nonnegative.")
    if min_distance < 1:
        raise ValueError("min_distance must be at least 1.")

    particle_color = particle_color.lower()
    threshold = filters.threshold_otsu(gray)

    if particle_color == "black":
        binary = gray < threshold
        foreground_type = "black particles on white background"
    elif particle_color == "white":
        binary = gray > threshold
        foreground_type = "white particles on black background"
    else:
        raise ValueError("particle_color must be 'black' or 'white'.")

    binary = _clean_binary_mask(binary, min_size, fill_holes, min_size)

    if use_watershed:
        instance_mask = _watershed_instances(binary, min_distance)
        method = "Otsu + Watershed"
    else:
        instance_mask = measure.label(binary)
        method = "Otsu + Connected Components"

    instance_mask = _clean_instance_mask(instance_mask, min_size)

    return {
        "method": method,
        "binary_mask": binary,
        "instance_mask": instance_mask,
        "parameters": {
            "particle_color": particle_color,
            "foreground_type": foreground_type,
            "threshold_value": float(threshold),
            "min_size": min_size,
            "fill_holes": fill_holes,
            "use_watershed": use_watershed,
            "min_distance": min_distance,
        },
    }


def sam3_output_to_result(
    output: Mapping[str, Any],
    mask_threshold: float = 0.5,
    min_size: int = 0,
    fill_holes: bool = False,
    hole_area_threshold: int = 50,
) -> dict[str, Any]:
    """
    Convert SAM3 output to the same instance-mask format used by Otsu.

    Higher-confidence masks keep overlapping pixels.
    """
    if not 0 <= mask_threshold <= 1:
        raise ValueError("mask_threshold must be between 0 and 1.")
    if min_size < 0 or hole_area_threshold < 0:
        raise ValueError("Size thresholds must be nonnegative.")

    masks, scores = _normalize_sam3_predictions(output)
    instance_mask = np.zeros(masks.shape[-2:], dtype=np.int32)
    kept_indices: list[int] = []

    for prediction_index in np.argsort(scores)[::-1]:
        mask = masks[prediction_index]
        object_mask = mask if mask.dtype == bool else mask > mask_threshold
        object_mask = _clean_binary_mask(
            object_mask,
            min_size,
            fill_holes,
            hole_area_threshold,
        )
        object_mask &= instance_mask == 0

        if not object_mask.any():
            continue

        instance_mask[object_mask] = len(kept_indices) + 1
        kept_indices.append(int(prediction_index))

    instance_mask = _relabel_mask(instance_mask)

    return {
        "method": "SAM3",
        "binary_mask": instance_mask > 0,
        "instance_mask": instance_mask,
        "kept_indices": kept_indices,
        "sam3_output": output,
        "parameters": {
            "mask_threshold": mask_threshold,
            "min_size": min_size,
            "fill_holes": fill_holes,
            "hole_area_threshold": hole_area_threshold,
            "input_predictions": int(len(masks)),
            "kept_predictions": int(instance_mask.max()),
        },
    }


def calculate_binary_metrics(
    pred_mask: np.ndarray,
    reference_mask: np.ndarray,
) -> dict[str, float | int]:
    """Compare total predicted and reference foreground regions."""
    pred = _validate_instance_mask(pred_mask, "Prediction mask") > 0
    reference = _validate_instance_mask(reference_mask, "Reference mask") > 0

    if pred.shape != reference.shape:
        raise ValueError(
            f"Mask shapes do not match: prediction {pred.shape}, "
            f"reference {reference.shape}."
        )

    intersection = int(np.logical_and(pred, reference).sum())
    union = int(np.logical_or(pred, reference).sum())
    pred_area = int(pred.sum())
    reference_area = int(reference.sum())

    return {
        "IoU": intersection / union if union else 0.0,
        "Dice": (
            2 * intersection / (pred_area + reference_area)
            if pred_area + reference_area else 0.0
        ),
        "Precision": intersection / pred_area if pred_area else 0.0,
        "Recall": intersection / reference_area if reference_area else 0.0,
        "Predicted area": pred_area,
        "Reference area": reference_area,
    }


# =============================================================================
# DISPLAY METHODS
# =============================================================================

def instance_mask_to_rgb(
    mask: np.ndarray,
    cmap_name: str = "tab20",
    show_boundaries: bool = True,
    boundary_color: tuple[float, float, float] = (0, 0, 0),
) -> np.ndarray:
    """Convert an instance mask to a white-background RGB image."""
    mask = _validate_instance_mask(mask)
    max_label = int(mask.max())
    colors = np.ones((max_label + 1, 3), dtype=float)

    if max_label:
        cmap = plt.get_cmap(cmap_name, max_label)
        colors[1:] = [cmap(index)[:3] for index in range(max_label)]

    rgb = colors[mask]

    if show_boundaries:
        boundaries = segmentation.find_boundaries(mask, mode="inner")
        rgb[boundaries] = boundary_color

    return rgb


def show_instance_mask(
    mask: np.ndarray,
    ax: plt.Axes,
    title: str,
    cmap_name: str = "tab20",
    show_boundaries: bool = True,
) -> None:
    """Display an instance mask."""
    ax.imshow(instance_mask_to_rgb(mask, cmap_name, show_boundaries))
    ax.set_title(title)
    ax.axis("off")


def show_otsu_result(
    image: Any,
    reference_mask: np.ndarray,
    result: Mapping[str, Any],
    title: str,
    cmap_name: str = "tab20",
    show_boundaries: bool = True,
) -> dict[str, float | int]:
    """Display raw image, reference mask, binary mask, and Otsu result."""
    metrics = calculate_binary_metrics(result["instance_mask"], reference_mask)
    _, axes = plt.subplots(1, 4, figsize=(18, 5))

    _show_raw_image(axes[0], image, "Original Image")
    show_instance_mask(
        reference_mask, axes[1], "Reference Mask",
        cmap_name, show_boundaries,
    )
    axes[2].imshow(result["binary_mask"], cmap="gray")
    axes[2].set_title("Otsu Binary Mask")
    axes[2].axis("off")
    show_instance_mask(
        result["instance_mask"], axes[3],
        f'{result["method"]} Instance Mask',
        cmap_name, show_boundaries,
    )

    _finish_figure(title)
    print_segmentation_summary(title, result, reference_mask, metrics)
    return metrics


def show_sam3_result(
    image: Any,
    reference_mask: np.ndarray,
    output: Mapping[str, Any],
    title: str,
    cmap_name: str = "tab20",
) -> dict[str, Any]:
    """
    Display raw image, reference mask, SAM3 predictions, and instance mask.

    output may be raw SAM3 output or a processed sam3_output_to_result result.
    """
    result, raw_output = _resolve_sam3_result(output)
    metrics = calculate_binary_metrics(result["instance_mask"], reference_mask)
    _, axes = plt.subplots(1, 4, figsize=(20, 5))

    _show_raw_image(axes[0], image, "Original Image")
    show_instance_mask(reference_mask, axes[1], "Reference Mask", cmap_name)
    _show_sam3_predictions(
        axes[2],
        image,
        raw_output,
        result["kept_indices"],
        cmap_name,
        result.get("parameters", {}).get("mask_threshold", 0.5),
    )
    show_instance_mask(
        result["instance_mask"], axes[3], "SAM3 Instance Mask", cmap_name
    )

    _finish_figure(title)
    print_segmentation_summary(title, result, reference_mask, metrics)
    result["metrics"] = metrics
    return result


def print_segmentation_summary(
    title: str,
    result: Mapping[str, Any],
    reference_mask: np.ndarray,
    metrics: Mapping[str, float | int] | None = None,
) -> None:
    """Print a method-independent segmentation summary."""
    metrics = metrics or calculate_binary_metrics(
        result["instance_mask"], reference_mask
    )

    print(title)
    print("Method:", result["method"])
    print("Reference objects:", count_instances(reference_mask))
    print("Detected objects:", count_instances(result["instance_mask"]))

    for key, value in result.get("parameters", {}).items():
        print(f"{key.replace('_', ' ').capitalize()}:", value)

    print("\nPredicted Mask vs Reference Mask:")
    for key, value in metrics.items():
        print(
            f"{key}: {value:.4f}"
            if isinstance(value, (float, np.floating))
            else f"{key}: {value}"
        )


def count_instances(mask: np.ndarray) -> int:
    """Count nonzero object IDs in an instance mask."""
    return int(np.count_nonzero(np.unique(_validate_instance_mask(mask)) > 0))


# =============================================================================
# MASK INPUT / OUTPUT
# =============================================================================

def load_instance_mask(mask_path: str | Path) -> np.ndarray:
    """Load an instance mask from PNG, TIFF, or NPY."""
    mask_path = Path(mask_path)

    if not mask_path.exists():
        raise FileNotFoundError(f"Mask file not found: {mask_path}")

    suffix = mask_path.suffix.lower()
    if suffix == ".npy":
        mask = np.load(mask_path)
    elif suffix in SUPPORTED_MASK_FORMATS:
        mask = np.asarray(Image.open(mask_path))
    else:
        raise ValueError(
            "Unsupported mask format. Use .png, .tif, .tiff, or .npy."
        )

    return _validate_instance_mask(mask)


def save_instance_mask(mask: np.ndarray, output_path: str | Path) -> Path:
    """Save an instance mask as a NumPy NPY file."""
    output_path = Path(output_path)

    if output_path.suffix.lower() != ".npy":
        output_path = output_path.with_suffix(".npy")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, _validate_instance_mask(mask))
    return output_path


# =============================================================================
# PRIVATE HELPERS
# =============================================================================

def _validate_instance_mask(
    mask: np.ndarray,
    name: str = "Instance mask",
) -> np.ndarray:
    mask = np.asarray(mask)

    if mask.ndim != 2:
        raise ValueError(f"{name} must be 2D, received {mask.shape}.")
    if not np.all(np.isfinite(mask)):
        raise ValueError(f"{name} contains nonfinite values.")
    if np.any(mask < 0) or not np.all(mask == np.floor(mask)):
        raise ValueError(f"{name} labels must be nonnegative integers.")

    return mask.astype(np.int32, copy=False)


def _remove_small_regions(
    labels: np.ndarray,
    min_size: int,
) -> np.ndarray:
    """Remove labels containing fewer than min_size pixels."""
    labels = np.asarray(labels)

    if min_size <= 0 or labels.size == 0:
        return labels.copy()

    counts = np.bincount(labels.ravel().astype(np.int64))
    small_labels = np.flatnonzero(counts < min_size)
    small_labels = small_labels[small_labels != 0]

    cleaned = labels.copy()
    if len(small_labels):
        cleaned[np.isin(cleaned, small_labels)] = 0

    return cleaned


def _clean_binary_mask(
    binary_mask: np.ndarray,
    min_size: int,
    fill_holes: bool,
    hole_area_threshold: int,
) -> np.ndarray:
    binary = np.asarray(binary_mask, dtype=bool)

    if min_size > 0:
        labels = measure.label(binary)
        binary = _remove_small_regions(labels, min_size) > 0

    if fill_holes and hole_area_threshold > 0:
        binary = morphology.remove_small_holes(
            binary,
            area_threshold=hole_area_threshold,
        )

    return np.asarray(binary, dtype=bool)


def _clean_instance_mask(
    instance_mask: np.ndarray,
    min_size: int,
) -> np.ndarray:
    cleaned = _remove_small_regions(instance_mask, min_size)
    return _relabel_mask(cleaned)


def _relabel_mask(instance_mask: np.ndarray) -> np.ndarray:
    relabeled, _, _ = relabel_sequential(instance_mask)
    return np.asarray(relabeled, dtype=np.int32)


def _watershed_instances(
    binary_mask: np.ndarray,
    min_distance: int,
) -> np.ndarray:
    distance = ndi.distance_transform_edt(binary_mask)
    coordinates = feature.peak_local_max(
        distance,
        labels=binary_mask,
        min_distance=min_distance,
        exclude_border=False,
    )

    if len(coordinates):
        marker_mask = np.zeros_like(binary_mask, dtype=bool)
        marker_mask[tuple(coordinates.T)] = True
        markers = measure.label(marker_mask)
    else:
        markers = measure.label(binary_mask)

    return segmentation.watershed(-distance, markers, mask=binary_mask)


def _normalize_sam3_predictions(
    output: Mapping[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    if "masks" not in output:
        raise KeyError("SAM3 output must contain 'masks'.")

    masks = _to_numpy(output["masks"])

    if masks.ndim == 4 and masks.shape[1] == 1:
        masks = masks[:, 0]
    elif masks.ndim == 2:
        masks = masks[None, ...]
    elif masks.ndim != 3:
        raise ValueError(f"Unsupported SAM3 mask shape: {masks.shape}")

    scores = _to_numpy(
        output.get("scores", np.ones(len(masks), dtype=float))
    ).reshape(-1)

    if len(scores) != len(masks):
        raise ValueError(
            "The number of SAM3 scores does not match the number of masks."
        )

    return masks, scores


def _resolve_sam3_result(
    output: Mapping[str, Any],
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    if "instance_mask" in output and "sam3_output" in output:
        return dict(output), output["sam3_output"]
    return sam3_output_to_result(output), output


def _to_numpy(value: Any) -> np.ndarray:
    """Convert a PyTorch tensor or array-like object to NumPy."""
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "float"):
        value = value.float()
    if hasattr(value, "cpu"):
        value = value.cpu()
    return np.asarray(value)


def _show_raw_image(ax: plt.Axes, image: Any, title: str) -> None:
    array = np.asarray(image)
    ax.imshow(array, cmap="gray" if array.ndim == 2 else None)
    ax.set_title(title)
    ax.axis("off")


def _show_sam3_predictions(
    ax: plt.Axes,
    image: Any,
    output: Mapping[str, Any],
    kept_indices: list[int],
    cmap_name: str,
    mask_threshold: float,
) -> None:
    masks, scores = _normalize_sam3_predictions(output)
    boxes = _to_numpy(output["boxes"]) if "boxes" in output else None
    image_array = np.asarray(image)

    ax.imshow(image_array, cmap="gray" if image_array.ndim == 2 else None)
    cmap = plt.get_cmap(cmap_name, max(len(kept_indices), 1))

    for object_id, prediction_index in enumerate(kept_indices, start=1):
        mask = masks[prediction_index]
        mask = mask if mask.dtype == bool else mask > mask_threshold
        color = cmap(object_id - 1)[:3]

        overlay = np.zeros((*mask.shape, 4), dtype=float)
        overlay[mask] = (*color, 0.45)
        ax.imshow(overlay)

        label_x = label_y = 0.0
        if boxes is not None and prediction_index < len(boxes):
            x1, y1, x2, y2 = boxes[prediction_index].astype(float)
            ax.add_patch(
                Rectangle(
                    (x1, y1),
                    x2 - x1,
                    y2 - y1,
                    fill=False,
                    edgecolor=color,
                    linewidth=1.5,
                )
            )
            label_x, label_y = x1, y1

        score_text = (
            f", p={float(scores[prediction_index]):.2f}"
            if prediction_index < len(scores) else ""
        )
        ax.text(
            label_x,
            label_y,
            f"id={object_id}{score_text}",
            fontsize=8,
            color="white",
            bbox={
                "facecolor": color,
                "alpha": 0.8,
                "edgecolor": "none",
                "pad": 1.5,
            },
        )

    ax.set_title("SAM3 Prediction with Labels")
    ax.axis("off")


def _finish_figure(title: str) -> None:
    plt.suptitle(title)
    plt.tight_layout()
    plt.show()
