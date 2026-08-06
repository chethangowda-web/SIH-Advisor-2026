"""
agents.py
LangChain AI agents powered by OpenRouter LLM + ChromaDB RAG.
Handles: Trend Analysis, Gap Finding, Idea Generation, Blueprint Creation.
"""

import asyncio
import json
import random
import re
import time
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from typing import Optional
import config

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

class LLMQuotaError(RuntimeError):
    """Raised when the LLM provider's usage limit (daily token quota, etc.) is hit."""

_llms: dict = {}

def get_llm(max_tokens: Optional[int] = None, model: Optional[str] = None) -> ChatOpenAI:
    global _llms
    mt = max_tokens if max_tokens else 4096
    if model is None:
        m = (
            config.FEATHERLESS_MODEL
            if config.LLM_PROVIDER == "featherless"
            else config.OPENROUTER_MODEL
        )
    else:
        m = model
    key = (m, mt)
    if key not in _llms:
        if config.LLM_PROVIDER == "featherless":
            api_key, base_url = config.FEATHERLESS_API_KEY, config.FEATHERLESS_BASE_URL
        else:
            api_key, base_url = config.OPENROUTER_API_KEY, config.OPENROUTER_BASE_URL
        kwargs = dict(
            api_key=api_key,
            base_url=base_url,
            model=m,
            temperature=0.7,
            max_tokens=mt,
            timeout=120.0,       # bound each provider call so nothing hangs forever
            max_retries=2,       # retry transient network / 5xx / 429 errors
        )
        # qwen3 models default to a thinking/reasoning mode that can occasionally
        # emit only a reasoning block with an empty final answer, which makes
        # OpenRouter fail JSON validation ("json_validate_failed"). Disable it so
        # the model always returns readable JSON. On Featherless the correct switch
        # is chat_template_kwargs.enable_thinking (big speed win: no "thinking" prelude).
        if m.lower().startswith("qwen"):
            if config.LLM_PROVIDER == "featherless":
                kwargs["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
            else:
                kwargs["extra_body"] = {"reasoning": {"enabled": False}}
        _llms[key] = ChatOpenAI(**kwargs)
    return _llms[key]

def _is_rate_limit(exc: Exception) -> bool:
    sc = getattr(exc, "status_code", None)
    if sc is not None and str(sc) == "429":
        return True
    text = str(exc)
    for marker in ("429", "rate_limit", "Rate limit", "tokens per day", "TPD", "quota"):
        if marker in text:
            return True
    return False

def _strip_reasoning(text: str) -> str:
    text = re.sub(r" thinking.*? response", "", text, flags=re.S)
    return text.strip()

def _extract_json(text: str):
    """Extract a JSON object or array from a model response."""
    text = _strip_reasoning(text or "")
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"```\s*$", "", text).strip()

    start_arr = text.find("[")
    start_obj = text.find("{")

    if start_obj == -1 and start_arr == -1:
        raise ValueError("No JSON found in response")

    if start_obj == -1:
        start = start_arr
        end = text.rfind("]") + 1
        if end <= start:
            raise ValueError("No valid JSON array found")
    elif start_arr == -1:
        start = start_obj
        end = text.rfind("}") + 1
        if end <= start:
            raise ValueError("No valid JSON object found")
    else:
        start = min(start_obj, start_arr)
        if start == start_obj:
            end = text.rfind("}") + 1
        else:
            end = text.rfind("]") + 1

    return json.loads(text[start:end])

def _as_list(data) -> list:
    """Coerce an extracted JSON payload into a list so consumers can always iterate it.
    Handles models that return a single object (wrap it) or wrap an array under a key."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("ideas", "gaps", "projects", "items", "results", "data"):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]
    return []

async def _invoke_with_retry(call, *args, attempts: int = 3, base_delay: float = 1.0, call_timeout: float = 150.0, **kwargs):
    if not config.OPENROUTER_API_KEY and not config.FEATHERLESS_API_KEY:
        raise RuntimeError(f"{config.LLM_PROVIDER.upper()} API key is not set. "
                           "Add it to backend/.env and restart.")
    last_err = None
    for i in range(attempts):
        try:
            return await asyncio.wait_for(call(*args, **kwargs), timeout=call_timeout)
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError as e:
            last_err = e
        except Exception as e:
            last_err = e
            if _is_rate_limit(e):
                raise LLMQuotaError(
                    "The AI service's usage limit was reached. Please try again later."
                ) from e
            delay = base_delay * (2 ** i) + random.random()
            await asyncio.sleep(delay)
    raise last_err

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

_summary_cache: Optional[str] = None

def get_all_projects_summary() -> str:
    global _summary_cache
    if _summary_cache is None:
        with open(config.DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        summaries = []
        for p in data[:28]:
            summaries.append(
                f"{p['year']} | {p['domain']} | {p['title']} | "
                f"Tech: {', '.join(p['technologies'][:3])}"
            )
        _summary_cache = "\n".join(summaries)
    return _summary_cache

TRENDS_TTL_SECONDS = 6 * 60 * 60
_trends_cache: dict = {"ts": 0.0, "data": None}

def _trends_fallback() -> dict:
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

async def analyze_trends() -> dict:
    now = time.time()
    if _trends_cache["data"] is not None and (now - _trends_cache["ts"]) < TRENDS_TTL_SECONDS:
        return _trends_cache["data"]
    data = _trends_fallback()
    _trends_cache["ts"] = now
    _trends_cache["data"] = data
    return data

async def find_gaps(domain: str = "all") -> list[dict]:
    llm = get_llm(max_tokens=4000)
    all_projects = get_all_projects_summary()
    domain_filter = f"Focus on the {domain} domain." if domain != "all" else "Cover all domains."
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Output ONLY a JSON array. No explanation."),
        ("human", """SIH projects (2017-2024):

