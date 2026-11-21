import importlib.util
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "hx711_convert",
    Path(__file__).resolve().parent / "cbpi4-hx711-loadcell" / "convert.py",
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
grams_from_raw = _module.grams_from_raw


class GramsFromRawTest(unittest.TestCase):
    def test_negative_scale_and_offset_stay_stable(self):
        # Empty raw -150000, each gram moves the raw value by -25.
        # Noise of 50 counts is 2 g, not 50 g.
        self.assertAlmostEqual(grams_from_raw(-150250, -150000, -25), 10.0)
        self.assertAlmostEqual(grams_from_raw(-150050, -150000, -25), 2.0)

    def test_positive_scale(self):
        self.assertAlmostEqual(grams_from_raw(500, 0, 25), 20.0)

    def test_fractional_scale_is_not_rounded_to_one(self):
        self.assertAlmostEqual(grams_from_raw(-200, 0, -0.4), 500.0)

    def test_zero_scale_is_rejected(self):
        with self.assertRaises(ValueError):
            grams_from_raw(100, 0, 0)


if __name__ == "__main__":
    unittest.main()
