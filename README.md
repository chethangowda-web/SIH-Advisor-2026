# ⚡ SIH AI Advisor
> AI-powered Smart India Hackathon project advisor — Analyze 35+ winning projects, generate novel ideas, and build professional blueprints.

---

## 🚀 Setup (Do This Once)

### Step 1 — Open PowerShell in the `backend` folder
```powershell
cd C:\Users\LENOVO\.gemini\antigravity\scratch\sih-ai-advisor\backend
```

### Step 2 — Create virtual environment
```powershell
python -m venv venv
```

### Step 3 — Activate it
```powershell
.\venv\Scripts\Activate.ps1
```
> If you get an error, run this first: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Step 4 — Install all packages
```powershell
pip install -r requirements.txt
```
> ⏳ This takes 5-10 minutes (downloads PyTorch, transformers etc.)

### Step 5 — Build the AI database (run ONCE)
```powershell
python data_pipeline.py
```
> This embeds all SIH projects into ChromaDB. Takes ~2 minutes.

### Step 6 — Start the server
```powershell
python main.py
```
> Server runs at: http://localhost:8000
> API docs at:    http://localhost:8000/docs

---

## 🖥️ Open the Frontend

Just open this file in your browser:
```
C:\Users\LENOVO\.gemini\antigravity\scratch\sih-ai-advisor\frontend\index.html
```

**OR** use VS Code Live Server (recommended) for best experience.

---

## 📁 Project Structure

```
sih-ai-advisor/
├── backend/
│   ├── main.py              ← FastAPI server
│   ├── agents.py            ← AI agents (Groq LLM + ChromaDB RAG)
│   ├── chains.py            ← Blueprint generator chain
│   ├── data_pipeline.py     ← Embed SIH data into ChromaDB
│   ├── config.py            ← Settings
│   ├── .env                 ← Your API keys (don't share!)
│   ├── requirements.txt     ← Python packages
│   ├── setup.bat            ← One-click setup for Windows
│   └── data/
│       └── sih_winners.json ← 35+ SIH projects (2017-2024)
└── frontend/
    ├── index.html           ← Main SPA
    ├── styles.css           ← Beautiful dark theme
    └── app.js               ← All JavaScript logic
```

---

## 🔥 Features

| Feature | Description |
|---------|-------------|
| 📊 Dashboard | Stats, domains, quick actions |
| 📈 Trend Analysis | AI analyzes winning patterns using Groq LLM |
| 💡 Idea Generator | Novel ideas by domain with novelty/feasibility/impact scores |
| 📋 Blueprint Builder | Full professional project proposal (8 sections) |
| 🤖 AI Chat | Ask anything about SIH strategy and winning tips |

---

## 🛠️ Tech Stack

**Backend**: Python · FastAPI · LangChain · Groq (Llama 3.3 70B) · ChromaDB · Sentence Transformers  
**Frontend**: Vanilla HTML/CSS/JS · Chart.js

---

## ⚡ Quick Tip
After `python main.py` starts, the status dot in the sidebar turns **green** ✅.  
All features become available immediately!
