"""
Deterministic barcode decoding -- the most reliable identification method.
"""

try:
    from pyzbar.pyzbar import decode
except ImportError:
    decode = None


def read_barcode(crop):
    if decode is None:
        return None

    results = decode(crop)
    if results:
        return results[0].data.decode("utf-8")
    return None