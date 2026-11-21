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
rolling_median = _module.rolling_median
apply_deadband = _module.apply_deadband
to_display = _module.to_display
follow_weight = _module.follow_weight
trimmed_mean = _module.trimmed_mean


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

    def test_display_converts_grams_to_kilograms(self):
        self.assertEqual(to_display(5125, "kg"), 5.125)
        self.assertEqual(to_display(5125, "g"), 5125.0)

    def test_rolling_median_ignores_a_single_spike(self):
        self.assertEqual(rolling_median([5000, 5002, 9800, 4998, 5001]), 5001)

    def test_deadband_keeps_small_changes_hidden(self):
        self.assertEqual(apply_deadband(5000, 5030, 50), 5000)
        self.assertEqual(apply_deadband(5000, 5080, 50), 5080)
        self.assertEqual(apply_deadband(None, 5080, 50), 5080)

    def test_stepping_off_is_shown_immediately(self):
        self.assertEqual(follow_weight(85000, 0, 200, 3000), 0)
        self.assertEqual(follow_weight(0, 85000, 200, 3000), 85000)

    def test_small_noise_does_not_replace_the_weight(self):
        self.assertEqual(follow_weight(85000, 85100, 200, 3000), 85000)

    def test_trimmed_mean_drops_spikes(self):
        self.assertEqual(trimmed_mean([10, 10, 10, 10, 500]), 10)


if __name__ == "__main__":
    unittest.main()
