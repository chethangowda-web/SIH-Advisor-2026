"""
agents.py
LangChain AI agents powered by Groq LLM + ChromaDB RAG.
Handles: Trend Analysis, Gap Finding, Idea Generation, Blueprint Creation.
"""

import asyncio
import json
import random
import time
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import config

# ─────────────────────────── Pydantic Schemas ───────────────────────────────

class ProjectIdea(BaseModel):
    title: str = Field(description="Catchy project title")
    tagline: str = Field(description="One-line description")
    problem_statement: str = Field(description="Detailed problem it solves")
    solution: str = Field(description="Detailed solution description")
    domain: str = Field(description="SIH domain category")
    technologies: list[str] = Field(description="List of tech stack")
    novelty_score: int = Field(description="Originality score 1-10")
    feasibility_score: int = Field(description="1-month feasibility score 1-10")
    impact_score: int = Field(description="Social impact score 1-10")
    novelty_reason: str = Field(description="Why this is novel/not done before")
    similar_past_projects: list[str] = Field(description="IDs of similar past SIH projects")
    target_beneficiaries: str = Field(description="Who benefits and how many")
    ministry_fit: str = Field(description="Best ministry/department for this PS")

class TrendAnalysis(BaseModel):
    top_domains: list[dict] = Field(description="Top domains with win counts")
    rising_technologies: list[str] = Field(description="Technologies gaining popularity")
    dominant_problem_types: list[str] = Field(description="Most common problem types")
    hardware_vs_software_ratio: str = Field(description="Hardware vs software ratio")
    key_insights: list[str] = Field(description="Key trends observed")
    predicted_hot_domains_2025: list[str] = Field(description="Predicted hot domains for 2025")

# ─────────────────────────── Singleton Loader ────────────────────────────────

class LLMQuotaError(RuntimeError):
    """Raised when the LLM provider's usage limit (daily token quota, etc.) is hit."""

_llms: dict = {}

def get_llm(max_tokens: Optional[int] = None) -> ChatGroq:
    """Return a cached ChatGroq instance. Different max_tokens values get their own
    instance so we can cap token burn per endpoint (chat is small, blueprints big)."""
    global _llms
    mt = max_tokens if max_tokens else 4096
    if mt not in _llms:
        _llms[mt] = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.GROQ_MODEL,
            temperature=0.7,
            max_tokens=mt,
        )
    return _llms[mt]

# ─────────────────────────── Resilient LLM Invoker ───────────────────────────

def _is_rate_limit(exc: Exception) -> bool:
    """True when the error is a Groq/OpenAI rate-limit or quota exhaustion."""
    sc = getattr(exc, "status_code", None)
    if sc is not None and str(sc) == "429":
        return True
    text = str(exc)
    for marker in ("429", "rate_limit", "Rate limit", "tokens per day", "TPD", "quota"):
        if marker in text:
            return True
    return False

async def _invoke_with_retry(call, *args, attempts: int = 3, base_delay: float = 1.0, **kwargs):
    """Invoke an LLM call (e.g. chain.ainvoke) with exponential backoff so transient
    Groq failures (5xx, brief timeouts) don't surface as hard errors.

    Rate-limit / quota errors are raised immediately with a clear message — retrying
    them only burns the daily token budget faster."""
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to backend/.env and restart.")
    last_err = None
    for i in range(attempts):
        try:
            return await call(*args, **kwargs)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            last_err = e
            if _is_rate_limit(e):
                raise LLMQuotaError(
                    "The AI service's usage limit was reached. Please try again later."
                ) from e
            delay = base_delay * (2 ** i) + random.random()
            await asyncio.sleep(delay)
    raise last_err


# ----------------------------------------------------------------

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_tfidf_vectorizer = None
_tfidf_matrix = None
_documents_list = []
_metadatas_list = []

