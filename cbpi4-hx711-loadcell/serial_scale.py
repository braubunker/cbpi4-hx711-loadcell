import glob
import threading
import time

try:
    from .convert import trimmed_mean
except ImportError:  # loaded as a plain file in the unit test
    import importlib.util
    from pathlib import Path

    _convert_spec = importlib.util.spec_from_file_location(
        "hx711_convert_for_serial",
        Path(__file__).resolve().parent / "convert.py",
    )
    _convert = importlib.util.module_from_spec(_convert_spec)
    _convert_spec.loader.exec_module(_convert)
    trimmed_mean = _convert.trimmed_mean


def parse_raw_line(line):
    """Read one Arduino line. ``R-12345`` and bare integers are raw counts."""
    text = str(line).strip()
    if not text:
        return None
    if text[0] in "Rr":
        text = text[1:].strip()
    try:
        return int(text, 10)
    except ValueError:
        return None


def find_serial_port(preferred):
    """Use the configured port, or the first Arduino that appears on USB."""
    choice = str(preferred or "auto").strip()
    if choice and choice.lower() != "auto":
        return choice
    matches = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
    if not matches:
        raise IOError("Kein Arduino an USB gefunden")
    return matches[0]


class SerialScale(object):
    """Background reader for the Arduino Nano sketch.

    The Nano prints one raw HX711 count per line. This reader keeps the
    latest samples and can wait for a fresh burst during calibration.
    """

    def __init__(self, port="auto", baud=115200, opener=None):
        self.port_setting = port
        self.port = None
        self.baud = int(baud)
        self._opener = opener
        self.samples = []
        self._seq = 0
        self.lock = threading.Lock()
        self._stop = False
        self.ser = None
        self.thread = None
        self.last_error = None

    def start(self):
        if self.thread is not None:
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def ingest(self, line, now=None):
        value = parse_raw_line(line)
        if value is None:
            return None
        stamp = time.time() if now is None else now
        with self.lock:
            self._seq += 1
            self.samples.append((self._seq, stamp, value))
            if len(self.samples) > 120:
                self.samples = self.samples[-120:]
        return value

    def status(self):
        with self.lock:
            count = len(self.samples)
        if count:
            return None
        if self.last_error:
            return self.last_error
        if self.port:
            return "Port {} ist offen, aber es kommen keine Messwerte".format(self.port)
        return "Kein Arduino an USB gefunden"

    def read_latest(self, count, max_age=3.0):
        count = max(1, int(count))
        deadline = time.time() + max_age + 2.0
        while time.time() < deadline:
            with self.lock:
                fresh = [item for item in self.samples if time.time() - item[1] <= max_age]
                if len(fresh) >= count:
                    return trimmed_mean(item[2] for item in fresh[-count:])
            time.sleep(0.05)
        raise TimeoutError(self.last_error or "Arduino sendet keine Daten")

    def read_fresh(self, count, timeout=None):
        count = max(1, int(count))
        if timeout is None:
            timeout = max(8.0, count * 0.3)
        with self.lock:
            start = self._seq
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self.lock:
                fresh = [item[2] for item in self.samples if item[0] > start]
                if len(fresh) >= count:
                    return trimmed_mean(fresh[:count])
            time.sleep(0.05)
        raise TimeoutError(self.last_error or "Arduino sendet keine neuen Daten")

    def close(self):
        self._stop = True
        self._close_port()

    def _run(self):
        while not self._stop:
            try:
                if self.ser is None:
                    self._open()
                raw_line = self.ser.readline()
                if isinstance(raw_line, bytes):
                    raw_line = raw_line.decode("ascii", errors="ignore")
                self.ingest(raw_line)
            except Exception as error:
                self.last_error = str(error)
                self._close_port()
                time.sleep(2)

    def _open(self):
        port = find_serial_port(self.port_setting)
        self.port = port
        if self._opener is not None:
            self.ser = self._opener(port, self.baud)
            return
        import serial

        port_handle = serial.Serial(port, self.baud, timeout=1)
        # Opening the port resets the Nano. Wait out the bootloader.
        port_handle.dtr = False
        time.sleep(0.05)
        port_handle.dtr = True
        time.sleep(2.0)
        port_handle.reset_input_buffer()
        self.ser = port_handle

    def _close_port(self):
        handle = self.ser
        self.ser = None
        if handle is not None:
            try:
                handle.close()
            except Exception:
                pass
