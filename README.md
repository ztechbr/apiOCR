# apiOCR

Expense bill OCR API built with Flask. Send an image (e.g., a photo taken on your phone) and receive extracted information such as vendor, date, total, and itemized lines.

## Features
- Accepts JPEG/PNG uploads from mobile devices.
- Corrects image orientation via EXIF metadata for iPhone photos.
- Performs OCR using Tesseract and heuristically extracts key fields.
- Dockerfile and Docker Compose for local development or deployment.

## Getting started

### Prerequisites
- Docker and Docker Compose installed.

### Run with Docker
```bash
docker compose up --build
```

The API will be available at `http://localhost:5000`.

### API

**Endpoint:** `POST /api/expenses/parse`

**Content-Type:** `multipart/form-data`

**Field:** `image` — the photo of your receipt/expense bill.

**Sample request using `curl`:**
```bash
curl -X POST http://localhost:5000/api/expenses/parse \
  -F "image=@/path/to/your/receipt.jpg"
```

**Sample response:**
```json
{
  "vendor": "COFFEE SHOP",
  "date": "2024-08-24",
  "total": 12.5,
  "items": [
    "Latte 8oz",
    "Almond croissant"
  ],
  "raw_text": "..."
}
```

### Health check
`GET /health` returns `ok`.

### Development without Docker
1. Install system Tesseract (e.g., `apt-get install tesseract-ocr`).
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the API:
   ```bash
   FLASK_APP=app.py flask run --host=0.0.0.0 --port=5000
   ```
