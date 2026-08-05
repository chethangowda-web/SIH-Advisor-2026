# SIH Aurora — AI Innovation Command Center

> AI-powered Smart India Hackathon advisor: analyze 35+ winning projects, generate novel, non-redundant ideas, and build professional blueprints.

**SIH Aurora** is a full-stack RAG application that helps SIH teams win. It indexes years of Smart India Hackathon winners into a vector database, then lets you explore trends, synthesize original proposals, and generate production-ready blueprint documents.

**Live demo** → [sih-advisor-2026-production.up.railway.app](https://sih-advisor-2026-production.up.railway.app) · API docs at `/docs`

---

## Features

- **Trend Analysis** — domain distribution, year trajectory, and rising-technologies insights from the indexed winner archive.
- **Idea Synthesizer** — RAG novelty filter + Groq Llama-3.3 generation for zero-redundancy, original concepts.
- **Blueprint Builder** — full technical specification documents: architecture, timeline, budget, risk, demo plan, and judge "wow" moments.
- **AI Mentor** — conversational Q&A against historical benchmarks and tech-stack optimization.
- **Aurora UI** — immersive command-center design: animated aurora background, glassmorphic gradient-border cards, particle field, boot splash, and 3D tilt micro-interactions.

---

## Quick Start

The fastest path on Windows is the one-command bootstrapper:

```bash
cd backend
setup.bat
```

This creates a virtual environment, installs dependencies, builds the vector database, and starts the API server.

### Manual setup

```bash
# 1. Backend
cd backend
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Linux/macOS
source venv/bin/activate

# 2. Configure the Groq API key
#    copy backend/.env.example -> backend/.env and fill in GROQ_API_KEY

# 3. Install dependencies
pip install -r requirements.txt

# 4. Build the vector database index (first run only)
python data_pipeline.py

# 5. Start the API server
python main.py

# 6. Frontend (in another terminal)
cd ../frontend
python -m http.server 8080
```

- API server: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs
- Frontend: http://localhost:8080

---

## Repository Structure

```
SIH-Advisor-2026/
├── backend/
│   ├── main.py              # FastAPI REST API server
│   ├── agents.py            # LangChain & ChromaDB RAG agents
│   ├── chains.py            # Proposal blueprint generator chain
│   ├── data_pipeline.py     # Vector embedding & indexing script
│   ├── config.py            # Environment configuration
│   ├── requirements.txt     # Python package dependencies
│   ├── setup.bat            # One-click Windows setup + start
│   ├── render.yaml          # Render deployment manifest
│   └── data/
│       └── sih_winners.json # Historical dataset of winning projects
└── frontend/
    ├── index.html           # Single-page application UI
    ├── styles.css           # Aurora design system
    ├── app.js               # App logic & API integration
    └── fx.js                # Ambient effects (particles, tilt, splash)
```

---

## Configuration Variables

Create `backend/.env` based on `.env.example`:

| Variable        | Description                        | Default                 |
| --------------- | ---------------------------------- | ----------------------- |
| `GROQ_API_KEY`  | Groq API key (required)            | —                       |
| `GROQ_MODEL`    | Groq LLM model                     | `llama-3.3-70b-versatile` |
| `EMBEDDING_MODEL`| Sentence-transformers model       | `all-MiniLM-L6-v2`      |
| `CHROMA_DB_PATH`| ChromaDB persistence directory     | `./chroma_db`           |
| `DATA_PATH`     | Historical winners JSON path        | `./data/sih_winners.json` |
| `PORT`          | Server port                         | `8000`                  |

Note: `.env`, `chroma_db/`, and `venv/` are gitignored and never committed.

---

## API Endpoints

| Method | Endpoint            | Description                              |
| ------ | ------------------- | ---------------------------------------- |
| GET    | `/api/stats`        | Aggregate statistics & breakdowns        |
| GET    | `/api/domains`      | Domain listing                           |
| GET    | `/api/trends`       | Trend & insight analysis                 |
| POST   | `/api/generate-ideas` | Novel idea synthesis & validation      |
| POST   | `/api/blueprint`    | Blueprint specification generation       |
| POST   | `/api/find-gaps`    | Uncovered problem-space detection        |
| POST   | `/api/chat`         | Conversational AI assistant              |

---

## Tech Stack

- **AI & RAG** — LangChain · ChromaDB · Sentence-Transformers (`all-MiniLM-L6-v2`) · Groq (Llama 3.3 70B)
- **Backend** — Python 3.11 · FastAPI · Uvicorn · Gunicorn
- **Frontend** — Vanilla JS · HTML5 Canvas · CSS3 · Chart.js
- **Deployment** — Docker-ready FastAPI + static frontend (Render / Railway)

---

## License

[MIT](LICENSE)