"""
Unit tests for ImageConverter.

Recommended project structure:

project_root/
    ImageConverter.py
    # or ImageConverter_auto_brightness_contrast.py
    Unittest/
        test_image_converter.py
        test_images/
            your_image_1.dm3
            your_image_2.dm3
            ...

Run from project_root:
    python -m unittest discover -s Unittest -p "test_*.py" -v

Notes:
- These tests use Python's built-in unittest framework.
- GUI dialogs are mocked so the tests do not require manual clicking.
- Tests using real DM3 files are skipped automatically if HyperSpy is not installed
  or if Unittest/test_images contains no .dm3 files.
"""

from __future__ import annotations

import csv
import importlib.util
import shutil
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
from PIL import Image


TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent
TEST_IMAGES_DIR = TEST_DIR / "test_images"
TEST_OUTPUT_ROOT = TEST_DIR / "test_output_converter"


# -----------------------------------------------------------------------------
# Optional HyperSpy handling
# -----------------------------------------------------------------------------
# The real DM3 integration tests require HyperSpy. However, several pure unit
# tests use mocked hs.load() and fake signal objects. To allow those tests to run
# even in a lightweight environment, a small hyperspy.api stub is installed only
# when HyperSpy is not available.
try:
    import hyperspy.api as _real_hs  # noqa: F401
    HAS_HYPERSPY = True
except Exception:
    HAS_HYPERSPY = False
    hyperspy_stub = types.ModuleType("hyperspy")
    hyperspy_api_stub = types.ModuleType("hyperspy.api")

    def _missing_hyperspy_load(*args, **kwargs):
        raise unittest.SkipTest("HyperSpy is not installed in this environment.")

    hyperspy_api_stub.load = _missing_hyperspy_load
    hyperspy_stub.api = hyperspy_api_stub
    sys.modules.setdefault("hyperspy", hyperspy_stub)
    sys.modules.setdefault("hyperspy.api", hyperspy_api_stub)


# -----------------------------------------------------------------------------
# Import ImageConverter from the project root
# -----------------------------------------------------------------------------
def _load_image_converter_module():
    candidate_files = [
        PROJECT_ROOT / "ImageConverter.py",
        PROJECT_ROOT / "image_converter.py",
        PROJECT_ROOT / "ImageConverter_auto_brightness_contrast.py",
        PROJECT_ROOT / "ImageConverter_registration_autoscale_v2.py",
        PROJECT_ROOT / "ImageConverter_registration_autoscale.py",
    ]
    for candidate in candidate_files:
        if candidate.exists():
            spec = importlib.util.spec_from_file_location("image_converter_under_test", candidate)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            sys.modules["image_converter_under_test"] = module
            spec.loader.exec_module(module)
            return module
    names = "\n".join(str(path) for path in candidate_files)
    raise FileNotFoundError(
        "Cannot find ImageConverter source file. Put your converter file in the "
        f"project root as one of these names:\n{names}"
    )


converter_module = _load_image_converter_module()
ImageConverter = converter_module.ImageConverter


# -----------------------------------------------------------------------------
# Fake HyperSpy-like signal objects for pure unit tests
# -----------------------------------------------------------------------------
class FakeAxis:
    def __init__(self, scale, units):
        self.scale = scale
        self.units = units


class FakeAxesManager:
    def __init__(self, y_scale=1.0, x_scale=1.0, units="nm"):
        self.signal_axes = [FakeAxis(y_scale, units), FakeAxis(x_scale, units)]

    def __iter__(self):
        return iter(self.signal_axes)


class FakeGeneralMetadata:
    def __init__(self, original_filename):
        self.original_filename = original_filename


class FakeMetadata:
    def __init__(self, original_filename):
        self.General = FakeGeneralMetadata(original_filename)


class FakeSignal:
    def __init__(self, data, original_filename, y_scale=1.0, x_scale=1.0, units="nm"):
        self.data = data
        self.metadata = FakeMetadata(original_filename)
        self.axes_manager = FakeAxesManager(y_scale=y_scale, x_scale=x_scale, units=units)


# -----------------------------------------------------------------------------
# Test helpers
# -----------------------------------------------------------------------------
def find_dm3_files():
    if not TEST_IMAGES_DIR.exists():
        return []
    return sorted(path for path in TEST_IMAGES_DIR.rglob("*") if path.is_file() and path.suffix.lower() == ".dm3")