def get_all_projects_data():
    global _documents_list, _metadatas_list, _tfidf_vectorizer, _tfidf_matrix
    if not _documents_list:
        with open(config.DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for project in data:
            doc_text = f"Title: {project['title']} | Year: {project['year']} | Domain: {project['domain']} | Problem: {project['problem_statement']} | Solution: {project['solution']} | Tech: {', '.join(project['technologies'])}"
            _documents_list.append(doc_text)
            _metadatas_list.append({
                "id": project["id"],
                "year": project["year"],
                "title": project["title"],
                "domain": project["domain"]
            })
        _tfidf_vectorizer = TfidfVectorizer().fit(_documents_list)
        _tfidf_matrix = _tfidf_vectorizer.transform(_documents_list)
    return _documents_list, _metadatas_list, _tfidf_vectorizer, _tfidf_matrix

def retrieve_similar_projects(query: str, n_results: int = 6) -> list[dict]:
    """Lightweight TF-IDF similarity search (0MB PyTorch RAM)."""
    docs, metas, vectorizer, matrix = get_all_projects_data()
    query_vec = vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, matrix)[0]
    
    top_indices = similarities.argsort()[-n_results:][::-1]
    
    projects = []
    for idx in top_indices:
        projects.append({
            "document": docs[idx],
            "metadata": metas[idx],
            "similarity": float(similarities[idx])
        })
    return projects

def get_all_projects_summary() -> str:
    """Get a compact summary of projects for trend analysis. Kept short to limit
    LLM input tokens (and therefore daily Groq quota burn)."""
    with open(config.DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    summaries = []
    for p in data[:28]:
        summaries.append(
            f"{p['year']} | {p['domain']} | {p['title']} | "
            f"Tech: {', '.join(p['technologies'][:3])}"
        )
    return "\n".join(summaries)

# ─────────────────────────── Agent: Trend Analyzer ───────────────────────────

TRENDS_TTL_SECONDS = 6 * 60 * 60  # cache successful trend analysis for 6 hours
_trends_cache: dict = {"ts": 0.0, "data": None}

def _trends_fallback() -> dict:
    """Deterministic trend report computed from the dataset. Used when the LLM is
    unavailable so the Trends page always renders instead of showing an error."""
    stats = get_statistics()
    total = stats["total_projects"]
    breakdown = stats["domain_breakdown"]

    top_domains = []
    for domain, count in sorted(breakdown.items(), key=lambda x: x[1], reverse=True)[:8]:
        top_domains.append({
            "domain": domain,
            "win_count": count,
            "percentage": round((count / total) * 100) if total else 0,
            "key_themes": [],
        })

    techs = [t["tech"] for t in stats["top_technologies"][:6]]
    year_breakdown = stats["year_breakdown"]

    return {
        "top_domains": top_domains,
        "rising_technologies": techs,
        "dominant_problem_types": ["AI-driven automation", "Data accessibility", "Last-mile delivery"],
        "hardware_vs_software_ratio": f"{stats['hardware_projects']} hardware, {stats['software_projects']} software",
        "key_insights": [
            f"Analyzing {total} SIH winning projects across {stats['domains_count']} domains.",
            f"Most active domain: {top_domains[0]['domain'] if top_domains else 'N/A'} ({top_domains[0]['win_count'] if top_domains else 0} wins).",
            f"Top technologies used by winners: {', '.join(techs) if techs else 'N/A'}.",
            "AI/ML, IoT and GenAI continue to dominate winning submissions.",
        ],
        "predicted_hot_domains_2025": [d["domain"] for d in top_domains[:4]],
    }

async def _analyze_trends_llm() -> dict:
    llm = get_llm(max_tokens=1500)
    all_projects = get_all_projects_summary()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert analyst of Smart India Hackathon (SIH) trends.
        Analyze the provided list of winning projects and extract key trends.
        Return a valid JSON object matching the schema exactly. No markdown, no extra text."""),
        ("human", """Analyze these SIH winning projects from 2017-2024:

{projects}

Return a JSON with these exact keys:
{{
  "top_domains": [
    {{"domain": "Healthcare", "win_count": 8, "percentage": 22, "key_themes": ["telemedicine", "AI diagnosis"]}},
    ...
  ],
  "rising_technologies": ["LangChain", "RAG", "Edge AI", ...],
  "dominant_problem_types": ["Rural Access", "Governance Transparency", ...],
  "hardware_vs_software_ratio": "30% hardware, 70% software",
  "key_insights": ["insight1", "insight2", ...],
  "predicted_hot_domains_2025": ["domain1", "domain2", ...]
}}""")
    ])

    chain = prompt | llm | StrOutputParser()
    response = await _invoke_with_retry(chain.ainvoke, {"projects": all_projects})

    # Parse JSON from response
    clean = response.strip().strip("```json").strip("```").strip()
    return json.loads(clean)

async def analyze_trends() -> dict:
    """Trend analysis computed deterministically from the dataset (no LLM call).

    This keeps the Trends page instant, always available, and free of the Groq
    token budget — it can never fail, time out, or show an error to users."""
    now = time.time()
    if _trends_cache["data"] is not None and (now - _trends_cache["ts"]) < TRENDS_TTL_SECONDS:
        return _trends_cache["data"]
    data = _trends_fallback()
    _trends_cache["ts"] = now
    _trends_cache["data"] = data
    return data

# ─────────────────────────── Agent: Gap Finder ───────────────────────────────

async def find_gaps(domain: str = "all") -> list[dict]:
    """Find unsolved problem spaces in SIH history."""
    llm = get_llm(max_tokens=2000)
    
    all_projects = get_all_projects_summary()
    
    domain_filter = f"Focus on the {domain} domain." if domain != "all" else "Cover all domains."
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert at identifying unsolved problems and innovation gaps
        in the Smart India Hackathon ecosystem. You understand both technical feasibility
        and social impact in the Indian context."""),
        ("human", """Based on these SIH winning projects (2017-2024):

{projects}

{domain_filter}

Identify 5 significant UNSOLVED PROBLEM GAPS that:
1. Have NOT been addressed in any past SIH project
2. Are urgent real-world Indian problems
3. Are technically solvable by a 6-person student team in 1 month
4. Have massive social impact potential

Return a JSON array:
[
  {{
    "gap_title": "Title of the gap",
    "problem": "Detailed description of unsolved problem",
    "why_unsolved": "Why hasn't this been solved yet",
    "potential_solution_direction": "High-level approach",
    "domain": "Domain category",
    "urgency": "High/Medium/Low",
    "beneficiaries": "Who would benefit",
    "estimated_impact": "Quantified potential impact"
  }},
  ...
]""")
    ])
    
    chain = prompt | llm | StrOutputParser()
    response = await _invoke_with_retry(chain.ainvoke, {
        "projects": all_projects,
        "domain_filter": domain_filter
    })
    
    try:
        clean = response.strip().strip("```json").strip("```").strip()
        # Find JSON array
        start = clean.find("[")
        end = clean.rfind("]") + 1
        return json.loads(clean[start:end])
    except Exception:
        return [{"error": "Could not parse gaps", "raw": response}]

