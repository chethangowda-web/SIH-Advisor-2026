"""
main.py
FastAPI server — all API endpoints for the SIH AI Advisor.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import agents
import chains

app = FastAPI(
    title="SIH AI Advisor API",
    description="AI-powered Smart India Hackathon project advisor",
    version="1.0.0"
)

# ─── CORS (allow frontend to call this API) ───────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request/Response Models ──────────────────────────────────────────────────

class IdeaRequest(BaseModel):
    domain: str
    theme: Optional[str] = ""
    num_ideas: int = 3

class BlueprintRequest(BaseModel):
    title: str
    problem_statement: str
    solution: str
    domain: str
    technologies: list[str]
    team_size: int = 6
    duration_weeks: int = 4

class ChatMessage(BaseModel):
    message: str
    history: Optional[list[dict]] = []

class GapRequest(BaseModel):
    domain: Optional[str] = "all"

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "🚀 SIH AI Advisor API is running!",
        "docs": "/docs",
        "endpoints": [
            "GET  /api/stats",
            "GET  /api/domains",
            "GET  /api/trends",
            "POST /api/generate-ideas",
            "POST /api/blueprint",
            "POST /api/find-gaps",
            "POST /api/chat",
        ]
    }

@app.get("/api/stats")
def get_stats():
    """Overall SIH dataset statistics."""
    try:
        return agents.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/domains")
def get_domains():
    """List all available SIH domains."""
    return {
        "domains": [
            "Agriculture",
            "Healthcare",
            "Education",
            "Governance",
            "Clean Technology",
            "Smart Cities",
            "Disaster Management",
            "Transportation",
            "Finance",
            "Cybersecurity",
            "Environment",
            "Smart Automation",
            "Security",
            "Heritage & Culture",
        ]
    }

@app.get("/api/trends")
async def get_trends():
    """AI-powered trend analysis of SIH winning projects."""
    try:
        trends = await agents.analyze_trends()
        return {"success": True, "data": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-ideas")
async def generate_ideas(request: IdeaRequest):
    """Generate novel SIH project ideas for a given domain."""
    try:
        if request.num_ideas < 1 or request.num_ideas > 5:
            raise HTTPException(status_code=400, detail="num_ideas must be 1-5")
        
        ideas = await agents.generate_ideas(
            domain=request.domain,
            theme=request.theme,
            num_ideas=request.num_ideas
        )
        return {"success": True, "domain": request.domain, "ideas": ideas}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/blueprint")
async def create_blueprint(request: BlueprintRequest):
    """Generate a full professional SIH project blueprint."""
    try:
        blueprint = await chains.generate_blueprint(
            title=request.title,
            problem_statement=request.problem_statement,
            solution=request.solution,
            domain=request.domain,
            technologies=request.technologies,
            team_size=request.team_size,
            duration_weeks=request.duration_weeks
        )
        return {"success": True, "blueprint": blueprint}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/find-gaps")
async def find_gaps(request: GapRequest):
    """Find unsolved problem gaps in SIH history."""
    try:
        gaps = await agents.find_gaps(domain=request.domain)
        return {"success": True, "domain": request.domain, "gaps": gaps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatMessage):
    """Chat with the SIH advisor AI."""
    try:
        response = await agents.chat_with_advisor(
            message=request.message,
            history=request.history
        )
        return {"success": True, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Server Entry Point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    # Check if ChromaDB exists, warn if not
    import config
    if not os.path.exists(config.CHROMA_DB_PATH):
        print("\n⚠️  WARNING: ChromaDB not found!")
        print("Run first: python data_pipeline.py\n")
    
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
