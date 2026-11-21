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
