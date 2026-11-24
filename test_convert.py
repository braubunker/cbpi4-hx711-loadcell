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
scale_from_kilograms = _module.scale_from_kilograms
raw_is_usable = _module.raw_is_usable
format_scale = _module.format_scale
center_stats = _module.center_stats
calibration_matches = _module.calibration_matches


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

    def test_calibration_in_kilograms_reads_back_the_same_weight(self):
        empty = 200000
        loaded = 370000
        scale = scale_from_kilograms(empty, loaded, 85)
        self.assertAlmostEqual(to_display(grams_from_raw(loaded, empty, scale), "kg"), 85)
        # Without the empty offset the same raw value is about twice the weight.
        self.assertGreater(to_display(grams_from_raw(loaded, 0, scale), "kg"), 150)

    def test_a_small_bridge_still_reads_back_85_kg(self):
        # 300 counts for 85 kg is 0.0035 counts per gram. Treating those
        # counts as grams shows 0.3 kg, which is the wrong display.
        empty = -263850
        loaded = empty + 300
        scale = scale_from_kilograms(empty, loaded, 85)
        stored = float(format_scale(scale))
        self.assertAlmostEqual(stored, 300 / 85000.0, places=8)
        self.assertAlmostEqual(to_display(grams_from_raw(loaded, empty, stored), "kg"), 85, places=2)

    def test_center_keeps_the_settled_reading(self):
        median, spread = center_stats([509, 508, 510, 509, 872000, 507, 511, 509, 508, 510])
        self.assertEqual(median, 509)
        self.assertLess(spread, 20)

    def test_a_control_reading_of_29_kg_is_not_87_kg(self):
        self.assertFalse(calibration_matches(87, 29.119))
        self.assertTrue(calibration_matches(87, 85.4))

    def test_saved_scale_from_a_spike_shows_a_small_step_as_a_fraction(self):
        # Offset 508.9 and scale 10.024 came from a raw spike. A settled
        # step of about 400 counts is then 0.04 kg, not 87 kg.
        grams = grams_from_raw(508.9 + 401, 508.9, 10.02427874)
        self.assertAlmostEqual(to_display(grams, "kg"), 0.04, places=2)
        settled = float(format_scale(scale_from_kilograms(508.9, 508.9 + 401, 87)))
        self.assertAlmostEqual(to_display(grams_from_raw(508.9 + 401, 508.9, settled), "kg"), 87, places=1)

    def test_zero_and_saturated_raw_are_rejected(self):
        self.assertFalse(raw_is_usable(0))
        self.assertFalse(raw_is_usable(8388607))
        self.assertTrue(raw_is_usable(-150000))


if __name__ == "__main__":
    unittest.main()
