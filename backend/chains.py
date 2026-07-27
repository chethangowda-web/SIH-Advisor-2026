"""
chains.py
LangChain chains for generating professional project blueprints.
"""

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import config
from agents import get_llm, retrieve_similar_projects

async def generate_blueprint(
    title: str,
    problem_statement: str,
    solution: str,
    domain: str,
    technologies: list[str],
    team_size: int = 6,
    duration_weeks: int = 4
) -> dict:
    """
    Generate a full professional project blueprint for a SIH submission.
    Returns structured blueprint with all sections.
    """
    llm = get_llm()
    
    # RAG: Get similar projects for reference
    query = f"{title} {domain} {problem_statement}"
    similar = retrieve_similar_projects(query, n_results=3)
    references = "\n".join([
        f"- {p['metadata']['title']} ({p['metadata']['year']})"
        for p in similar
    ])
    
    tech_stack = ", ".join(technologies)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert SIH project consultant who has helped 50+ teams win 
        at Smart India Hackathon. You create PROFESSIONAL, DETAILED project blueprints that 
        impress judges with technical depth and real-world impact understanding.
        
        Write in a confident, professional tone. Be SPECIFIC with numbers and metrics.
        Return ONLY valid JSON. No markdown fences."""),
        ("human", """Create a complete professional SIH project blueprint for:

TITLE: {title}
DOMAIN: {domain}
PROBLEM: {problem_statement}
SOLUTION: {solution}
TECH STACK: {tech_stack}
TEAM SIZE: {team_size} people
DURATION: {duration_weeks} weeks

Similar past SIH projects for inspiration (don't copy, improve upon):
{references}

Return this EXACT JSON structure:
{{
  "project_overview": {{
    "title": "{title}",
    "tagline": "Powerful one-liner",
    "domain": "{domain}",
    "problem_type": "Software/Hardware/Both",
    "executive_summary": "150-word executive summary for judges"
  }},
  "problem_analysis": {{
    "core_problem": "Crisp problem statement",
    "current_situation": "Current state in India with statistics",
    "stakeholders_affected": ["stakeholder1", "stakeholder2"],
    "root_causes": ["cause1", "cause2", "cause3"],
    "why_urgent_now": "Why this needs to be solved today",
    "existing_solutions_limitations": "What existing solutions lack"
  }},
  "proposed_solution": {{
    "solution_overview": "Detailed solution overview",
    "key_features": [
      {{"feature": "Feature name", "description": "Feature description", "impact": "User impact"}}
    ],
    "unique_value_proposition": "What makes this truly different",
    "innovation_aspects": ["innovation1", "innovation2"]
  }},
  "technical_architecture": {{
    "tech_stack": {{
      "frontend": ["tech1"],
      "backend": ["tech2"],
      "ai_ml": ["tech3"],
      "database": ["tech4"],
      "infrastructure": ["tech5"],
      "apis_integrations": ["api1"]
    }},
    "system_components": [
      {{"component": "Component name", "purpose": "What it does", "technology": "Tech used"}}
    ],
    "data_flow": "Step-by-step data flow description",
    "scalability_approach": "How system scales"
  }},
  "implementation_plan": {{
    "total_duration": "{duration_weeks} weeks",
    "phases": [
      {{
        "phase": "Phase 1: Foundation",
        "week": "Week 1",
        "tasks": ["task1", "task2"],
        "deliverable": "What's delivered",
        "team_allocation": "Who does what"
      }}
    ]
  }},
  "team_structure": {{
    "total_members": {team_size},
    "roles": [
      {{"role": "Team Lead / Backend", "responsibilities": ["resp1", "resp2"], "skills_needed": ["skill1"]}}
    ]
  }},
  "impact_assessment": {{
    "primary_beneficiaries": "Who directly benefits",
    "beneficiary_count": "Estimated number",
    "sdg_goals_addressed": ["SDG 3", "SDG 9"],
    "government_schemes_aligned": ["Scheme 1", "Digital India"],
    "short_term_impact": "Impact in 6 months",
    "long_term_impact": "Impact in 5 years",
    "measurable_outcomes": ["outcome1 with metric", "outcome2 with metric"]
  }},
  "budget_estimate": {{
    "total_budget": "₹X,XXX",
    "breakdown": [
      {{"item": "Cloud hosting (AWS/GCP)", "cost": "₹2,000/month", "justification": "Why needed"}}
    ],
    "cost_per_beneficiary": "₹X per user",
    "monetization_potential": "Future revenue model"
  }},
  "risk_analysis": {{
    "risks": [
      {{"risk": "Risk description", "probability": "High/Medium/Low", "mitigation": "How to handle"}}
    ]
  }},
  "demo_plan": {{
    "demo_flow": ["Step 1: Show X", "Step 2: Demonstrate Y"],
    "key_wow_moments": ["Moment that impresses judges"],
    "technical_demo_requirements": ["Laptop", "Internet", "..."]
  }},
  "conclusion": {{
    "why_this_will_win": "Compelling argument for judges",
    "next_steps_post_sih": "What happens after winning",
    "government_adoption_path": "How government can adopt this"
  }}
}}""")
    ])
    
    chain = prompt | llm | StrOutputParser()
    response = await chain.ainvoke({
        "title": title,
        "domain": domain,
        "problem_statement": problem_statement,
        "solution": solution,
        "tech_stack": tech_stack,
        "team_size": team_size,
        "duration_weeks": duration_weeks,
        "references": references
    })
    
    try:
        clean = response.strip().strip("```json").strip("```").strip()
        start = clean.find("{")
        end = clean.rfind("}") + 1
        return json.loads(clean[start:end])
    except Exception as e:
        return {
            "error": f"Blueprint generation failed: {str(e)}",
            "raw_response": response[:1000]
        }
