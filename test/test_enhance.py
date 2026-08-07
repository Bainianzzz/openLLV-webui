"""Tests for ``inference.enhance`` helpers."""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np
import openLLV as llv
from PIL import Image

from inference.enhance import _to_pil, enhance


class TestToPil(unittest.TestCase):
    def test_pil_image(self) -> None:
        result = _to_pil(Image.fromarray(np.zeros((4, 5, 3), dtype=np.uint8)))
        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.mode, "RGB")

    def test_numpy_array(self) -> None:
        result = _to_pil(np.zeros((4, 5, 3), dtype=np.uint8))
        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.mode, "RGB")

    def test_unsupported_type(self) -> None:
        with self.assertRaises(TypeError):
            _to_pil("not an image")


class TestEnhance(unittest.TestCase):
    def test_enhance(self) -> None:
        """A valid image is enhanced and returned as a PIL RGB image."""
        image = Image.fromarray(np.zeros((4, 5, 3), dtype=np.uint8))
        predicted = np.full((4, 5, 3), 255, dtype=np.uint8)

        with mock.patch.object(
            llv, "predict", return_value=(predicted, None)
        ) as predict:
            result = enhance("SomeMethod", image)

        predict.assert_called_once_with("SomeMethod", image, save=False)
        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.mode, "RGB")
