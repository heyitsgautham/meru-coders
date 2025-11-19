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
cd backend
pip install -r requirements.txt

# 2. Configure settings
cp config/settings.sample.py config/settings.py

# 3. Run the backend server
python run.py
```

The backend API will start on **http://localhost:2490**

Open `frontend/index.html` in your browser to access the web interface.

---

## Installation

### Backend Setup

Navigate to the backend directory and install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

### Configuration

Copy the sample configuration file and edit if needed:

```bash
cd backend
cp config/settings.sample.py config/settings.py
```

Edit `backend/config/settings.py` to customize:
- `SECRET_KEY`: Flask secret key for sessions
- `UPLOAD_FOLDER`: Path for uploaded files
- `MAX_CONTENT_LENGTH`: Maximum upload size (default: 16MB)
- `CLIENT_SECRET`: Google OAuth credentials path (optional)

### Frontend Setup

The frontend is a static web application. Simply open `frontend/index.html` in a modern web browser, or serve it using any static file server:

```bash
# Option 1: Direct file access
open frontend/index.html

# Option 2: Using Python's HTTP server
cd frontend
python -m http.server 8080
```

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
meru-coders/
├── backend/                    # Backend API server
│   ├── run.py                 # Application entry point
│   ├── app.py                 # Flask application factory
│   ├── requirements.txt       # Python dependencies
│   ├── api/                   # API routes
│   │   └── routes.py          # REST API endpoints
│   ├── config/                # Configuration files
│   │   └── settings.py        # Application settings
│   ├── core/                  # Core logic
│   │   └── meter_analyzer.py # Meter identification engine
│   ├── ocr/                   # OCR integrations
│   │   ├── tesseract_ocr.py  # Tesseract wrapper
│   │   └── google_ocr.py     # Google OCR wrapper
│   ├── data/                  # Meter definition CSV files
│   │   ├── chanda_sama.csv
│   │   ├── chanda_ardhasama.csv
│   │   ├── chanda_vishama.csv
│   │   ├── chanda_matra.csv
│   │   ├── chanda_jaati.csv
│   │   └── examples.json
│   ├── experiments/           # Evaluation and test scripts
│   │   └── evaluation/        # Test datasets and results
│   ├── uploads/               # Upload storage
│   │   ├── photos/           # Uploaded images
│   │   ├── texts/            # Uploaded text files
│   │   └── results/          # Analysis results
│   └── utils/                 # Utility functions
│
└── frontend/                   # Frontend web application
    ├── index.html             # Main HTML page
    ├── src/                   # JavaScript source
    │   ├── app.js            # Application initialization
    │   ├── components/       # UI components
    │   │   ├── navigation.js
    │   │   ├── forms.js
    │   │   ├── examples.js
    │   │   └── results.js
    │   ├── services/         # API services
    │   │   └── api.js
    │   └── styles/           # CSS stylesheets
    │       ├── main.css
    │       ├── components.css
    │       └── responsive.css
    └── public/               # Static assets
        └── assets/
```

---

## Usage

### Running the Application

**Backend Server:**

```bash
cd backend
python run.py
```

The API server will start on port 2490. You'll see:
```
═══════════════════════════════════════
🚀 Starting Sanskrit Meter Identification System
═══════════════════════════════════════
📍 Local:   http://localhost:2490
📍 Network: http://192.168.x.x:2490
═══════════════════════════════════════
```

**Frontend Application:**

Open `frontend/index.html` in your web browser, or serve it via HTTP:

```bash
cd frontend
python -m http.server 8080
# Then visit http://localhost:8080
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
cd backend/experiments/evaluation

# Run evaluation tests
python test_chandojnanam.py
python test_shreevatsa.py
python test_skrutable.py
python test_functions.py
```

### Architecture Overview

**Backend (Flask REST API):**
- **MeterAnalyzer** (`backend/core/meter_analyzer.py`): Core engine for meter identification using fuzzy matching
- **Flask App** (`backend/app.py`): Application factory with CORS support
- **API Routes** (`backend/api/routes.py`): REST endpoints for text/image/file analysis
- **OCR Modules** (`backend/ocr/`): Tesseract and Google OCR integration

**Frontend (JavaScript SPA):**
- **App** (`frontend/src/app.js`): Application initialization and state management
- **Components** (`frontend/src/components/`): Modular UI components for navigation, forms, and results
- **API Service** (`frontend/src/services/api.js`): HTTP client for backend communication
- **Styles** (`frontend/src/styles/`): Responsive CSS with component-based architecture

---

## Technology Stack

**Backend:**
- Python 3.8+
- Flask 2.2.2+ (REST API framework)
- Tesseract OCR (optional, for image processing)
- Google Cloud Vision API (optional, for advanced OCR)
- indic-transliteration (for script conversion)

**Frontend:**
- Vanilla JavaScript (ES6+)
- HTML5 & CSS3
- Responsive design (mobile-friendly)

See `backend/requirements.txt` for complete Python dependencies.

---

## API Endpoints

The backend provides the following REST API endpoints:

- `POST /api/analyze/text` - Analyze Sanskrit text for meter identification
- `POST /api/analyze/image` - Upload and analyze image containing Sanskrit text
- `POST /api/analyze/file` - Upload and batch process text file
- `GET /api/examples` - Get sample meter examples

All endpoints support transliteration schemes via query parameters.

---

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

---

## License

This is an open-source project for Sanskrit text analysis.

---

## Acknowledgments

- Sanskrit meter definitions based on traditional chandas shastra
- Evaluation datasets from various Sanskrit texts (Meghaduta, Ramaraksha, etc.)
- OCR integration with Tesseract and Google Cloud Vision
