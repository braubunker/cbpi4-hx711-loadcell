import importlib.util
import threading
import time
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

    def test_busy_port_is_explained(self):
        message = _module._port_error(OSError("device reports readiness to read but returned no data (device disconnected or multiple access on port?)"), "/dev/ttyUSB0")
        self.assertIn("USB-Verbindung", message)

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

    def test_stable_window_ignores_one_spike(self):
        scale = SerialScale(port="/dev/ttyUSB0")
        result = {}

        def worker():
            try:
                result["value"] = scale.read_stable(count=8, spread_limit=2500, timeout=2)
            except Exception as error:
                result["error"] = error

        thread = threading.Thread(target=worker)
        thread.start()
        time.sleep(0.05)
        for value in (509, 510, 508, 872000, 509, 511, 507, 509, 510):
            scale.ingest("R{}".format(value))
            time.sleep(0.02)
        thread.join(3)
        self.assertNotIn("error", result)
        self.assertLess(abs(result["value"][0] - 509), 3)
        self.assertLess(result["value"][1], 20)

    def test_jumping_window_is_rejected(self):
        scale = SerialScale(port="/dev/ttyUSB0")
        result = {}

        def worker():
            try:
                result["value"] = scale.read_stable(count=8, spread_limit=2500, timeout=1)
            except Exception as error:
                result["error"] = error

        thread = threading.Thread(target=worker)
        thread.start()
        time.sleep(0.05)
        for value in (509, 872000, 292000, 509, 872000, 292000, 509, 872000, 292000, 509):
            scale.ingest("R{}".format(value))
            time.sleep(0.02)
        thread.join(2)
        self.assertIsInstance(result.get("error"), RuntimeError)
        self.assertIn("springen", str(result["error"]))


if __name__ == "__main__":
    unittest.main()
