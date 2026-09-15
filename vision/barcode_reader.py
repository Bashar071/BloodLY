"""
Deterministic barcode decoding -- the most reliable identification method.
"""
from pyzbar.pyzbar import decode


def read_barcode(crop):
    results = decode(crop)
    if results:
        return results[0].data.decode("utf-8")
    return None