import glob
import threading
import time

try:
    from .convert import STABLE_SPREAD, center_stats, raw_is_usable, trimmed_mean
except ImportError:  # loaded as a plain file in the unit test
    import importlib.util
    from pathlib import Path

    _convert_spec = importlib.util.spec_from_file_location(
        "hx711_convert_for_serial",
        Path(__file__).resolve().parent / "convert.py",
    )
    _convert = importlib.util.module_from_spec(_convert_spec)
    _convert_spec.loader.exec_module(_convert)
    STABLE_SPREAD = _convert.STABLE_SPREAD
    center_stats = _convert.center_stats
    raw_is_usable = _convert.raw_is_usable
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


def _port_error(error, port):
    text = str(error)
    lowered = text.lower()
    if "busy" in lowered or "resource busy" in lowered or "errno 16" in lowered:
        return "Port {} ist belegt. Ein offenes cat oder den seriellen Monitor schliessen.".format(port or "USB")
    if "no data" in lowered or "multiple access" in lowered:
        return "USB-Verbindung zum Nano ist abgerissen. Kabel neu einstecken und CraftBeerPi neu starten."
    return text


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
        self._glitches = 0

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

    def read_latest_stats(self, count, max_age=3.0):
        """Median and spread of the newest samples."""
        count = max(1, int(count))
        deadline = time.time() + max_age + 2.0
        while time.time() < deadline:
            with self.lock:
                fresh = [item[2] for item in self.samples if time.time() - item[1] <= max_age]
                if len(fresh) >= count:
                    return center_stats(fresh[-count:])
            time.sleep(0.05)
        raise TimeoutError(self.last_error or "Arduino sendet keine Daten")

    def read_latest(self, count, max_age=3.0):
        median, _spread = self.read_latest_stats(count, max_age)
        return median

    def read_stable(self, count=20, spread_limit=None, timeout=None):
        """Wait until a fresh window sits still, then return its median.

        The last calibration used a short burst that was hundreds of
        thousands of counts away from the settled reading. The saved
        factor then showed a real stance as a fraction of a kilogram.
        """
        count = max(5, int(count))
        if spread_limit is None:
            spread_limit = STABLE_SPREAD
        if timeout is None:
            timeout = max(12.0, count * 0.35)
        with self.lock:
            start = self._seq
        deadline = time.time() + timeout
        last_median = None
        last_spread = None
        while time.time() < deadline:
            with self.lock:
                fresh = [item[2] for item in self.samples if item[0] > start]
            if len(fresh) >= count:
                median, spread = center_stats(fresh[-count:])
                last_median, last_spread = median, spread
                if spread <= spread_limit and raw_is_usable(median):
                    return median, spread
            time.sleep(0.05)
        if last_spread is None:
            raise TimeoutError(self.last_error or "Arduino sendet keine neuen Daten")
        raise RuntimeError("Rohwerte springen, Spanne {} Zaehler".format(int(round(last_spread))))

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
                if self.ingest(raw_line) is not None:
                    self._glitches = 0
                    self.last_error = None
            except Exception as error:
                self._glitches += 1
                self.last_error = _port_error(error, self.port)
                # A single empty read is normal while the Nano settles.
                # Reopening on every glitch resets the board and repeats it.
                if self._glitches >= 5:
                    self._close_port()
                    self._glitches = 0
                    time.sleep(1)
                else:
                    time.sleep(0.1)

    def _open(self):
        port = find_serial_port(self.port_setting)
        self.port = port
        if self._opener is not None:
            self.ser = self._opener(port, self.baud)
            return
        import serial

        port_handle = serial.Serial()
        port_handle.port = port
        port_handle.baudrate = self.baud
        port_handle.timeout = 1
        port_handle.exclusive = True
        port_handle.rtscts = False
        port_handle.dsrdtr = False
        port_handle.dtr = False
        port_handle.rts = False
        port_handle.open()
        port_handle.dtr = False
        port_handle.rts = False
        time.sleep(0.2)
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
