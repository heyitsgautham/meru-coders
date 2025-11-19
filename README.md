# Sanskrit Meter Identification

Professional web application for identification of meters (छन्द) in Sanskrit texts.

## Features

* Clean and intuitive user interface for meter analysis
* Fuzzy matching algorithm for meter identification
* Batch processing of entire files
* OCR integration for image-based text recognition (Tesseract + Google OCR)
* Support for multiple input/output transliteration schemes (Devanagari, IAST, ITRANS, etc.)

---

## Quick Start

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Configure settings
cp config/settings.sample.py config/settings.py

# 3. Run the application
python run.py
```

Access at: **http://localhost:2490**

---

## Installation

### Python Requirements

```bash
pip install -r requirements.txt
```

### Configuration

Copy the sample configuration file and edit if needed:

```bash
cp config/settings.sample.py config/settings.py
```

Edit `config/settings.py` to customize:
- `SECRET_KEY`: Flask secret key for sessions
- `UPLOAD_FOLDER`: Path for uploaded files
- `MAX_CONTENT_LENGTH`: Maximum upload size (default: 16MB)
- `CLIENT_SECRET`: Google OAuth credentials path (optional)

### OCR Setup (Optional)

#### Tesseract OCR

Install Tesseract and Indian language packs:

```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-san tesseract-ocr-mar \
  tesseract-ocr-hin tesseract-ocr-ben tesseract-ocr-tel \
  tesseract-ocr-tam tesseract-ocr-kan tesseract-ocr-mal tesseract-ocr-guj
```

#### Google OCR (Optional)

1. Visit: https://pypi.org/project/google-drive-ocr/
2. Follow setup instructions to create a Google Cloud Platform project
3. Download `client_secret.json` and place in project root
4. Update `CLIENT_SECRET` path in `config/settings.py`

---

## Project Structure

```
chanda/
├── run.py                  # Application entry point
├── config/                 # Configuration files
│   ├── settings.py         # Application settings (copy from .sample)
│   └── settings.sample.py  # Sample configuration
├── src/                    # Source code
│   ├── core/              # Core logic
│   │   └── meter_analyzer.py  # Meter identification engine
│   ├── web/               # Web application
│   │   ├── app.py         # Flask application factory
│   │   ├── routes.py      # Route handlers
│   │   └── uploads.py     # Upload configuration
│   ├── ocr/               # OCR integrations
│   │   ├── tesseract_ocr.py   # Tesseract wrapper
│   │   └── google_ocr.py      # Google OCR wrapper
│   └── utils/             # Utility functions
├── data/                   # Meter definition CSV files
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
└── tests/                  # Test cases
```

---

## Usage

### Running the Application

```bash
python run.py
```

The application will start on port 2490. You'll see:
```
═══════════════════════════════════════
🚀 Starting Sanskrit Meter Identification System
═══════════════════════════════════════
📍 Local:   http://localhost:2490
📍 Network: http://192.168.x.x:2490
═══════════════════════════════════════
```

### Input Methods

1. **Text Input**: Paste or type Sanskrit text directly
2. **Image Upload**: Upload images containing Sanskrit text (requires OCR)
3. **File Upload**: Upload text files for batch processing

### Output Schemes

Choose from multiple transliteration schemes:
- Devanagari (default)
- IAST (International Alphabet of Sanskrit Transliteration)
- ITRANS
- And more...

---

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_meter_analyzer.py
```

### Module Overview

- **MeterAnalyzer** (`src/core/meter_analyzer.py`): Core engine for meter identification
- **Flask App** (`src/web/app.py`): Application factory pattern with dependency injection
- **Routes** (`src/web/routes.py`): HTTP endpoints for text/image/file analysis
- **OCR Modules** (`src/ocr/`): Tesseract and Google OCR wrappers

---

## Requirements

- Python 3.8+
- Flask 2.2.2+
- Tesseract OCR (optional, for image processing)
- Google Cloud credentials (optional, for Google OCR)

See `requirements.txt` for complete Python dependencies.

---

## License

This is an open-source project for Sanskrit text analysis