# ─────────────────────────── Agent: Idea Generator ───────────────────────────

async def generate_ideas(
    domain: str,
    theme: str = "",
    num_ideas: int = 3
) -> list[dict]:
    """Generate novel SIH project ideas with novelty and feasibility scoring."""
    llm = get_llm(max_tokens=3500)
    
    # RAG: retrieve similar past projects
    query = f"{domain} {theme} India problem solution"
    similar = retrieve_similar_projects(query, n_results=6)
    
    context = "\n\n".join([
        f"Past Project: {p['metadata']['title']} ({p['metadata']['year']})\n"
        f"Domain: {p['metadata']['domain']}\n"
        f"Summary: {p['document'][:300]}..."
        for p in similar
    ])
    
    past_ids = [p["metadata"]["id"] for p in similar]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert SIH project advisor with deep knowledge of:
        - Indian social problems and government priorities
        - Emerging technologies (AI/ML, IoT, Blockchain, GenAI)
        - What makes winning SIH projects (novelty + feasibility + impact)
        - Student team capabilities (6 people, 1-month development)
        
        Generate TRULY NOVEL ideas that haven't been done before in SIH.
        Each idea must solve a REAL, URGENT Indian problem.
        Return ONLY valid JSON, no markdown or extra text."""),
        ("human", """Generate {num_ideas} novel SIH project ideas for domain: {domain}
        {theme_instruction}
        
        PAST SIH PROJECTS (for context & to AVOID duplication):
        {context}
        
        Each idea MUST:
        - Be genuinely novel (not a copy of past projects)
        - Solve a real Indian problem
        - Be buildable by 6 students in 1 month
        - Use modern tech (AI/ML, IoT, Blockchain, GenAI)
        
        Return a JSON array of {num_ideas} ideas:
        [
          {{
            "title": "Catchy project title",
            "tagline": "One-line description",
            "problem_statement": "Detailed problem (2-3 sentences)",
            "solution": "Detailed solution (3-4 sentences)",
            "domain": "{domain}",
            "technologies": ["tech1", "tech2", "tech3", "tech4", "tech5"],
            "novelty_score": 8,
            "feasibility_score": 7,
            "impact_score": 9,
            "novelty_reason": "Why this hasn't been done before",
            "similar_past_projects": ["project-id1"],
            "target_beneficiaries": "Who benefits and estimated number",
            "ministry_fit": "Ministry of XYZ",
            "sih_problem_statement_type": "Software/Hardware"
          }}
        ]""")
    ])
    
    theme_instruction = f"Theme/Focus: {theme}" if theme else ""
    
    chain = prompt | llm | StrOutputParser()
    response = await _invoke_with_retry(chain.ainvoke, {
        "num_ideas": num_ideas,
        "domain": domain,
        "theme_instruction": theme_instruction,
        "context": context
    })
    
    try:
        clean = response.strip().strip("```json").strip("```").strip()
        start = clean.find("[")
        end = clean.rfind("]") + 1
        ideas = json.loads(clean[start:end])
        return ideas
    except Exception:
        return [{"error": "Could not parse ideas", "raw": response[:500]}]

# ─────────────────────────── Agent: Chat ─────────────────────────────────────

async def chat_with_advisor(message: str, history: list[dict]) -> str:
    """Chat with the SIH advisor using RAG context."""
    llm = get_llm(max_tokens=1000)
    
    # Retrieve relevant projects
    similar = retrieve_similar_projects(message, n_results=4)
    context = "\n".join([
        f"- {p['metadata']['title']} ({p['metadata']['year']}): {p['document'][:200]}..."
        for p in similar
    ])
    
    # Build message history
    messages = [
        ("system", f"""You are an expert SIH (Smart India Hackathon) advisor helping students 
        build winning projects. You have deep knowledge of:
        - All SIH winning projects from 2017-2024
        - Indian government priorities and ministries  
        - Modern tech stacks suitable for student teams
        - What judges look for: novelty, impact, feasibility
        
        Relevant past projects for context:
        {context}
        
        Be encouraging, specific, and give actionable advice.""")
    ]
    
    # Add history
    for msg in history[-6:]:  # Last 3 exchanges
        messages.append((msg["role"], msg["content"]))
    
    messages.append(("human", message))
    
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm | StrOutputParser()
    try:
        response = await _invoke_with_retry(chain.ainvoke, {})
        return response
    except LLMQuotaError:
        return ("I've hit my AI service's usage limit for the moment — it resets "
                "automatically in a little while. Please try again soon; I'll be "
                "ready to help with SIH ideas then. 🙂")
    except Exception:
        return ("I'm having trouble reaching the AI service right now. "
                "Please try again in a moment.")

# ─────────────────────────── Statistics ──────────────────────────────────────

def get_statistics() -> dict:
    """Get overall dataset statistics."""
    with open(config.DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    domains = {}
    years = {}
    techs = {}
    
    for p in data:
        # Count domains
        d = p["domain"]
        domains[d] = domains.get(d, 0) + 1
        
        # Count years
        y = p["year"]
        years[y] = years.get(y, 0) + 1
        
        # Count technologies
        for t in p["technologies"]:
            techs[t] = techs.get(t, 0) + 1
    
    top_techs = sorted(techs.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_projects": len(data),
        "years_covered": f"2017-2024",
        "domains_count": len(domains),
        "domain_breakdown": domains,
        "year_breakdown": dict(sorted(years.items())),
        "top_technologies": [{"tech": t, "count": c} for t, c in top_techs],
        "hardware_projects": sum(1 for p in data if p.get("is_hardware")),
        "software_projects": sum(1 for p in data if not p.get("is_hardware")),
    }
