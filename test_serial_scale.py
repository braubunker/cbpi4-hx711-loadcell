import importlib.util
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "hx711_serial_scale",
    Path(__file__).resolve().parent / "cbpi4-hx711-loadcell" / "serial_scale.py",
)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
parse_raw_line = _module.parse_raw_line
find_serial_port = _module.find_serial_port
SerialScale = _module.SerialScale


class SerialScaleTest(unittest.TestCase):
    def test_parse_arduino_lines(self):
        self.assertEqual(parse_raw_line("R-12345"), -12345)
        self.assertEqual(parse_raw_line("R 500"), 500)
        self.assertEqual(parse_raw_line("hx711-nano"), None)
        self.assertEqual(parse_raw_line(""), None)

    def test_explicit_port_is_kept(self):
        self.assertEqual(find_serial_port("/dev/ttyUSB0"), "/dev/ttyUSB0")

    def test_fresh_samples_ignore_the_previous_burst(self):
        scale = SerialScale(port="/dev/ttyUSB0")
        for value in range(10):
            scale.ingest("R{}".format(value))
        start = scale._seq
        for value in (10, 10, 10, 10, 80):
            scale.ingest("R{}".format(value))
        fresh = [item[2] for item in scale.samples if item[0] > start]
        self.assertEqual(_module.trimmed_mean(fresh[:5]), 10)


if __name__ == "__main__":
    unittest.main()