{projects}

{domain_filter}

Find 5 unsolved problem gaps. Return ONLY:
[{{"gap_title":"T","problem":"P","why_unsolved":"W","potential_solution_direction":"S","domain":"D","urgency":"High/Medium/Low","beneficiaries":"B","estimated_impact":"I"}}]""")
    ])
    chain = prompt | llm | StrOutputParser()
    response = await _invoke_with_retry(chain.ainvoke, {
        "projects": all_projects,
        "domain_filter": domain_filter
    })
    try:
        return _as_list(_extract_json(response))
    except Exception:
        return [{"error": "Could not parse gaps", "raw": response}]

async def generate_ideas(domain: str, theme: str = "", num_ideas: int = 3) -> list[dict]:
    llm = get_llm(max_tokens=6000)
    query = f"{domain} {theme} India problem solution"
    similar = retrieve_similar_projects(query, n_results=6)
    context = "\n\n".join([
        f"Past Project: {p['metadata']['title']} ({p['metadata']['year']})\n"
        f"Domain: {p['metadata']['domain']}\n"
        f"Summary: {p['document'][:300]}..."
        for p in similar
    ])
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Output ONLY a JSON array. No explanation."),
        ("human", """Generate {num_ideas} novel SIH project ideas for {domain}.
{theme_instruction}

Past projects:
{context}

Return ONLY:
[{{"title":"T","tagline":"TL","problem_statement":"P","solution":"S","domain":"{domain}","technologies":["t1","t2"],"novelty_score":8,"feasibility_score":7,"impact_score":9,"novelty_reason":"R","similar_past_projects":["id"],"target_beneficiaries":"B","ministry_fit":"M"}}]""")
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
        return _as_list(_extract_json(response))[:num_ideas]
    except Exception:
        return [{"error": "Could not parse ideas", "raw": response[:500]}]

async def chat_with_advisor(message: str, history: list[dict]) -> str:
    llm = get_llm(max_tokens=1000)
    similar = retrieve_similar_projects(message, n_results=4)
    context = "\n".join([
        f"- {p['metadata']['title']} ({p['metadata']['year']}): {p['document'][:200]}..."
        for p in similar
    ])
    messages = [
        ("system", f"""You are a SIH (Smart India Hackathon) advisor helping students build winning projects. You know all SIH winning projects from 2017-2024. Give actionable, specific, encouraging advice.

Relevant past projects for context:
{context}""")
    ]
    for msg in history[-6:]:
        messages.append((msg["role"], msg["content"]))
    messages.append(("human", message))
    prompt = ChatPromptTemplate.from_messages(messages)
    chain = prompt | llm | StrOutputParser()
    try:
        response = await _invoke_with_retry(chain.ainvoke, {})
        return _strip_reasoning(response)
    except LLMQuotaError:
        return ("I've hit my AI service's usage limit for the moment. Please try again soon; I'll be ready to help with SIH ideas then.")
    except Exception:
        return ("I'm having trouble reaching the AI service right now. Please try again in a moment.")

_stats_cache: Optional[dict] = None

def get_statistics() -> dict:
    global _stats_cache
    if _stats_cache is not None:
        return _stats_cache
    with open(config.DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    domains = {}
    years = {}
    techs = {}
    for p in data:
        d = p["domain"]
        domains[d] = domains.get(d, 0) + 1
        y = p["year"]
        years[y] = years.get(y, 0) + 1
        for t in p["technologies"]:
            techs[t] = techs.get(t, 0) + 1
    top_techs = sorted(techs.items(), key=lambda x: x[1], reverse=True)[:10]
    _stats_cache = {
        "total_projects": len(data),
        "years_covered": "2017-2024",
        "domains_count": len(domains),
        "domain_breakdown": domains,
        "year_breakdown": dict(sorted(years.items())),
        "top_technologies": [{"tech": t, "count": c} for t, c in top_techs],
        "hardware_projects": sum(1 for p in data if p.get("is_hardware")),
        "software_projects": sum(1 for p in data if not p.get("is_hardware")),
    }
    return _stats_cache