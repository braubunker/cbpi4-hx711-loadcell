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


def apply_deadband(previous, candidate, deadband):
    """Keep the previous grams until the change is large enough to show."""
    candidate = float(candidate)
    if previous is None:
        return candidate
    if abs(candidate - float(previous)) < float(deadband):
        return float(previous)
    return candidate


def to_display(grams, unit):
    """Show kilograms by default. Calibration itself stays in grams."""
    grams = float(grams)
    if str(unit).lower() == "g":
        return round(grams, 1)
    return round(grams / 1000.0, 3)
