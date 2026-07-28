"""
agents.py
LangChain AI agents powered by Groq LLM + ChromaDB RAG.
Handles: Trend Analysis, Gap Finding, Idea Generation, Blueprint Creation.
"""

import json
import chromadb
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from sentence_transformers import SentenceTransformer
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

_llm: Optional[ChatGroq] = None
_embedding_model: Optional[SentenceTransformer] = None
_chroma_collection = None

def get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            api_key=config.GROQ_API_KEY,
            model=config.GROQ_MODEL,
            temperature=0.7,
            max_tokens=4096,
        )
    return _llm

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
    """Get a summary of all projects for trend analysis."""
    with open(config.DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    summaries = []
    for p in data:
        summaries.append(
            f"[{p['id']}] {p['year']} | {p['domain']} | {p['title']} | "
            f"Tech: {', '.join(p['technologies'][:3])} | "
            f"Impact: {p['impact'][:80]}"
        )
    return "\n".join(summaries)

# ─────────────────────────── Agent: Trend Analyzer ───────────────────────────

async def analyze_trends() -> dict:
    """Analyze trends across all SIH winning projects."""
    llm = get_llm()
    
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
    response = await chain.ainvoke({"projects": all_projects})
    
    # Parse JSON from response
    try:
        # Clean response in case of markdown
        clean = response.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except Exception:
        return {"error": "Could not parse trend analysis", "raw": response}

# ─────────────────────────── Agent: Gap Finder ───────────────────────────────

async def find_gaps(domain: str = "all") -> list[dict]:
    """Find unsolved problem spaces in SIH history."""
    llm = get_llm()
    
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
    response = await chain.ainvoke({
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
    llm = get_llm()
    
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
    response = await chain.ainvoke({
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
    llm = get_llm()
    
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
    response = await chain.ainvoke({})
    return response

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
