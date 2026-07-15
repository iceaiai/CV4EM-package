"""
Convert AnyLabeling JSON annotations to instance masks or COCO annotations.

Supported area-based shape types:
    polygon
    rectangle
    circle

Unsupported non-area shape types are skipped:
    point
    line
    linestrip

Instance mask values:
    0 = background
    1 = object 1
    2 = object 2
    ...
    n = object n

A single 2D instance mask cannot preserve multiple object IDs at the same
overlapping pixel. The object drawn later overwrites the earlier object in the
overlap. COCO annotations preserve overlapping objects independently.
"""

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw


PathLike = Union[str, Path]
ImageShape = Tuple[int, int]


class MakeMasks:
    """Convert AnyLabeling JSON annotations to instance masks and COCO data."""

    SUPPORTED_SHAPE_TYPES = {"polygon", "rectangle", "circle"}
    SUPPORTED_MASK_FORMATS = {"png", "tif", "tiff", "npy"}

    def __init__(self,input_dir: Optional[PathLike] = None,output_dir: Optional[PathLike] = None,output_folder_name: str = "masks", default_image_shape: ImageShape = (512, 512),) -> None:
        self.input_dir = Path(input_dir or ".").resolve()
        self.output_dir = Path(output_dir or ".").resolve()
        self.output_folder_name = output_folder_name
        self.default_image_shape = self._normalize_image_shape(default_image_shape)
        self.mask_dir = self.output_dir / self.output_folder_name
        self.mask_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core mask methods
    # ------------------------------------------------------------------

    def load_anylabeling_json(self, json_path: PathLike) -> Dict[str, Any]:
        """Load one AnyLabeling JSON annotation file."""

        json_path = Path(json_path)

        with json_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def create_instance_mask_from_json(
        self,
        data: Dict[str, Any],
        image_shape: Optional[ImageShape] = None,
    ) -> np.ndarray:
        """
        Create one consecutive-ID instance mask from loaded AnyLabeling data.

        Object IDs are assigned from 1 to n in annotation order. Unsupported or
        invalid shapes are skipped. Later objects overwrite earlier objects in
        overlapping pixels.
        """

        height, width = self._resolve_image_shape(image_shape)

        mask_image = Image.new("I", (width, height), 0)
        draw = ImageDraw.Draw(mask_image)

        object_id = 1

        for shape_type, points in self._iter_valid_shapes(data):
            self._draw_instance_shape(
                draw=draw,
                shape_type=shape_type,
                points=points,
                object_id=object_id,
            )
            object_id += 1

        return np.asarray(mask_image, dtype=np.int32)

    def save_mask(
        self,
        mask: np.ndarray,
        save_path: PathLike,
    ) -> Path:
        """
        Save an instance mask as PNG, TIFF, or NPY.

        PNG and TIFF masks are stored as uint16. Use NPY when more than 65535
        instance IDs must be preserved.
        """

        save_path = Path(save_path)
        output_format = save_path.suffix.lower().lstrip(".")

        if output_format not in self.SUPPORTED_MASK_FORMATS:
            raise ValueError(
                "Unsupported output format. "
                "Use .png, .tif, .tiff, or .npy."
            )

        save_path.parent.mkdir(parents=True, exist_ok=True)

        if output_format == "npy":
            np.save(save_path, mask)
        else:
            Image.fromarray(mask.astype(np.uint16)).save(save_path)

        return save_path

    def save_all_masks(
        self,
        image_shape: Optional[ImageShape] = None,
        output_format: str = "png",
        save_npy: bool = True,
        overwrite: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """Convert every JSON file in ``input_dir`` to an instance mask."""

        output_format = output_format.lower().lstrip(".")

        if output_format not in self.SUPPORTED_MASK_FORMATS:
            raise ValueError(
                "Unsupported output format. "
                "Use png, tif, tiff, or npy."
            )

        saved_files: Dict[str, Dict[str, Any]] = {}

        for json_path in self._get_json_paths():
            data = self.load_anylabeling_json(json_path)
            mask = self.create_instance_mask_from_json(
                data=data,
                image_shape=image_shape,
            )

            mask_path = (
                self.mask_dir
                / f"{json_path.stem}_mask.{output_format}"
            )

            if overwrite or not mask_path.exists():
                self.save_mask(mask, mask_path)

            record: Dict[str, Any] = {
                "mask_path": mask_path,
                "num_objects": int(mask.max()),
                "mask_shape": mask.shape,
            }

            if save_npy and output_format != "npy":
                npy_path = self.mask_dir / f"{json_path.stem}_mask.npy"

                if overwrite or not npy_path.exists():
                    self.save_mask(mask, npy_path)

                record["npy_path"] = npy_path

            saved_files[json_path.name] = record

        return saved_files

    def show_instance_mask(
        self,
        mask: np.ndarray,
        title: str = "Instance Mask",
    ) -> None:
        """Display an instance mask using a categorical color map."""

        plt.figure(figsize=(6, 6))
        plt.imshow(
            mask,
            cmap="nipy_spectral",
            interpolation="nearest",
        )
        plt.title(title)
        plt.axis("off")
        plt.colorbar(label="Object ID")
        plt.show()

    # ------------------------------------------------------------------
    # Core COCO methods
    # ------------------------------------------------------------------

    def convert_one_json_to_coco(
        self,
        json_path: PathLike,
        image_file_name: Optional[str] = None,
        image_shape: Optional[ImageShape] = None,
        category_name: str = "nanostructure",
        category_id: int = 1,
        circle_points: int = 36,
        save_path: Optional[PathLike] = None,
    ) -> Dict[str, Any]:
        """Convert one AnyLabeling JSON file to one COCO JSON dataset."""

        json_path = Path(json_path)
        data = self.load_anylabeling_json(json_path)

        if image_file_name is None:
            image_file_name = data.get(
                "imagePath",
                f"{json_path.stem}.png",
            )

        coco_data = self._create_coco_dataset(
            items=[(data, str(image_file_name))],
            image_shape=image_shape,
            category_name=category_name,
            category_id=category_id,
            circle_points=circle_points,
        )

        if save_path is None:
            save_path = (
                self.output_dir
                / "coco_annotations"
                / f"{json_path.stem}_coco.json"
            )

        self._save_json(coco_data, save_path)

        return coco_data

    def save_all_as_coco(
        self,
        image_shape: Optional[ImageShape] = None,
        category_name: str = "nanostructure",
        category_id: int = 1,
        image_extension: str = ".png",
        circle_points: int = 36,
        save_path: Optional[PathLike] = None,
    ) -> Dict[str, Any]:
        """Convert every JSON file in ``input_dir`` into one COCO dataset."""

        if not image_extension.startswith("."):
            image_extension = f".{image_extension}"

        items: List[Tuple[Dict[str, Any], str]] = []

        for json_path in self._get_json_paths():
            data = self.load_anylabeling_json(json_path)
            image_file_name = data.get(
                "imagePath",
                f"{json_path.stem}{image_extension}",
            )
            items.append((data, str(image_file_name)))

        coco_dataset = self._create_coco_dataset(
            items=items,
            image_shape=image_shape,
            category_name=category_name,
            category_id=category_id,
            circle_points=circle_points,
        )

        if save_path is None:
            save_path = self.output_dir / "coco_annotations.json"

        self._save_json(coco_dataset, save_path)

        return coco_dataset

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_json_paths(self) -> List[Path]:
        json_paths = sorted(self.input_dir.glob("*.json"))

        if not json_paths:
            raise FileNotFoundError(
                f"No JSON files found in {self.input_dir}"
            )

        return json_paths

    def _resolve_image_shape(
        self,
        image_shape: Optional[ImageShape],
    ) -> ImageShape:
        if image_shape is None:
            return self.default_image_shape

        return self._normalize_image_shape(image_shape)

    @staticmethod
    def _normalize_image_shape(
        image_shape: ImageShape,
    ) -> ImageShape:
        if len(image_shape) != 2:
            raise ValueError(
                "image_shape must contain (height, width)."
            )

        height, width = map(int, image_shape)

        if height <= 0 or width <= 0:
            raise ValueError(
                "Image height and width must be positive."
            )

        return height, width

    def _iter_valid_shapes(
        self,
        data: Dict[str, Any],
    ) -> Iterator[Tuple[str, np.ndarray]]:
        for shape in data.get("shapes", []):
            validated_shape = self._validate_shape(shape)

            if validated_shape is not None:
                yield validated_shape

    def _validate_shape(
        self,
        shape: Dict[str, Any],
    ) -> Optional[Tuple[str, np.ndarray]]:
        shape_type = shape.get("shape_type", "polygon")
        points = shape.get("points", [])

        if shape_type not in self.SUPPORTED_SHAPE_TYPES:
            print(
                f"Skipping unsupported shape_type: {shape_type}"
            )
            return None

        minimum_points = 3 if shape_type == "polygon" else 2

        if len(points) < minimum_points:
            print(
                f"Skipping invalid {shape_type} with fewer than "
                f"{minimum_points} points."
            )
            return None

        try:
            points_array = np.asarray(
                points,
                dtype=np.float32,
            )
        except (TypeError, ValueError):
            print(
                f"Skipping invalid {shape_type} with nonnumeric points."
            )
            return None

        if (
            points_array.ndim != 2
            or points_array.shape[1] != 2
            or not np.all(np.isfinite(points_array))
        ):
            print(
                f"Skipping invalid {shape_type} point coordinates."
            )
            return None

        if shape_type == "circle":
            center = points_array[0]
            edge = points_array[1]
            radius = float(np.linalg.norm(edge - center))

            if radius <= 0:
                print("Skipping invalid circle with zero radius.")
                return None

        return shape_type, points_array

    @staticmethod
    def _draw_instance_shape(
        draw: ImageDraw.ImageDraw,
        shape_type: str,
        points: np.ndarray,
        object_id: int,
    ) -> None:
        fill_value = int(object_id)

        if shape_type == "polygon":
            polygon_xy = [
                (float(x), float(y))
                for x, y in points
            ]
            draw.polygon(
                polygon_xy,
                outline=fill_value,
                fill=fill_value,
            )
            return

        if shape_type == "rectangle":
            x1, y1 = points[0]
            x2, y2 = points[1]
            box = [
                float(min(x1, x2)),
                float(min(y1, y2)),
                float(max(x1, x2)),
                float(max(y1, y2)),
            ]
            draw.rectangle(
                box,
                outline=fill_value,
                fill=fill_value,
            )
            return

        cx, cy = points[0]
        px, py = points[1]
        radius = float(np.hypot(px - cx, py - cy))
        box = [
            float(cx - radius),
            float(cy - radius),
            float(cx + radius),
            float(cy + radius),
        ]
        draw.ellipse(
            box,
            outline=fill_value,
            fill=fill_value,
        )

    def _shape_to_polygon(
        self,
        shape: Dict[str, Any],
        circle_points: int,
    ) -> Optional[np.ndarray]:
        validated_shape = self._validate_shape(shape)

        if validated_shape is None:
            return None

        shape_type, points = validated_shape

        if shape_type == "polygon":
            return points

        if shape_type == "rectangle":
            x1, y1 = points[0]
            x2, y2 = points[1]
            x_min, x_max = sorted((float(x1), float(x2)))
            y_min, y_max = sorted((float(y1), float(y2)))

            return np.asarray(
                [
                    [x_min, y_min],
                    [x_max, y_min],
                    [x_max, y_max],
                    [x_min, y_max],
                ],
                dtype=np.float32,
            )

        if circle_points < 3:
            raise ValueError(
                "circle_points must be at least 3."
            )

        cx, cy = points[0]
        px, py = points[1]
        radius = float(np.hypot(px - cx, py - cy))

        angles = np.linspace(
            0.0,
            2.0 * np.pi,
            int(circle_points),
            endpoint=False,
        )

        return np.column_stack(
            (
                cx + radius * np.cos(angles),
                cy + radius * np.sin(angles),
            )
        ).astype(np.float32)

    def _create_coco_dataset(
        self,
        items: List[Tuple[Dict[str, Any], str]],
        image_shape: Optional[ImageShape],
        category_name: str,
        category_id: int,
        circle_points: int,
    ) -> Dict[str, Any]:
        height, width = self._resolve_image_shape(image_shape)

        coco_dataset: Dict[str, Any] = {
            "images": [],
            "annotations": [],
            "categories": [
                {
                    "id": int(category_id),
                    "name": str(category_name),
                    "supercategory": "object",
                }
            ],
        }

        annotation_id = 1

        for image_id, (data, image_file_name) in enumerate(
            items,
            start=1,
        ):
            coco_dataset["images"].append(
                {
                    "id": image_id,
                    "file_name": image_file_name,
                    "height": height,
                    "width": width,
                }
            )

            for shape in data.get("shapes", []):
                polygon = self._shape_to_polygon(
                    shape=shape,
                    circle_points=circle_points,
                )

                if polygon is None:
                    continue

                area, bbox = self._polygon_area_and_bbox(polygon)

                if area <= 0:
                    print(
                        "Skipping annotation with zero area: "
                        f"{shape.get('label')}"
                    )
                    continue

                segmentation = (
                    polygon
                    .flatten()
                    .astype(float)
                    .tolist()
                )

                coco_dataset["annotations"].append(
                    {
                        "id": annotation_id,
                        "image_id": image_id,
                        "category_id": int(category_id),
                        "segmentation": [segmentation],
                        "area": area,
                        "bbox": bbox,
                        "iscrowd": 0,
                    }
                )
                annotation_id += 1

        return coco_dataset

    @staticmethod
    def _polygon_area_and_bbox(
        points: np.ndarray,
    ) -> Tuple[float, List[float]]:
        x_coordinates = points[:, 0]
        y_coordinates = points[:, 1]

        area = 0.5 * abs(
            np.dot(
                x_coordinates,
                np.roll(y_coordinates, 1),
            )
            - np.dot(
                y_coordinates,
                np.roll(x_coordinates, 1),
            )
        )

        x_min = float(np.min(x_coordinates))
        y_min = float(np.min(y_coordinates))
        x_max = float(np.max(x_coordinates))
        y_max = float(np.max(y_coordinates))

        bbox = [
            x_min,
            y_min,
            x_max - x_min,
            y_max - y_min,
        ]

        return float(area), bbox

    @staticmethod
    def _save_json(
        data: Dict[str, Any],
        save_path: PathLike,
    ) -> Path:
        save_path = Path(save_path)
        save_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with save_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
            )

        return save_path
