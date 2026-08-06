"""
chains.py
LangChain chains for generating professional project blueprints via OpenRouter.
"""

from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
from agents import get_llm, retrieve_similar_projects, _invoke_with_retry, _strip_reasoning

def _extract_json(text: str) -> dict:
    text = _strip_reasoning(text or "")
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"```\s*$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response")
    return json.loads(text[start:end + 1])

_BLUEPRINT_DEFAULTS = {
    "project_overview": {"title": "", "tagline": "", "executive_summary": "", "domain": "", "problem_type": ""},
    "problem_analysis": {"current_situation": "", "why_urgent_now": "", "root_causes": []},
    "proposed_solution": {"solution_overview": "", "key_features": [], "unique_value_proposition": ""},
    "technical_architecture": {"tech_stack": {}, "data_flow": ""},
    "implementation_plan": {"duration": "", "phases": []},
    "team_structure": {"roles": []},
    "impact_assessment": {
        "primary_beneficiaries": "",
        "beneficiary_count": "",
        "measurable_outcomes": [],
        "sdg_goals_addressed": [],
    },
    "budget_estimate": {"total_budget": "", "breakdown": []},
    "risk_analysis": {"risks": []},
    "demo_plan": {"demo_flow": [], "key_wow_moments": []},
    "conclusion": {"why_this_will_win": "", "government_adoption_path": ""},
}

def _normalize_blueprint(raw: dict) -> dict:
    """Ensure every top-level section the frontend expects is present, even if the
    model omitted it, so the rendered blueprint is always complete."""
    merged = dict(_BLUEPRINT_DEFAULTS)
    if not isinstance(raw, dict):
        return merged
    for key, default in _BLUEPRINT_DEFAULTS.items():
        val = raw.get(key)
        if isinstance(val, dict) and isinstance(default, dict):
            merged[key] = {**default, **val}
        elif val is not None:
            merged[key] = val
    return merged

async def generate_blueprint(
    title: str,
    problem_statement: str,
    solution: str,
    domain: str,
    technologies: list[str],
    team_size: int = 6,
    duration_weeks: int = 4
) -> dict:
    llm = get_llm(max_tokens=6000)
    query = f"{title} {domain} {problem_statement}"
    similar = retrieve_similar_projects(query, n_results=3)
    references = ", ".join([
        f"{p['metadata']['title']} ({p['metadata']['year']})"
        for p in similar
    ])
    tech_stack = ", ".join(technologies)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a senior SIH blueprint architect. Return ONLY a valid JSON object. No markdown fences, no extra commentary."),
        ("human", """Create a professional Smart India Hackathon blueprint.

Title: {title}
Domain: {domain}
Problem: {problem}
Solution: {solution}
Preferred Tech: {tech_stack}
Team Size: {team_size} people
Duration: {duration_weeks} weeks
Reference winning projects: {refs}

Return ONLY a JSON object matching EXACTLY this schema:

{{"project_overview":{{"title":"{title}","tagline":"<one-line tagline>","executive_summary":"<2-3 sentence summary>","domain":"{domain}","problem_type":"Software or Hardware"}},"problem_analysis":{{"current_situation":"<paragraph>","why_urgent_now":"<paragraph>","root_causes":["<cause1>","<cause2>"]}},"proposed_solution":{{"solution_overview":"<paragraph>","key_features":[{{"feature":"<name>","description":"<detail>","impact":"<outcome>"}}],"unique_value_proposition":"<why this beats alternatives>"}},"technical_architecture":{{"tech_stack":{{"frontend":[],"backend":[],"database":[],"ai_ml":[],"infra":[],"apis":[]}},"data_flow":"<paragraph>"}},"implementation_plan":{{"duration":"{duration_weeks} weeks","phases":[{{"week":"1","phase":"<phase name>","tasks":["<task>"],"deliverable":"<deliverable>"}}]}},"team_structure":{{"roles":[{{"role":"<role>","responsibilities":["<item>"],"skills":["<item>"]}}]}},"impact_assessment":{{"primary_beneficiaries":"<who>","beneficiary_count":"<number>","measurable_outcomes":["<outcome>"],"sdg_goals_addressed":["<SDG>"]}},"budget_estimate":{{"total_budget":"<rupee amount>","breakdown":[{{"item":"<item>","cost":"<rupee amount>","justification":"<reason>"}}]}},"risk_analysis":{{"risks":[{{"probability":"High or Medium or Low","risk":"<risk>","mitigation":"<mitigation>"}}]}},"demo_plan":{{"demo_flow":["<step1>","<step2>"],"key_wow_moments":["<moment>"]}},"conclusion":{{"why_this_will_win":"<paragraph>","government_adoption_path":"<paragraph>"}}}}""")
    ])

    chain = prompt | llm | StrOutputParser()
    last_response = ""
    for attempt in range(2):
        try:
            response = await _invoke_with_retry(chain.ainvoke, {
                "title": title,
                "domain": domain,
                "problem": problem_statement,
                "solution": solution,
                "tech_stack": tech_stack,
                "team_size": team_size,
                "duration_weeks": duration_weeks,
                "refs": references
            })
            last_response = response or ""
            return _normalize_blueprint(_extract_json(last_response))
        except Exception as e:
            pass

    return {
        "error": "Blueprint generation failed. Please try again in a moment.",
        "raw_response": last_response[:1000],
    }