def read_csv_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


class ImageConverterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TEST_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    def make_output_dir(self, name):
        output_dir = TEST_OUTPUT_ROOT / name
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def make_converter(self, output_dir, output_size=(64, 64), output_format="png"):
        converter = ImageConverter(
            select_input_dir=True,
            select_output_dir=True,
            output_format=output_format,
            output_size=output_size,
            pixel_size_unit="nm",
        )
        converter.output_path = output_dir
        return converter

    # -------------------------------------------------------------------------
    # Pure unit tests: no real DM3 files required
    # -------------------------------------------------------------------------
    def test_autoscale_converts_pixel_size_units(self):
        converter = ImageConverter(select_input_dir=False, select_output_dir=False)

        np.testing.assert_allclose(
            converter.autoscale((1.0, 2.0), from_unit="um", to_unit="nm"),
            (1000.0, 2000.0)
        )

        np.testing.assert_allclose(
            converter.autoscale((10.0, 20.0), from_unit="nm", to_unit="angstrom"),
            (100.0, 200.0)
        )

        np.testing.assert_allclose(
            converter.autoscale((10.0, 20.0), from_unit="angstrom", to_unit="nm"),
            (1.0, 2.0)
        )

    def test_auto_brightness_contrast_returns_uint8_image(self):
        converter = ImageConverter(select_input_dir=False, select_output_dir=False)
        image_data = np.linspace(10, 20, 100, dtype=float).reshape(10, 10)
        image_data[0, 0] = -10000.0
        image_data[-1, -1] = 10000.0

        adjusted = converter.auto_brightness_contrast(
            image_data,
            lower_percentile=5,
            upper_percentile=95,
        )

        self.assertEqual(adjusted.shape, image_data.shape)
        self.assertEqual(adjusted.dtype, np.uint8)
        self.assertGreaterEqual(adjusted.min(), 0)
        self.assertLessEqual(adjusted.max(), 255)
        self.assertEqual(adjusted[0, 0], 0)
        self.assertEqual(adjusted[-1, -1], 255)

    def test_rgb_structured_arrays_are_converted_to_grayscale(self):
        converter = ImageConverter(select_input_dir=False, select_output_dir=False)
        rgb_dtype = np.dtype([("R", "u1"), ("G", "u1"), ("B", "u1")])
        rgb_data = np.zeros((2, 2), dtype=rgb_dtype)
        rgb_data[0, 0] = (100, 150, 200)

        gray = converter._convert_rgb_to_grayscale(rgb_data)
        expected = 0.299 * 100 + 0.587 * 150 + 0.114 * 200

        self.assertEqual(gray.shape, (2, 2))
        self.assertAlmostEqual(float(gray[0, 0]), expected)

    def test_stable_source_id_is_repeatable_and_path_dependent(self):
        converter = ImageConverter(select_input_dir=False, select_output_dir=False)
        source_a = TEST_IMAGES_DIR / "same_name.dm3"
        source_b = TEST_IMAGES_DIR / "subfolder" / "same_name.dm3"

        id_a_1 = converter._get_source_image_id(source_a)
        id_a_2 = converter._get_source_image_id(source_a)
        id_b = converter._get_source_image_id(source_b)

        self.assertEqual(id_a_1, id_a_2)
        self.assertNotEqual(id_a_1, id_b)
        self.assertEqual(len(id_a_1), 10)

    def test_fake_single_image_conversion_creates_output_csv_and_metadata(self):
        output_dir = self.make_output_dir("fake_single")
        converter = self.make_converter(output_dir=output_dir, output_size=(32, 32))

        fake_source = TEST_IMAGES_DIR / "fake_single.dm3"
        fake_data = np.arange(64 * 64, dtype=float).reshape(64, 64)
        fake_signal = FakeSignal(
            data=fake_data,
            original_filename=str(fake_source),
            y_scale=2.0,
            x_scale=3.0,
            units="nm",
        )

        with mock.patch.object(converter, "_set_input_dir", return_value=TEST_IMAGES_DIR), \
             mock.patch.object(converter_module.hs, "load", return_value=fake_signal), \
             mock.patch.object(converter, "_ask_four_choice", return_value="yes_to_all"):
            converter.convert_to_image(input_data="fake_single.dm3", auto_brightness_contrast=True)

        output_images = sorted(output_dir.glob("*.png"))
        self.assertEqual(len(output_images), 1)
        self.assertTrue(output_images[0].exists())

        csv_path = output_dir / "image_registration.csv"
        self.assertTrue(csv_path.exists())
        rows = read_csv_rows(csv_path)
        self.assertEqual(len(rows), 1)

        row = rows[0]
        self.assertEqual(row["source_name"], "fake_single.dm3")
        self.assertEqual(row["converted_image_height"], "32")
        self.assertEqual(row["converted_image_width"], "32")
        # 64x64 source resized to 32x32 doubles the pixel size.
        self.assertEqual(float(row["converted_pixel_size_y"]), 4.0)
        self.assertEqual(float(row["converted_pixel_size_x"]), 6.0)
        self.assertEqual(row["status"], "saved")

    def test_repeated_conversion_uses_same_filename_and_can_overwrite_yes_to_all(self):
        output_dir = self.make_output_dir("overwrite_yes_to_all")
        converter = self.make_converter(output_dir=output_dir, output_size=(32, 32))

        fake_source = TEST_IMAGES_DIR / "stable_name.dm3"
        fake_signal = FakeSignal(
            data=np.arange(64 * 64, dtype=float).reshape(64, 64),
            original_filename=str(fake_source),
            y_scale=1.0,
            x_scale=1.0,
            units="nm",
        )

        with mock.patch.object(converter, "_set_input_dir", return_value=TEST_IMAGES_DIR), \
             mock.patch.object(converter_module.hs, "load", return_value=fake_signal), \
             mock.patch.object(converter, "_ask_four_choice", return_value="yes_to_all"):
            converter.convert_to_image(input_data="stable_name.dm3")
            first_outputs = sorted(path.name for path in output_dir.glob("*.png"))
            converter.convert_to_image(input_data="stable_name.dm3")
            second_outputs = sorted(path.name for path in output_dir.glob("*.png"))

        self.assertEqual(first_outputs, second_outputs)
        self.assertEqual(len(second_outputs), 1)

        rows = read_csv_rows(output_dir / "image_registration.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "overwritten")

    def test_repeated_conversion_can_skip_existing_file_no_to_all(self):
        output_dir = self.make_output_dir("overwrite_no_to_all")
        converter = self.make_converter(output_dir=output_dir, output_size=(32, 32))

        fake_source = TEST_IMAGES_DIR / "skip_existing.dm3"
        fake_signal = FakeSignal(
            data=np.arange(64 * 64, dtype=float).reshape(64, 64),
            original_filename=str(fake_source),
            y_scale=1.0,
            x_scale=1.0,
            units="nm",
        )

        with mock.patch.object(converter, "_set_input_dir", return_value=TEST_IMAGES_DIR), \
             mock.patch.object(converter_module.hs, "load", return_value=fake_signal), \
             mock.patch.object(converter, "_ask_four_choice", return_value="yes_to_all"):
            converter.convert_to_image(input_data="skip_existing.dm3")

        with mock.patch.object(converter, "_set_input_dir", return_value=TEST_IMAGES_DIR), \
             mock.patch.object(converter_module.hs, "load", return_value=fake_signal), \
             mock.patch.object(converter, "_ask_four_choice", return_value="no_to_all"):
            converter.convert_to_image(input_data="skip_existing.dm3")

        output_images = sorted(output_dir.glob("*.png"))
        self.assertEqual(len(output_images), 1)

        rows = read_csv_rows(output_dir / "image_registration.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "skipped")

    def test_keep_original_resolution_creates_multiple_patch_records(self):
        output_dir = self.make_output_dir("keep_original_resolution")
        converter = self.make_converter(output_dir=output_dir, output_size=(64, 64))

        fake_source = TEST_IMAGES_DIR / "patch_source.dm3"
        fake_data = np.arange(128 * 128, dtype=float).reshape(128, 128)
        fake_signal = FakeSignal(
            data=fake_data,
            original_filename=str(fake_source),
            y_scale=0.5,
            x_scale=0.5,
            units="nm",
        )

        with mock.patch.object(converter, "_set_input_dir", return_value=TEST_IMAGES_DIR), \
             mock.patch.object(converter_module.hs, "load", return_value=fake_signal), \
             mock.patch.object(converter, "_ask_four_choice", return_value="yes_to_all"):
            converter.convert_to_image(input_data="patch_source.dm3", keep_original_resolution=True)

        patch_dirs = [path for path in output_dir.iterdir() if path.is_dir()]
        self.assertEqual(len(patch_dirs), 1)
        patch_images = sorted(patch_dirs[0].glob("*.png"))
        self.assertEqual(len(patch_images), 4)

        rows = read_csv_rows(output_dir / "image_registration.csv")
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertEqual(row["keep_original_resolution"], "True")
            self.assertEqual(row["converted_image_height"], "64")
            self.assertEqual(row["converted_image_width"], "64")
            self.assertEqual(float(row["converted_pixel_size_y"]), 0.5)
            self.assertEqual(float(row["converted_pixel_size_x"]), 0.5)
            self.assertEqual(row["status"], "saved")

    def test_manual_register_images_writes_csv_to_output_directory(self):
        output_dir = self.make_output_dir("manual_registration")
        converter = self.make_converter(output_dir=output_dir)

        source_path = TEST_IMAGES_DIR / "manual_source.dm3"
        converted_path = output_dir / "manual_converted.png"

        converter.manual_register_images([
            {
                "source_name": "manual_source.dm3",
                "source_pixel_size": (0.5, 0.5),
                "source_pixel_unit": "nm",
                "source_path": str(source_path),
                "source_shape": (128, 128),
                "converted_name": "manual_converted.png",
                "converted_pixel_size": (1.0, 1.0),
                "converted_pixel_unit": "nm",
                "converted_path": str(converted_path),
                "converted_shape": (64, 64),
                "status": "manual",
            }
        ])

        csv_path = output_dir / "image_registration.csv"
        self.assertTrue(csv_path.exists())
        rows = read_csv_rows(csv_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_name"], "manual_source.dm3")
        self.assertEqual(rows[0]["converted_name"], "manual_converted.png")
        self.assertEqual(rows[0]["status"], "manual")

    # -------------------------------------------------------------------------
    # Integration tests with real DM3 files in Unittest/test_images
    # -------------------------------------------------------------------------
    def test_collects_real_dm3_files_from_test_images_folder(self):
        dm3_files = find_dm3_files()
        if not dm3_files:
            self.skipTest("No .dm3 files found in Unittest/test_images.")

        output_dir = self.make_output_dir("collect_real_dm3")
        converter = self.make_converter(output_dir=output_dir)
        converter.input_path = TEST_IMAGES_DIR
        converter.output_path = output_dir

        collected_paths = converter._collect_image_file_paths_from_directory()
        collected_dm3_paths = [path for path in collected_paths if path.suffix.lower() == ".dm3"]

        self.assertGreaterEqual(len(collected_dm3_paths), 1)
        self.assertEqual(set(dm3_files), set(collected_dm3_paths))

    def test_convert_first_real_dm3_creates_output_image_and_csv(self):
        if not HAS_HYPERSPY:
            self.skipTest("HyperSpy is not installed; real DM3 conversion test skipped.")
        dm3_files = find_dm3_files()
        if not dm3_files:
            self.skipTest("No .dm3 files found in Unittest/test_images.")

        first_dm3 = dm3_files[0]
        relative_input = first_dm3.relative_to(TEST_IMAGES_DIR)
        output_dir = self.make_output_dir("real_dm3_single")
        converter = self.make_converter(output_dir=output_dir, output_size=(64, 64))

        with mock.patch.object(converter, "_set_input_dir", return_value=TEST_IMAGES_DIR), \
             mock.patch.object(converter, "_ask_four_choice", return_value="yes_to_all"):
            converter.convert_to_image(input_data=str(relative_input), auto_brightness_contrast=True)

        output_images = sorted(output_dir.glob("*.png"))
        self.assertGreaterEqual(len(output_images), 1)
        with Image.open(output_images[0]) as image:
            self.assertEqual(image.size, (64, 64))

        csv_path = output_dir / "image_registration.csv"
        self.assertTrue(csv_path.exists())
        rows = read_csv_rows(csv_path)
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[0]["converted_image_height"], "64")
        self.assertEqual(rows[0]["converted_image_width"], "64")
        self.assertTrue(Path(rows[0]["converted_path"]).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
