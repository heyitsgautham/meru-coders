# Meru Coders - Sanskrit Meter Identification# Sanskrit Meter Identification



🔍 **An intelligent web application for automated identification and analysis of Sanskrit meters (छन्द/Chhandas)**Professional web application for identification of meters (छन्द) in Sanskrit texts.



Meru Coders is a powerful tool designed to help Sanskrit scholars, students, and enthusiasts identify and analyze prosodic patterns in Sanskrit verse. Using advanced fuzzy matching algorithms and comprehensive meter databases, it can accurately identify various meter types from text input, images, or files.## Features



---* Clean and intuitive user interface for meter analysis

* Fuzzy matching algorithm for meter identification

## ✨ Features* Batch processing of entire files

* OCR integration for image-based text recognition (Tesseract + Google OCR)

- 🎯 **Intelligent Meter Detection** - Advanced fuzzy matching algorithm for accurate meter identification* Support for multiple input/output transliteration schemes (Devanagari, IAST, ITRANS, etc.)

- 📊 **Multiple Meter Types** - Support for Sama, Ardhasama, Vishama, Matra, and Jaati-based meters

- 🖼️ **OCR Integration** - Extract and analyze text from images using Tesseract and Google Cloud Vision---

- 📝 **Flexible Input Methods** - Text input, image upload, or file upload for batch processing

- 🌐 **Transliteration Support** - Multiple schemes including Devanagari, IAST, ITRANS, and more## Quick Start

- 🎨 **Modern UI** - Clean, responsive interface that works on desktop and mobile devices

- 🚀 **REST API** - Well-documented API endpoints for integration with other applications```bash

- 📚 **Comprehensive Database** - Extensive collection of meter definitions and patterns# 1. Install Python dependencies

cd backend

---pip install -r requirements.txt



## 🚀 Quick Start# 2. Configure settings

cp config/settings.sample.py config/settings.py

### Prerequisites

# 3. Run the backend server

- Python 3.8 or higherpython run.py

- Modern web browser (Chrome, Firefox, Safari, Edge)```

- (Optional) Tesseract OCR for image processing

The backend API will start on **http://localhost:2490**

### Installation & Setup

Open `frontend/index.html` in your browser to access the web interface.

1. **Clone the repository**

   ```bash---

   git clone https://github.com/codedbykishore/meru-coders.git

   cd meru-coders## Installation

   ```

### Backend Setup

2. **Install backend dependencies**

   ```bashNavigate to the backend directory and install dependencies:

   cd backend

   pip install -r requirements.txt```bash

   ```cd backend

pip install -r requirements.txt

3. **Configure the application** (optional)```

   ```bash

   cp config/settings.sample.py config/settings.py### Configuration

   # Edit config/settings.py to customize settings

   ```Copy the sample configuration file and edit if needed:



4. **Start the backend server**```bash

   ```bashcd backend

   python run.pycp config/settings.sample.py config/settings.py

   ``````

   

   The API will be available at `http://localhost:2490`Edit `backend/config/settings.py` to customize:

- `SECRET_KEY`: Flask secret key for sessions

5. **Open the frontend**- `UPLOAD_FOLDER`: Path for uploaded files

   - `MAX_CONTENT_LENGTH`: Maximum upload size (default: 16MB)

   Simply open `frontend/index.html` in your browser, or serve it via HTTP:- `CLIENT_SECRET`: Google OAuth credentials path (optional)

   ```bash

   cd ../frontend### Frontend Setup

   python -m http.server 8080

   # Visit http://localhost:8080The frontend is a static web application. Simply open `frontend/index.html` in a modern web browser, or serve it using any static file server:

   ```

```bash

---# Option 1: Direct file access

open frontend/index.html

## 📖 Usage Guide

# Option 2: Using Python's HTTP server

### Text Analysiscd frontend

python -m http.server 8080

1. Navigate to the **Text Input** tab```

2. Enter or paste Sanskrit text (in Devanagari or Roman script)

3. Select your preferred output transliteration scheme### OCR Setup (Optional)

4. Click **Analyze** to identify the meters

5. View detailed results including meter names, patterns, and confidence scores#### Tesseract OCR



### Image Analysis (OCR)Install Tesseract and Indian language packs:



1. Navigate to the **Image Upload** tab```bash

2. Upload an image containing Sanskrit text# Ubuntu/Debian

3. Choose OCR engine (Tesseract or Google OCR)sudo apt install tesseract-ocr tesseract-ocr-san tesseract-ocr-mar \

4. Select output transliteration scheme  tesseract-ocr-hin tesseract-ocr-ben tesseract-ocr-tel \

5. Click **Process** to extract text and analyze meters  tesseract-ocr-tam tesseract-ocr-kan tesseract-ocr-mal tesseract-ocr-guj

```

