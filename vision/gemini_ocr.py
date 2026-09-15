"""
Optional AI OCR fallback -- only used when barcode + cap color both fail.
Never used to infer blood type from liquid appearance, only printed text.
"""
import time
import json
import cv2
from config import GEMINI_MODEL, GEMINI_CACHE_TTL_SECONDS

_client = None
_cache = {}

PROMPT = """
You are reading a label on a single blood sample tube in a lab inventory
system. Read ONLY the printed text visible on the label (ID numbers, and
blood type text like A+, A-, B+, B-, AB+, AB-, O+, O- if printed).

Do NOT infer or guess blood type from the color or appearance of the liquid
in the tube -- this is not visually determinable and must never be reported.
If no blood type text is printed, set blood_type to null.

Respond ONLY with JSON in this exact structure, no other text:
{"blood_type": "...", "id_text": "...", "confidence": "high"|"medium"|"low"}
"""


def _get_client():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client()
    return _client


def read_label_with_gemini(crop):
    crop_hash = hash(crop.tobytes())
    cached = _cache.get(crop_hash)
    if cached and (time.time() - cached[1] < GEMINI_CACHE_TTL_SECONDS):
        return cached[0]

    try:
        from PIL import Image
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        client = _get_client()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[pil_img, PROMPT],
        )
        text = response.text.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
    except Exception as e:
        result = {"blood_type": None, "id_text": None, "confidence": "low", "error": str(e)}

    _cache[crop_hash] = (result, time.time())
    return result