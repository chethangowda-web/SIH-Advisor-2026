# ⚡ SIH AI Advisor
> AI-powered Smart India Hackathon project advisor — Analyze 35+ winning projects, generate novel ideas, and build professional blueprints.

---

## 🚀 Setup & Execution Guide

### Step 1 — Navigate to the backend directory
```bash
cd sih-ai-advisor/backend
```

### Step 2 — Create virtual environment
```bash
python -m venv venv
```

### Step 3 — Activate environment
- **Windows (PowerShell)**: `.\venv\Scripts\Activate.ps1`
- **Linux/macOS**: `source venv/bin/activate`

### Step 4 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 5 — Build vector database index
```bash
python data_pipeline.py
```

### Step 6 — Start API server
```bash
python main.py
```
> Server runs at: http://localhost:8000  
> API Documentation: http://localhost:8000/docs

---

## 📁 Repository Structure

```
sih-ai-advisor/
├── backend/
│   ├── main.py              ← FastAPI REST API server
│   ├── agents.py            ← LangChain & ChromaDB RAG agents
│   ├── chains.py            ← Proposal blueprint generator chain
│   ├── data_pipeline.py     ← Vector embedding & indexing script
│   ├── config.py            ← Environment configuration
│   ├── requirements.txt     ← Python package dependencies
│   └── data/
│       └── sih_winners.json ← Historical dataset of winning projects
└── frontend/
    ├── index.html           ← Single Page Application UI
    ├── styles.css           ← Kinetic high-contrast design system
    └── app.js               ← Client-side application logic & API integration
```

---

## 🛠️ Tech Stack & Architecture

- **AI & RAG**: LangChain · ChromaDB · Sentence-Transformers (`all-MiniLM-L6-v2`) · Groq API (Llama 3.3 70B)
- **Backend**: Python 3.11 · FastAPI · Uvicorn · Gunicorn
- **Frontend**: Vanilla JS · HTML5 Canvas · CSS3 Kinetic Design System · Chart.js
- **Deployment**: Render (Backend API) · Vercel (Frontend Application)