### File Processing

#### Google OCR (Optional)

1. Navigate to the **File Upload** tab

2. Upload a text file containing Sanskrit verses1. Visit: https://pypi.org/project/google-drive-ocr/

3. Configure processing options2. Follow setup instructions to create a Google Cloud Platform project

4. Download results as JSON or text file3. Download `client_secret.json` and place in project root

4. Update `CLIENT_SECRET` path in `config/settings.py`

---

---

## 🏗️ Project Architecture

## Project Structure

### Backend (Flask REST API)

```

```meru-coders/

backend/├── backend/                    # Backend API server

├── run.py                     # Application entry point│   ├── run.py                 # Application entry point

├── app.py                     # Flask app factory│   ├── app.py                 # Flask application factory

├── requirements.txt           # Python dependencies│   ├── requirements.txt       # Python dependencies

├── api/│   ├── api/                   # API routes

│   └── routes.py             # REST API endpoints│   │   └── routes.py          # REST API endpoints

├── core/│   ├── config/                # Configuration files

│   └── meter_analyzer.py     # Meter identification engine│   │   └── settings.py        # Application settings

├── ocr/│   ├── core/                  # Core logic

│   ├── tesseract_ocr.py      # Tesseract OCR integration│   │   └── meter_analyzer.py # Meter identification engine

│   └── google_ocr.py         # Google Cloud Vision integration│   ├── ocr/                   # OCR integrations

├── config/│   │   ├── tesseract_ocr.py  # Tesseract wrapper

│   └── settings.py           # Application configuration│   │   └── google_ocr.py     # Google OCR wrapper

├── data/│   ├── data/                  # Meter definition CSV files

│   ├── chanda_sama.csv       # Sama meter definitions│   │   ├── chanda_sama.csv

│   ├── chanda_ardhasama.csv  # Ardhasama meter definitions│   │   ├── chanda_ardhasama.csv

│   ├── chanda_vishama.csv    # Vishama meter definitions│   │   ├── chanda_vishama.csv

│   ├── chanda_matra.csv      # Matra-based meters│   │   ├── chanda_matra.csv

│   ├── chanda_jaati.csv      # Jaati-based meters│   │   ├── chanda_jaati.csv

│   └── examples.json         # Sample verses│   │   └── examples.json

├── experiments/│   ├── experiments/           # Evaluation and test scripts

│   └── evaluation/           # Test scripts and datasets│   │   └── evaluation/        # Test datasets and results

└── uploads/│   ├── uploads/               # Upload storage

    ├── photos/               # Uploaded images│   │   ├── photos/           # Uploaded images

    ├── texts/                # Uploaded text files│   │   ├── texts/            # Uploaded text files

    └── results/              # Analysis outputs│   │   └── results/          # Analysis results

```│   └── utils/                 # Utility functions

│

### Frontend (JavaScript SPA)└── frontend/                   # Frontend web application

    ├── index.html             # Main HTML page

```    ├── src/                   # JavaScript source

frontend/    │   ├── app.js            # Application initialization

├── index.html                # Main HTML page    │   ├── components/       # UI components

├── src/    │   │   ├── navigation.js

│   ├── app.js               # Application initialization    │   │   ├── forms.js

│   ├── components/    │   │   ├── examples.js

│   │   ├── navigation.js    # Navigation component    │   │   └── results.js

│   │   ├── forms.js         # Input forms    │   ├── services/         # API services

│   │   ├── examples.js      # Example verses display    │   │   └── api.js

│   │   └── results.js       # Results visualization    │   └── styles/           # CSS stylesheets

│   ├── services/    │       ├── main.css

│   │   └── api.js           # Backend API client    │       ├── components.css

│   └── styles/    │       └── responsive.css

│       ├── main.css         # Core styles    └── public/               # Static assets

│       ├── components.css   # Component styles        └── assets/

│       └── responsive.css   # Mobile responsiveness```

└── public/

    └── assets/              # Static assets---

```

## Usage

---

### Running the Application

## 🔌 API Documentation

**Backend Server:**

### Base URL

``````bash

http://localhost:2490/apicd backend

```python run.py

```

### Endpoints

The API server will start on port 2490. You'll see:

#### Analyze Text```

```http═══════════════════════════════════════

POST /api/analyze/text🚀 Starting Sanskrit Meter Identification System

Content-Type: application/json═══════════════════════════════════════

📍 Local:   http://localhost:2490

{📍 Network: http://192.168.x.x:2490

  "text": "Sanskrit verse in Devanagari or Roman",═══════════════════════════════════════

  "output_scheme": "devanagari"```

}

