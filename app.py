from datetime import datetime
from typing import Dict, List, Optional

from dateutil import parser as dateparser
from flask import Flask, jsonify, request
from PIL import ExifTags, Image, ImageOps
import pytesseract

app = Flask(__name__)


def _fix_orientation(image: Image.Image) -> Image.Image:
    """Adjust image orientation based on EXIF data if available."""
    try:
        exif = image._getexif()
        if not exif:
            return image
        orientation_key = next(
            key for key, value in ExifTags.TAGS.items() if value == "Orientation"
        )
        orientation = exif.get(orientation_key)
        if orientation:
            return ImageOps.exif_transpose(image)
    except Exception:
        # If anything goes wrong, return the image as-is rather than failing the request.
        return image
    return image


def extract_text(image: Image.Image) -> str:
    corrected = _fix_orientation(image)
    grayscale = corrected.convert("L")
    return pytesseract.image_to_string(grayscale)


def _parse_date(text: str) -> Optional[str]:
    date_candidates = []
    lines = text.splitlines()
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        try:
            parsed = dateparser.parse(cleaned, fuzzy=True, default=datetime.min)
            if parsed.year > 1900:
                date_candidates.append(parsed)
        except (ValueError, OverflowError):
            continue
    if not date_candidates:
        return None
    best = sorted(date_candidates, key=lambda d: d, reverse=True)[0]
    return best.date().isoformat()


def _parse_amounts(text: str) -> Optional[float]:
    import re

    numbers: List[float] = []
    pattern = re.compile(r"(?:total|amount|balance|due)?[^\d]*(\d+[.,]\d{2})", re.IGNORECASE)
    for match in pattern.finditer(text):
        raw = match.group(1).replace(",", "")
        try:
            numbers.append(float(raw))
        except ValueError:
            continue
    if not numbers:
        return None
    return max(numbers)


def _parse_vendor(text: str) -> Optional[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    likely_headers = []
    for line in lines[:5]:
        if any(char.isdigit() for char in line):
            continue
        if len(line.split()) == 1 and len(line) <= 2:
            continue
        likely_headers.append(line)
    return likely_headers[0] if likely_headers else None


def _parse_items(text: str) -> List[str]:
    items: List[str] = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if len(line.split()) <= 1:
            continue
        if any(token.lower() in {"total", "subtotal", "tax", "balance"} for token in line.split()):
            continue
        items.append(line)
    return items[:10]


@app.route("/health", methods=["GET"])
def health() -> str:
    return "ok"


@app.route("/api/expenses/parse", methods=["POST"])
def parse_expense():
    if "image" not in request.files:
        return jsonify({"error": "Image file is required under the 'image' key."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Provided file has no filename."}), 400

    try:
        image = Image.open(file.stream)
    except Exception:
        return jsonify({"error": "Failed to read image. Ensure the file is a valid image."}), 400

    text = extract_text(image)

    response: Dict[str, Optional[str]] = {
        "vendor": _parse_vendor(text),
        "date": _parse_date(text),
        "total": _parse_amounts(text),
    }
    items = _parse_items(text)
    if items:
        response["items"] = items
    response["raw_text"] = text

    return jsonify(response)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
