# Meru Coders - AI-Powered Sanskrit Meter Identification System

**SIH 2025 Grand Finale | Problem Statement #25158 | Team: Erase Sure**

A comprehensive AI-powered platform for identifying, analyzing, and learning Sanskrit meters (Chandas). Combines 2,500-year-old traditional knowledge from Pingala's Chandas Shastra with modern AI/ML technologies.

---

## Quick summary

| Feature | Achievement |
|---------|-------------|
| **Accuracy** | 94.6% whole-verse and 99.3% first-line on a 147-verse benchmark ([details](#accuracy-evaluation)) |
| **Database** | 1,920+ meters across all categories (largest digital collection) |
| **AI Features** | Multi-modal chatbot, RAG-powered knowledge base, voice interaction |
| **Input Modes** | Text, Image (OCR), Audio (STT), File upload (DOCX/TXT) |
| **Special Features** | Daṇḍaka detection, Community platform, Interactive LG Lab, TTS with voice selection |
| **Architecture** | Modern REST API + React SPA with real-time WebSocket support |
| **Testing** | Offline pytest and vitest suites in CI, plus corpus evaluation harnesses |

---

## Repository layout

```
meru-coders/
├── backend/                    Flask API, Python 3.11
│   ├── app.py, run.py          app factory and server entry point
│   ├── api/                    REST routes, chatbot, community feed, WebSocket
│   ├── auth/                   username and password login, Google OAuth through Supabase
│   ├── contributions/          crowd-sourced verse and meter submissions
│   ├── core/                   meter engine (chanda.py and its chanda_* mixins), daṇḍaka detector, text classifier,
│   │                           Gemini input validator, RAG engine
│   ├── models/                 Supabase data access for community and contributions
│   ├── ocr/                    Google Cloud Vision and Tesseract OCR
│   ├── utils/                  file processing, pada splitting, TTS, upload cleanup
│   ├── pipeline/               dataset checks, accuracy benchmarks, Rigveda ground-truth build
│   ├── experimental/           alternative engines and the local TTS model that evaluation/ compares; not served
│   ├── config/settings.py      every setting, read from environment variables
│   ├── data/                   meter definition CSVs and the ChromaDB index
│   ├── source/                 verse corpora behind the dataset browser and verse search
│   ├── tests/                  offline pytest suite that CI runs
│   ├── evaluation/             corpus accuracy runs and comparisons with other engines
│   └── scripts/                dataset builders, Supabase setup, smoke and manual scripts
├── frontend/                   React 18, Vite and TypeScript single-page app
├── reference/                  IITK, GPT and ICU baseline engines used by evaluation/
├── docs/                       prosody references and hackathon write-ups
├── scripts/deploy.sh           Google Cloud Run deployment
├── docker-compose.yml          backend on :5000 and frontend on :8080
└── pyproject.toml, uv.lock     Python dependencies
```

## Quick start

You need Python 3.11 with [uv](https://docs.astral.sh/uv/), Node 20, and optionally Tesseract for local OCR.

```bash
git clone https://github.com/heyitsgautham/meru-coders.git
cd meru-coders

# Backend: creates .venv from uv.lock, then serves http://localhost:5000
uv sync
cp .env.example .env                    # optional, every variable has a default
uv run python backend/run.py

# Frontend, in a second terminal: serves http://localhost:8080
cd frontend
npm ci
npm run dev
```

Without uv, `pip install -r backend/requirements.txt` installs the same pinned versions; that file is exported from `uv.lock`.
[`frontend/README.md`](frontend/README.md) covers the client's configuration, layout, styling and tests.

Check that the API answers:

```bash
curl http://localhost:5000/health
curl -X POST http://localhost:5000/api/identify/text \
  -H 'Content-Type: application/json' \
  -d '{"text": "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"}'
```

The second call returns `अनुष्टुभ् (पाद 1-2) (anuṣṭubh) [10.0] | अनुष्टुभ् (पाद 3-4) (anuṣṭubh) [10.0]` as the primary match.

Meter identification, dataset browsing and verse search need no keys.
The other features switch on as you add configuration.

| Feature | What it needs |
|---|---|
| Chatbot and AI input validation | `GEMINI_API_KEY_1` (up to `_6`) |
| Signup, community feed, contributions | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, and `VITE_SUPABASE_*` for Google sign-in |
| Cloud Vision OCR and Google Cloud TTS | `GOOGLE_APPLICATION_CREDENTIALS`; Tesseract is the OCR fallback |
| Retrieval-augmented chatbot answers | `uv sync --extra rag` and the index in `backend/data/chroma_db/` |
| Voice input | `INDIC_ASR_URL` pointing at an IndicConformer service |
| Admin login | `ADMIN_PASSWORD` |
| Error reports to Sentry | `SENTRY_DSN`, plus optional `SENTRY_ENVIRONMENT` and `SENTRY_TRACES_SAMPLE_RATE` |

### Docker

```bash
docker compose up --build
```

This builds both images from the repository root and starts the backend on port 5000 and the nginx-served frontend on port 8080.
The frontend waits for the backend's `/health` check.
Compose passes the root `.env` to the backend container when it exists.

## Running tests

```bash
uv run pytest                    # offline backend suite, corpus accuracy floors included
uv run pytest --cov              # same, with the coverage floor from pyproject.toml
uv run pytest -m corpus          # only the accuracy floors on the classical and Rigveda corpora
uv run python -m backend.pipeline.validate   # meter table, corpus and registry checks
uv run ruff check .              # lint
uv run ruff format --check .     # formatting

cd frontend
npm run lint
npm run typecheck
npm test                         # vitest
npm run test:coverage            # vitest with the coverage floor from vitest.config.ts
npm run build
```

GitHub Actions runs all of these on every push and pull request, plus `pip-audit`, `npm audit` and a gitleaks secret scan.
The suite in `backend/tests/` runs without network access or API keys.
`backend/tests/test_engine_golden.py` pins the engine's output on 150 reference verses, and `backend/tests/test_corpus_accuracy.py` holds the accuracy figures below as floors.

## Data pipeline

The engine and the API read committed datasets only: meter definition CSVs in `backend/data/`, verse corpora in `backend/source/`, and a generated Rigveda ground-truth module in `backend/evaluation/data/`.
`backend/pipeline/` checks them and builds the generated ones, and the Data quality CI job runs those checks on every push.

```bash
uv run python -m backend.pipeline.build --check   # every derived dataset matches a fresh build
uv run python -m backend.pipeline.build           # validate the inputs, then regenerate them
uv run python -m backend.pipeline.validate        # schema and content checks against known_issues.json
```

`backend/tests/pipeline/test_data_quality.py` pins each dataset's schema and row count, rejects duplicate verses, and holds the meter tables' known defects to their recorded counts.
[docs/data-pipeline.md](docs/data-pipeline.md) traces each file to its origin and its readers, lists the checks, and records the defects the meter tables still carry.

## Architecture

```
React SPA (frontend/)  ──HTTP /api/*, Socket.IO──▶  Flask app (backend/app.py)
                                                      │
        ┌──────────────────────┬──────────────────────┼────────────────────────┬─────────────────────┐
        ▼                      ▼                      ▼                        ▼                     ▼
  api/routes.py          api/chatbot.py         auth/, api/community.py   ocr/                  utils/
  identify, datasets,    Gemini chat with       contributions/            Cloud Vision,         file extraction,
  verse search, TTS      meter-analysis tools   (Supabase)                Tesseract             TTS, cleanup job
        │                      │
        ▼                      ▼
  core/chanda.py  ◀── meter CSVs in backend/data/ (sama, ardhasama, viṣama, mātrā, jāti, Vedic)
  syllabify → mark laghu/guru → match patterns → score confidence → pick Vedic or classical mode
```

`create_app()` builds one `Chanda` engine at startup and shares it across requests.
The engine loads the meter definition CSVs once, splits each line into syllables, marks each syllable laghu or guru, and matches the pattern against every meter.
Each match gets a confidence score, and `display_chanda_primary` lists the matches within 80% of the best score.
For whole verses, a text classifier picks Vedic syllable-count rules or classical pattern rules.
Gemini is optional and only screens input and powers the chatbot.

`backend/core/chanda.py` keeps the constructor and the `identify_*` entry points; the rest of the engine lives in mixin modules beside it (`chanda_syllables`, `chanda_matching`, `chanda_vedic` and others).
`backend/api/schemas.py` declares the JSON body of each POST route as a pydantic model, and `parse_body` in `backend/api/validation.py` validates it before the handler runs.
A malformed body gets a 400 whose `error` names the first bad field and whose `details` lists every problem.
Every response carries an `X-Request-ID` header that also appears on each log line, and `GET /metrics` serves Prometheus request counts and latency histograms.
`LOG_FORMAT=json` writes one JSON object per log line.
With `SENTRY_DSN` set, unhandled exceptions go to Sentry tagged with the same request ID, and no request bodies or cookies are sent.

### API endpoints

All routes sit under `/api` except `/health`.

| Area | Routes |
|---|---|
| Identification | `POST /identify/text`, `/identify/image`, `/identify/file`, `/identify/dandaka`, `/file/extract`, `/ocr/extract`; `GET /download/<filename>` |
| Datasets and verse search | `GET /datasets`, `/datasets/<id>`, `/examples`, `/schemes`; `POST /sloka/search`, `/sloka/validate` |
| Speech | `POST /tts/generate`, `/audio/transcribe`; `GET /tts/audio/<filename>` |
| Chatbot | `POST /chatbot/chat`, `/chatbot/analyze-meter`; `GET /chatbot/history/<id>`, `/chatbot/conversations`, `/chatbot/personas`, `/chatbot/health`; `DELETE /chatbot/clear/<id>` |
| Auth | `POST /auth/signup`, `/auth/login`, `/auth/logout`, `/auth/admin-login`, `/auth/oauth/start`, `/auth/oauth/exchange`; `GET /auth/profile` |
| Contributions | `POST /contributions/submit`; `GET /contributions/my-contributions`, `/contributions/approved`, `/contributions/admin/pending`; `POST /contributions/admin/approve/<id>`, `/contributions/admin/reject/<id>` |
| Community | 38 routes under `/community` for posts, comments, likes, bookmarks, follows, notifications, search, reports and image upload |
| Service | `GET /health`, `/metrics` (Prometheus), `/api/info` |

---

## Core features

### 1. Multi-mode meter identification

#### **Mode 1: Text Input**
- Direct Sanskrit text input in Devanagari, IAST, SLP1, or other schemes
- Automatic script detection and normalization
- Supports verse, line, or pada-level analysis
- **Endpoint:** `POST /api/identify/text`

#### **Mode 2: Image Input (OCR)**
- Upload images of Sanskrit texts (manuscripts, books, inscriptions)
- Supports 9+ Indian scripts: Devanagari, Telugu, Tamil, Kannada, Malayalam, Bengali, Gujarati, etc.
- Dual OCR engines: Tesseract + Google Vision API
- Automatic preprocessing and enhancement
- **Endpoint:** `POST /api/identify/image`

#### **Mode 3: Audio Input (Speech-to-Text)**
- Record or upload Sanskrit audio
- Google Cloud Speech-to-Text integration
- Real-time transcription
- WAV format support with automatic conversion
- **Endpoint:** `POST /api/audio/transcribe`

#### **Mode 4: File Upload**
- Batch processing of text files (TXT)
- Document parsing (DOCX); the PDF extractor exists but `FileProcessor.ALLOWED_EXTENSIONS` keeps PDF uploads off
- Multi-verse analysis with line-by-line results
- Download results as JSON/CSV
- **Endpoint:** `POST /api/identify/file`

#### **Mode 5: Daṇḍaka/Rājaśyāmalā Identification** **NEW**
- Special mode for unmetrical long-form verses
- Akṣara counting with virāma rules
- Classification: Saṃkīrṇa, Madhyama, Prabandha, Ati-daṇḍakam
- Rājaśyāmalā Stotram detection with semantic analysis
- Confidence scoring with keyword matching
- **Endpoint:** `POST /api/identify/dandaka`

### 2. AI chatbot with text, image and voice input

**Revolutionary conversational interface for Sanskrit prosody learning!**

#### Features
- **Multi-Modal Input:**
  - 💬 Text messages (ask questions about meters, rules, examples)
  - 🎤 Voice messages (speak Sanskrit verses or questions)
  - 🖼️ Image messages (upload images of verses for analysis)
  
- **Agentic Capabilities:**
  - Automatic meter identification when Sanskrit verses are detected
  - Invokes identification API autonomously
  - Provides detailed explanations with scansion, patterns, and meter families
  
- **RAG-Powered Responses:** (2,844 documents)
  - Retrieves information from 1,920+ meter definitions
  - References classical texts (Chandovallari, Pingala's Chandas Shastra)
  - Provides source citations: `[Source: chanda_sama.csv]`, `[Source: chandovallari.txt]`
  - Reduces hallucinations by 60-80%
  
- **Personality Modes:**
  - **Default:** General Sanskrit prosody assistant
  - **Scholar:** Formal academic responses with citations
  - **Teacher:** Educational, beginner-friendly explanations
  - **Poet:** Creative, artistic perspective on meters
  - **Acharya Pingala:** Speaks as the legendary prosody master
  
- **Conversation Memory:**
  - Multi-turn conversations with context retention
  - Session-based chat history
  - User-specific conversation threads
  
- **Real-Time Streaming:**
  - WebSocket support for live responses
  - Character-by-character streaming for natural feel
  
- **Powered by:** Google Gemini 2.5 Flash, rotating across up to six API keys (`GEMINI_API_KEY_1` to `_6`)

**Endpoints:**
- `POST /api/chatbot/chat` - Chat; an audio or image attachment travels in the same request
- `POST /api/chatbot/analyze-meter` - Identify the meter of a verse from the chat
- `GET /api/chatbot/history/{conversation_id}` - Retrieve a conversation
- `GET /api/chatbot/conversations` - List conversations
- `DELETE /api/chatbot/clear/{conversation_id}` - Clear a conversation
- `GET /api/chatbot/personas` - List the available personas

### 3. Text-to-speech with voice selection

**Multi-tier TTS system with male/female voice options**

#### Supported Engines (Priority Order):
1. **Google Cloud TTS** (Premium quality)
   - Male: `hi-IN-Wavenet-B` (Rishi voice)
   - Female: `hi-IN-Wavenet-A` (Lekha voice)
   - Requires billing enabled
   
2. **edge-tts** (Microsoft Bing)
   - Male: `hi-IN-MadhurNeural`
   - Female: `hi-IN-SwaraNeural`
   - Good quality but may have rate limits
   
3. **pyttsx3** (Offline)
   - Male: Rishi (English-India)
   - Female: Lekha (Hindi-India)
   - Works offline, lower quality
   
4. **gTTS** (Fallback)
   - Reliable but no voice selection
   - Always uses default female voice

#### Features
- User can select male or female voice
- Automatic fallback if preferred engine unavailable
- Audio preview before identification
- Download generated audio files
- **Endpoint:** `POST /api/tts/generate`

### 4. Community platform

**Social learning platform for Sanskrit enthusiasts!**

#### Features
- **Posts & Discussions:**
  - Create posts with Sanskrit verses, questions, insights
  - Image uploads (5MB max, PNG/JPG/GIF/WebP)
  - Like/unlike posts
  - Comment threads with nested replies
  - Share posts to social media
  
- **User Profiles:**
  - Custom avatars and bios
  - Sanskrit scholar badges
  - Activity tracking (posts, contributions)
  - Follow/unfollow users
  
- **Moderation:**
  - Admin panel for content moderation
  - Report inappropriate content
  - Ban/unban users
  - Delete posts/comments
  
- **Real-Time Notifications:**
  - WebSocket-based live updates
  - Notification bell with unread count
  - Activity feed
  
- **Search & Discovery:**
  - Search posts by keywords
  - Filter by user, date, popularity
  - Trending topics

**Endpoints:** 15+ endpoints under `/api/community/*`

### 5. Crowd-sourced contributions

**Enable the community to expand the database!**

#### Features
- **Submit New Verses:**
  - Users can submit verses with suggested meters
  - Admin review and approval workflow
  - Automatic validation against existing database
  
- **Submit Meter Definitions:**
  - Contribute new meter patterns
  - Include L-G patterns, syllable counts, matra counts
  - References to classical texts
  
- **Contribution History:**
  - View your submitted contributions
  - Track approval status
  - Contribution statistics and badges

**Endpoints:**
- `POST /api/contributions/submit` - Submit contribution
- `GET /api/contributions/my-contributions` - View your submissions
- `GET /api/contributions/approved` - Approved contributions shown in the dataset browser
- `GET /api/contributions/admin/pending` - Admin: pending review
- `POST /api/contributions/admin/approve/{id}`, `/admin/reject/{id}` - Admin: approve or reject

### 6. Authentication and authorization

**Secure user management with OAuth support**

#### Features
- **Username/Password Auth:**
  - Secure signup with bcrypt password hashing
  - JWT-based session management
  - Email verification (optional)
  
- **OAuth Providers:**
  - Google OAuth
  - GitHub OAuth
  - Seamless social login
  
- **Role-Based Access Control:**
  - User roles: `user`, `moderator`, `admin`
  - Protected routes with `@require_auth` decorator
  - Admin-only endpoints with `@require_admin`
  
- **Session Management:**
  - Refresh token support
  - Logout from all devices
  - Session expiry handling

**Endpoints:**
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/profile` - Get current user
- `POST /api/auth/admin-login` - Admin login
- `POST /api/auth/oauth/start`, `/oauth/exchange` - Google sign-in through Supabase; the client refreshes the Supabase session itself

### 7. Interactive L-G Lab

**Explore the mathematical beauty of Laghu-Guru patterns!**

#### Modules

1. **Breath Pattern Simulator**
   - Visualize L-G patterns as breathing rhythms
   - Interactive breath cycles matching meter patterns
   - Understanding natural rhythms in prosody

2. **Music & Tāla Mapper**
   - Map meters to Indian classical music tālas
   - Visualize rhythmic structures
   - Carnatic and Hindustani tāla correlations

3. **Fibonacci Visualizer**
   - Explore Pingala's binary numbers (Meru Prastara)
   - Visualize Pascal's Triangle in Sanskrit prosody
   - Fibonacci sequences in meter combinations

4. **Nature Pattern Comparison**
   - Compare L-G patterns with nature: heartbeat, waves, bird songs
   - Scientific connections between prosody and natural rhythms
   - Educational animations

5. **Combinatorics Calculator**
   - Calculate possible meter variations
   - Pingala's mathematical formulas
   - Binomial coefficients visualization

**Access:** `/lg-lab` page in frontend

### 8. Chandas game (separate app)

**Gamified learning platform for mastering meters!**

The game lives in a separate repository and is not part of this one; `GAME_INTEGRATION_SUMMARY.md` describes how it was wired in during the hackathon.
- Interactive lessons and quizzes
- Progress tracking and achievements
- Challenge modes
- Leaderboards
- Built with FastAPI backend + React frontend

### 9. Dataset management

**Comprehensive meter database with search and export**

#### Features
- View all meter definitions with pagination
- Search by name, L-G pattern, syllable count
- Filter by category (Sama, Vishama, Vedic, etc.)
- Export subsets as CSV/JSON
- Dataset statistics and analytics

**Endpoints:**
- `GET /api/datasets` - List all datasets
- `GET /api/datasets/{id}` - One dataset's entries, paged and filterable

### 10. Shloka validation and search

**AI-powered verse validation and scripture search**

#### Features
- **Shloka Checker:**
  - Validates if input is a proper Sanskrit verse
  - Detects prose, random text, mixed content
  - Uses Google Gemini for semantic validation
  - Confidence scoring
  
- **Scripture Search:**
  - Search verses in Bhagavad Gita, Ramayana, etc.
  - Semantic search with vector embeddings
  - Find similar verses
  - Context and commentary

**Endpoints:**
- `POST /api/sloka/validate` - Validate shloka
- `POST /api/sloka/search` - Search scriptures

---

## Technical architecture

### Backend stack

```python
# Core Technologies
Flask 2.2.2+              # Web framework
Flask-CORS                # Cross-origin support
Flask-SocketIO 5.3.0+     # Real-time WebSocket
Werkzeug 2.2.2+           # WSGI utilities

# AI & ML
google-genai 1.0.0+       # Gemini 2.0 Flash integration
langchain 0.1.0+          # RAG framework
langchain-google-genai    # Gemini embeddings
sentence-transformers     # Multilingual embeddings (768-dim)

# Authentication & Database
supabase 2.25.0           # Backend-as-a-Service
PyJWT 2.8.0+              # JWT tokens
bcrypt 4.0.1+             # Password hashing
Flask-Limiter 3.5.0       # Rate limiting

# OCR & Document Processing
pytesseract 0.3.9+        # Tesseract OCR wrapper
Pillow 9.0.0+             # Image processing
google-cloud-vision 3.0+  # Google Vision API
google-cloud-speech 2.0+  # Speech-to-Text
pdfplumber 0.10.0+        # PDF extraction
PyMuPDF 1.24.0+           # PDF rendering
python-docx 1.1.0+        # DOCX parsing

# Sanskrit Text Processing
indic_transliteration 2.3.10+  # Script conversion
sanskrit_text 0.2.1+            # Syllabification
python_Levenshtein 0.12.2+      # Fuzzy matching

# Text-to-Speech
edge-tts 7.2.3+           # Microsoft Bing TTS
gTTS 2.5.4+               # Google TTS
pyttsx3 2.99+             # Offline TTS

# Background Tasks
APScheduler 3.10.0        # Job scheduling
eventlet 0.35.0           # Async I/O
```

### Frontend stack

```json
// Core Framework
"react": "^18.3.1"
"react-dom": "^18.3.1"
"react-router-dom": "^6.x"
"typescript": "^5.x"
"vite": "^6.x"

// UI Components
"@radix-ui/*": "^1.x"     // 20+ primitive components
"shadcn/ui"               // Pre-built component library
"framer-motion": "^12.x"  // Animations
"lucide-react": "^0.487"  // Icons

// State Management & API
"axios": "^1.13.2"        // HTTP client
"@supabase/supabase-js"   // Supabase client
"socket.io-client"        // WebSocket client

// AI Integration
"@google/generative-ai"   // Gemini SDK
"ai": "^5.0.107"          // Vercel AI SDK
"@assistant-ui/react"     // Chatbot UI components

// Utilities
"clsx": "^2.1.1"          // Conditional classes
"tailwindcss"             // Utility-first CSS
"class-variance-authority" // Component variants
```

### Database schema (Supabase PostgreSQL)

```sql
-- Users table
users (
  id UUID PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE,
  role TEXT DEFAULT 'user',
  avatar_url TEXT,
  bio TEXT,
  created_at TIMESTAMP
)

-- Community posts
community_posts (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  content TEXT NOT NULL,
  image_url TEXT,
  likes INTEGER DEFAULT 0,
  created_at TIMESTAMP
)

-- Comments
community_comments (
  id UUID PRIMARY KEY,
  post_id UUID REFERENCES community_posts(id),
  user_id UUID REFERENCES users(id),
  content TEXT NOT NULL,
  created_at TIMESTAMP
)

-- Contributions
contributions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  contribution_type TEXT,
  data JSONB,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP
)

-- User profiles
user_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  full_name TEXT,
  bio TEXT,
  avatar_url TEXT,
  scholar_badge BOOLEAN,
  contribution_count INTEGER DEFAULT 0
)
```

### Vector database (ChromaDB)

```python
# RAG System - 2,844 Documents
Collections:
  - chandas_meters      # 1,887 meter definitions
    └─ Embedding model: paraphrase-multilingual-mpnet-base-v2
    └─ Dimensions: 768
    └─ Distance: Cosine similarity
  
  - chandas_docs        # 957 documentation chunks
    └─ Sources: Chandovallari, Pingala's Chandas Shastra
    └─ Chunk size: 512 tokens
    └─ Overlap: 50 tokens

# Retrieval Parameters
top_k: 5 documents
min_relevance_score: 0.6
max_context_length: 3,000 characters
```

## Accuracy evaluation

The harnesses in `backend/evaluation/` run the engine over real corpora.
These are the figures from running them on the current code.

```bash
uv run python -m backend.evaluation.csv_accuracy --all
```

| Measure on the 147-verse benchmark | Result |
|---|---|
| First line identified correctly | 146 of 147 (99.3%) |
| Every line of the verse correct | 134 of 147 (91.2%) |
| Individual lines | 485 of 499 (97.2%) |
| Whole-verse identification | 139 of 147 (94.6%) |

```bash
uv run python -m backend.evaluation.rigveda_validation
```

| Measure on the 9,247 labelled Rigveda riks | Result |
|---|---|
| Exact meter in Vedic mode | 8,067 (87.2%) |
| Exact meter, a family member or a part of a compound meter | 9,009 (97.4%) |

`backend/tests/test_corpus_accuracy.py` asserts these counts as floors, including 94.6% whole-verse accuracy, and the Data quality CI job runs it with `uv run pytest -m corpus`.
Both harnesses exit 1 below the same floors, which live in `backend/pipeline/benchmarks.py`.

`backend/tests/test_regression_verses.py` holds a small regression set: the Gāyatrī mantra, three Gita verses and two fragments.
Its Jagatī case still fails and is marked as an expected failure.

### Meter coverage

```
Total Meters: 1,920+

By Category:
├─ Sama (uniform):        1,629 meters
├─ Vishama (varied):         71 meters
├─ Vedic:                    28 meters
├─ Ardhasama:             Various
├─ Mātrā-based:               9 validated
└─ Jāti-based:             Multiple
```

The other harnesses cover the Rigveda, Rāmāyaṇa, WSC 2023 and Meghadūta sets, and compare the engine with the IITK, ChatGPT-generated and ICU-based implementations in `reference/`.
`backend/evaluation/README.md` lists them.

---

## Documentation index

| Document | What it covers |
|---|---|
| [`frontend/README.md`](frontend/README.md) | The React client: configuration, layout, styling and tests |
| [`docs/data-pipeline.md`](docs/data-pipeline.md) | Where the meter tables and corpora come from, and the checks CI runs on them |
| [`backend/evaluation/README.md`](backend/evaluation/README.md) | The accuracy harnesses and how to run them |
| [`docs/chandas_rules.md`](docs/chandas_rules.md) | Prosody rules, L-G patterns and mātrā counting |
| [`docs/meter.md`](docs/meter.md) | Meter classes, families and pattern variants |
| [`docs/SIH_2025_SUBMISSION.md`](docs/SIH_2025_SUBMISSION.md) | The Smart India Hackathon 2025 submission, with the judges' checklist, demo script and comparison that used to sit in this README |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Development workflow, checks and commit format |

## Configuration

`backend/config/settings.py` reads every setting from the environment and loads the root `.env` when it exists, then `backend/.env` for older checkouts.
`.env.example` at the root lists every variable the backend reads, and `frontend/.env.example` lists the three the frontend reads.
`backend/tests/test_env_example.py` fails when the code reads a variable that neither file lists.
Nothing is required to run meter identification.

| Variable | Used for | Default |
|---|---|---|
| `SECRET_KEY` | signing local JWTs | a development-only value |
| `DEBUG`, `LOG_LEVEL`, `PORT` | Flask runtime | `false`, `INFO`, `5000` |
| `LOG_FORMAT` | `text`, or `json` for one JSON object per log line | `text` |
| `CORS_ORIGINS` | allowed origins for Socket.IO | `*` |
| `REDIS_URL`, `RATELIMIT_DEFAULT` | Flask-Limiter storage and default limit | `memory://`, `100 per hour` |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` | auth, community and contributions | unset, features answer 503 |
| `SUPABASE_DB_*`, `DB_PASSWORD` | direct Postgres access in `backend/scripts/` | unset |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | admin login | `admin-erase-sure`, login disabled |
| `AUTH_EMAIL_DOMAIN`, `FRONTEND_URL` | synthetic emails and OAuth redirects | `merucoders.app`, `http://localhost:8080` |
| `GEMINI_API_KEY_1` to `_6` | chatbot and AI validation, tried in order | unset, both disabled |
| `GOOGLE_APPLICATION_CREDENTIALS` | Cloud Vision OCR and Cloud TTS | `backend/secrets/gcp-credentials.json` |
| `HF_TOKEN` | Sanskrit TTS model in API mode | unset |
| `INDIC_ASR_URL` | voice transcription service | unset, voice input answers 503 |
| `SYLLABIZATION_METHOD` | `auto`, `icu` or `sanskrit_text` | `auto` |
| `CLEANUP_ENABLED`, `CLEANUP_INTERVAL_MINUTES`, `FILE_MAX_AGE_MINUTES` | upload cleanup job; the test suite sets `CLEANUP_ENABLED=false` | `true`, `60`, `60` |
| `VITE_API_URL` | frontend API base | `http://localhost:5000/api` on localhost |
| `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | Google sign-in in the browser | unset, sign-in disabled |

## Deployment

`scripts/deploy.sh backend|frontend|both` builds both images with Cloud Build and deploys them to Cloud Run.
It reads the project and region through `scripts/load_config.sh`, and writes `frontend/config.js` with the backend URL before the frontend build.
The backend image carries `backend/.env` and `backend/secrets/` when they exist on the deploying machine, because the script sets only `DEBUG`, `LOG_LEVEL` and `CORS_ORIGINS` on the service.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow, checks and commit format.

---

## License

This project is developed for Smart India Hackathon 2025.

**Copyright © 2025 Erase Sure Team**

---

## Acknowledgments

### Inspiration and foundation
- **Acharya Pingala** - For Chandas Shastra (500-200 BCE)
- **Halayudha** - For commentary on Pingala's work (10th century)
- **AICTE IKS Division** - For promoting Indian Knowledge Systems

### Technical references
- **GRETIL Corpus** - Sanskrit text repository
- **Sanskrit Heritage Site** - Linguistic resources

### Open source libraries
- Flask, React, Supabase - Core frameworks
- Google Generative AI - Gemini models
- LangChain - RAG framework
- Tesseract OCR - Text recognition
- And all other dependencies listed in requirements.txt

### Special thanks
- SIH 2025 organizing committee
- AICTE mentors and coordinators
- Sanskrit scholars who validated our work
- Open source community

---

## Team members

### Erase Sure Team

1. **Gautham Krishna** - Team Lead & Full Stack Developer
2. **Kishore B** - Backend Developer
3. **Hiruthik Sudhakar** - Frontend Developer  
4. **Harevasu** - AI/ML Engineer
5. **Sreevalsan** - Database & DevOps
6. **Krithika** - UI/UX Designer