```**Frontend Application:**



#### Analyze ImageOpen `frontend/index.html` in your web browser, or serve it via HTTP:

```http

POST /api/analyze/image```bash

Content-Type: multipart/form-datacd frontend

python -m http.server 8080

image: <file># Then visit http://localhost:8080

ocr_engine: tesseract|google```

output_scheme: devanagari

```### Input Methods



#### Analyze File1. **Text Input**: Paste or type Sanskrit text directly

```http2. **Image Upload**: Upload images containing Sanskrit text (requires OCR)

POST /api/analyze/file3. **File Upload**: Upload text files for batch processing

Content-Type: multipart/form-data

### Output Schemes

file: <file>

output_scheme: devanagariChoose from multiple transliteration schemes:

```- Devanagari (default)

- IAST (International Alphabet of Sanskrit Transliteration)

#### Get Examples- ITRANS

```http- And more...

GET /api/examples

```---



### Supported Transliteration Schemes## Development



- `devanagari` - देवनागरी script### Running Tests

- `iast` - International Alphabet of Sanskrit Transliteration

- `itrans` - Indian languages transliteration```bash

- `slp1` - Sanskrit Library Phonetic Basiccd backend/experiments/evaluation

- `velthuis` - Velthuis transliteration

- `wx` - WX notation# Run evaluation tests

python test_chandojnanam.py

---python test_shreevatsa.py

python test_skrutable.py

## 🛠️ Technology Stackpython test_functions.py

```

### Backend

- **Python 3.8+** - Core programming language### Architecture Overview

- **Flask 2.2.2+** - Web framework and REST API

- **indic-transliteration** - Script conversion library**Backend (Flask REST API):**

- **Tesseract OCR** - Open-source OCR engine- **MeterAnalyzer** (`backend/core/meter_analyzer.py`): Core engine for meter identification using fuzzy matching

- **Google Cloud Vision API** - Advanced OCR service- **Flask App** (`backend/app.py`): Application factory with CORS support

- **Pandas** - Data processing for meter databases- **API Routes** (`backend/api/routes.py`): REST endpoints for text/image/file analysis

- **OCR Modules** (`backend/ocr/`): Tesseract and Google OCR integration

### Frontend

- **HTML5 & CSS3** - Modern web standards**Frontend (JavaScript SPA):**

- **Vanilla JavaScript (ES6+)** - No framework dependencies- **App** (`frontend/src/app.js`): Application initialization and state management

- **Responsive Design** - Mobile-first approach- **Components** (`frontend/src/components/`): Modular UI components for navigation, forms, and results

- **Fetch API** - HTTP client for API communication- **API Service** (`frontend/src/services/api.js`): HTTP client for backend communication

- **Styles** (`frontend/src/styles/`): Responsive CSS with component-based architecture

---

---

## 🧪 Testing & Evaluation

## Technology Stack

The project includes comprehensive evaluation scripts and test datasets:

**Backend:**

```bash- Python 3.8+

cd backend/experiments/evaluation- Flask 2.2.2+ (REST API framework)

- Tesseract OCR (optional, for image processing)

# Run evaluation tests- Google Cloud Vision API (optional, for advanced OCR)

python test_chandojnanam.py      # Test against Chandojnanam tool- indic-transliteration (for script conversion)

python test_shreevatsa.py        # Test against Shreevatsa's algorithm

python test_skrutable.py         # Test against Skrutable tool**Frontend:**

python test_functions.py         # Unit tests for core functions- Vanilla JavaScript (ES6+)

```- HTML5 & CSS3

- Responsive design (mobile-friendly)

### Test Datasets

See `backend/requirements.txt` for complete Python dependencies.

- **Meghaduta** - Classical Sanskrit poetry

- **Rajendrakarnapura** - Traditional verses---

- **Ramaraksha** - Devotional hymn

- **Shantavilasa** - Literary composition## API Endpoints



Each dataset includes:The backend provides the following REST API endpoints:

- Original texts from multiple sources

- Ground truth meter annotations- `POST /api/analyze/text` - Analyze Sanskrit text for meter identification

- OCR outputs (Tesseract & Google)- `POST /api/analyze/image` - Upload and analyze image containing Sanskrit text

- Evaluation results and accuracy metrics- `POST /api/analyze/file` - Upload and batch process text file

- `GET /api/examples` - Get sample meter examples

---

All endpoints support transliteration schemes via query parameters.

## ⚙️ Configuration

---

### Backend Configuration

## Contributing

Edit `backend/config/settings.py`:

Contributions are welcome! Please feel free to submit issues or pull requests.

```python

# Flask Configuration---

