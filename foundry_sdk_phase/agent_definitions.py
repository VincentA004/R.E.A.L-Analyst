import os
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "prompt_templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def render_prompt(template_name: str, context: dict = None) -> str:
    """Render a Jinja2 prompt template with optional context."""
    context = context or {}
    template = env.get_template(template_name)
    return template.render(**context)

def get_all_agents():
    """Return all agent definitions with rendered instructions."""
    agents = [
        {
            "name": "InvestmentAdvisorAgent",
            "template": "investment_advisor.j2",
            "context": {},
        },
        {
            "name": "ValuationExpertAgent",
            "template": "valuation_expert.j2",
            "context": {},
        },
        {
            "name": "ZoningAdvisorAgent",
            "template": "zoning_advisor.j2",
            "context": {},
        }
    ]

    return [
        {
            "name": agent["name"],
            "instructions": render_prompt(agent["template"], agent.get("context", {})),
            "tools": []  # To be filled later by setup_agent_tools.py
        }
        for agent in agents
    ]
