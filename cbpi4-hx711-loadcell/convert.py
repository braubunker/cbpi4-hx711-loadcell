def grams_from_raw(raw, offset, scale):
    """Convert one raw HX711 reading to grams.

    Scale is raw counts per gram and may be negative when the bridge
    polarity is reversed. Offset is the raw reading at zero and may be
    negative. A scale of 0 cannot be used.
    """
    scale = float(scale)
    if scale == 0.0:
        raise ValueError("HX711 scale is 0")
    return (float(raw) - float(offset)) / scale


def rolling_median(values):
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("no readings to smooth")
    return ordered[len(ordered) // 2]


def trimmed_mean(values, trim=0.2):
    """Average the middle readings and drop the spikes at both ends."""
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("no readings")
    cut = int(len(ordered) * float(trim))
    if cut * 2 >= len(ordered):
        cut = 0
    core = ordered[cut:len(ordered) - cut] if cut else ordered
    return sum(core) / float(len(core))


def apply_deadband(previous, candidate, deadband):
    """Keep the previous grams until the change is large enough to show."""
    candidate = float(candidate)
    if previous is None:
        return candidate
    if abs(candidate - float(previous)) < float(deadband):
        return float(previous)
    return candidate


def follow_weight(previous, candidate, deadband, snap):
    """Track a real step at once and ease only the small movements.

    A rolling median made the display sit between the old and the new
    weight for several readings. Stepping off an 85 kg load therefore
    stayed near 75 kg. Changes of ``snap`` grams or more replace the
    shown value immediately.
    """
    candidate = float(candidate)
    if previous is None:
        return candidate
    previous = float(previous)
    delta = abs(candidate - previous)
    if delta >= float(snap):
        return candidate
    if delta < float(deadband):
        return previous
    return previous + 0.25 * (candidate - previous)


def scale_from_kilograms(empty_raw, loaded_raw, kilograms):
    """Raw counts per gram from an empty reading and a known kilogram load.

    A platform that barely moves can be well under one count per gram.
    That factor is still valid and must not be rounded away.
    """
    kilograms = float(kilograms)
    if kilograms <= 0:
        raise ValueError("weight must be positive")
    return (float(loaded_raw) - float(empty_raw)) / (kilograms * 1000.0)


def format_scale(scale):
    """Keep a small counts-per-gram factor readable and exact enough.

    Rounding to four decimals turns 0.003529 into 0.0035. Eight decimals
    still read the calibration weight back as the same kilograms.
    """
    text = "{:.8f}".format(float(scale)).rstrip("0").rstrip(".")
    if text in ("", "-", "-0"):
        return "0"
    return text


# A resting HX711 stays within a few hundred counts. A window that also
# contains a stray reading hundreds of thousands away is not a weight.
STABLE_SPREAD = 2500.0


def center_stats(values):
    """Return the median and the spread of the central readings.

    One spike at the end of the window does not move the median and does
    not widen the reported spread.
    """
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("no readings")
    median = ordered[len(ordered) // 2]
    if len(ordered) < 5:
        core = ordered
    else:
        cut = len(ordered) // 5
        core = ordered[cut:len(ordered) - cut]
    return median, core[-1] - core[0]


def calibration_matches(expected_kg, actual_kg, tolerance=0.15):
    """True when a second reading still shows the weight that was applied."""
    expected_kg = float(expected_kg)
    actual_kg = float(actual_kg)
    if expected_kg <= 0:
        return False
    return abs(actual_kg - expected_kg) <= tolerance * expected_kg


def raw_is_usable(raw):
    """Reject a stuck zero and a saturated 24-bit HX711 word."""
    raw = float(raw)
    return raw != 0.0 and abs(raw) < 8000000.0


def to_display(grams, unit):
    """Show kilograms by default. Calibration itself stays in grams."""
    grams = float(grams)
    if str(unit).lower() == "g":
        return round(grams, 1)
    return round(grams / 1000.0, 3)