SECRET_KEY = 'your-secret-key-here'

DEBUG = False## License



# Upload SettingsThis is an open-source project for Sanskrit text analysis.

UPLOAD_FOLDER = 'uploads'

MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size---



# OCR Configuration## Acknowledgments

CLIENT_SECRET = 'path/to/client_secret.json'  # For Google OCR

- Sanskrit meter definitions based on traditional chandas shastra

# Server Settings- Evaluation datasets from various Sanskrit texts (Meghaduta, Ramaraksha, etc.)

HOST = '0.0.0.0'- OCR integration with Tesseract and Google Cloud Vision

PORT = 2490
```

### OCR Setup

#### Tesseract OCR (Recommended for Local Use)

Install Tesseract and Sanskrit language pack:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-san

# Additional Indian language packs (optional)
sudo apt-get install tesseract-ocr-hin tesseract-ocr-mar \
  tesseract-ocr-ben tesseract-ocr-tam tesseract-ocr-tel

# macOS
brew install tesseract tesseract-lang
```

#### Google Cloud Vision (Optional - Better Accuracy)

1. Create a Google Cloud Platform project
2. Enable the Vision API
3. Create OAuth 2.0 credentials
4. Download `client_secret.json`
5. Place it in the project root
6. Update `CLIENT_SECRET` path in `config/settings.py`

For detailed setup: https://cloud.google.com/vision/docs/setup

---

## 📚 Meter Types Supported

### Sama Meters (समछन्द)
All four padas have identical syllabic patterns
- Anushtup, Indravajra, Upendravajra, Vasantatilaka, Malini, and more

### Ardhasama Meters (अर्धसमछन्द)
Odd and even padas have different but repeating patterns
- Upajati, Vamshastha, and others

### Vishama Meters (विषमछन्द)
Each pada has a unique pattern
- Rathoddhata, Sragdhara, and more

### Matra Meters (मात्राछन्द)
Based on syllable weight (mora count)
- Arya, Giti, Vaitalia, and variants

### Jaati Meters (जातिछन्द)
Based on syllable groups (ganas)
- Various traditional classifications

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Ways to Contribute

- 🐛 **Report bugs** - Open an issue with details
- 💡 **Suggest features** - Share your ideas for improvements
- 📝 **Improve documentation** - Help us make docs clearer
- 🔧 **Submit pull requests** - Fix bugs or add features
- 📊 **Add meter definitions** - Expand the meter database
- 🧪 **Add test cases** - Improve evaluation coverage

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and test thoroughly
4. Commit with clear messages: `git commit -m "feat: add new feature"`
5. Push to your fork: `git push origin feature/your-feature-name`
6. Open a pull request with a detailed description

### Commit Message Convention

We follow the Conventional Commits specification:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

---

## 📄 License

This project is open-source and available for use in Sanskrit text analysis, research, and education.

---

## 🙏 Acknowledgments

### Data Sources
- Traditional Sanskrit prosody texts (Pingala's Chandahshastra, etc.)
- Meter definitions compiled from classical sources
- Test datasets from public Sanskrit repositories

### Tools & Libraries
- **Tesseract OCR** - Open-source OCR engine
- **Google Cloud Vision** - Advanced image text detection
- **indic-transliteration** - Script conversion utilities
- **Flask** - Web framework

### Inspiration
- Shreevatsa's Sanskrit meter identification work
- Chandojnanam meter analysis tool
- Skrutable Sanskrit toolkit

### Community
Special thanks to all contributors, testers, and users who have helped improve this project.

---

## 📞 Contact & Support

- **GitHub Issues**: For bug reports and feature requests
- **Repository**: [github.com/codedbykishore/meru-coders](https://github.com/codedbykishore/meru-coders)
- **Developer**: [@codedbykishore](https://github.com/codedbykishore)

---

## 🗺️ Roadmap

### Planned Features

- [ ] Advanced meter variation detection
- [ ] Meter composition suggestions
- [ ] Batch API for processing multiple files
- [ ] User authentication and saved analyses
- [ ] Mobile app (React Native)
- [ ] Docker containerization
- [ ] Expanded meter database
- [ ] Machine learning-based pattern recognition
- [ ] Integration with Sanskrit corpora
- [ ] Export to various formats (PDF, LaTeX, etc.)

---

<div align="center">

**Built with ❤️ for Sanskrit scholars and enthusiasts**

⭐ Star us on GitHub if you find this project useful!

[Report Bug](https://github.com/codedbykishore/meru-coders/issues) · [Request Feature](https://github.com/codedbykishore/meru-coders/issues) · [Documentation](https://github.com/codedbykishore/meru-coders/wiki)

</div>
