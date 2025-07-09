
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import OpenApiTool,  OpenApiAnonymousAuthDetails,OpenApiConnectionAuthDetails, OpenApiConnectionSecurityScheme
from azure.ai.agents.models import BingGroundingTool, FileSearchTool
from azure.ai.agents.models import ConnectedAgentTool

def register_all_tools(client: AIProjectClient):


    agent_map = {agent.name: agent for agent in client.agents.list_agents()}
    
    zoning_agent = agent_map.get("ZoningAdvisorAgent")
    valuation_agent = agent_map.get("ValuationExpertAgent") 
    investment_agent = agent_map.get("InvestmentAdvisorAgent")
    
    register_zoning_tools(zoning_agent, client)
    register_valuation_tools(valuation_agent, client)

    register_investment_tools(investment_agent, zoning_agent, valuation_agent, client)

def register_investment_tools(investment_agent: AgentsClient, zoning_subagent: AgentsClient, valuation_subagent: AgentsClient, client: AIProjectClient):
    """
    Registers investment-related tools for the InvestmentAdvisorAgent.
    """

    # Register Zoning and Valuation Subagents
    zoning_tool = ConnectedAgentTool(
        agent_id=zoning_subagent.id,
        name="Zoning Advisor",
        description="Connects to the Zoning Advisor Agent for zoning-related queries."
    )

    valuation_tool = ConnectedAgentTool(
        agent_id=valuation_subagent.id,
        name="Valuation Expert",
        description="Connects to the Valuation Expert Agent for property valuation queries."
    )

    investment_agent.update_agent(
        agent_id=investment_agent.id,
        tools=[zoning_tool, valuation_tool]
    )

def register_zoning_tools(zoning_agent: AgentsClient, client: AIProjectClient):
    """
    Registers zoning-related tools for the ZoningAdvisorAgent.
    """
    # Register File Search Tool
    file_search_tool = FileSearchTool(
       vector_store_ids = []
    )
    
    bing_connection_name = os.getenv("BING_CONNECTION_NAME")
    if not bing_connection_name:
        raise EnvironmentError("Missing BING_CONNECTION_NAME in environment variables")
    
    bing_connection = client.connections.get(bing_connection_name)
    grounding_tool = BingGroundingTool(connection_id=bing_connection.id)

    zoning_agent.update_agent(
        agent_id=zoning_agent.id,
        tools=[file_search_tool, grounding_tool]
    )
    
def register_valuation_tools(valuation_agent: AgentsClient, client: AIProjectClient): 
    
    rentcast_tool = _register_rentcast_tool(
        client=client,
        name="rentcast_api",
        description="Tool for accessing RentCast real estate data, including rent estimates, comps, and market trends.",
        auth_type=os.getenv("RENTCAST_AUTH_MODE", "anonymous")
    )

    bing_connection_name = os.getenv("BING_CONNECTION_NAME")
    if not bing_connection_name:
        raise EnvironmentError("Missing BING_CONNECTION_NAME in environment variables")
    
    bing_connection = client.connections.get(bing_connection_name)
    grounding_tool = BingGroundingTool(connection_id=bing_connection.id)
    
    valuation_agent.update_agent(
        agent_id=valuation_agent.id,
        tools = [rentcast_tool, grounding_tool]
    )


def _register_rentcast_tool(client: AIProjectClient, name: str, description: str, auth_type: str = "anonymous") -> OpenApiTool:
    """
    Registers the RentCast OpenAPI tool using either anonymous or connection-based authentication.
    """
    load_dotenv()
    schema_dir = Path(__file__).parent / "openapi_schemas"

    if auth_type == "anonymous":
        api_key = os.getenv("RENTCAST_API_KEY")
        if not api_key:
            raise EnvironmentError("Missing RENTCAST_API_KEY in environment variables")

        schema_path = schema_dir / f"rentcast_{auth_type}.json"
        with open(schema_path, "r") as f:
            schema_template = f.read()

        schema_filled = schema_template.replace("{{API_KEY}}", api_key)
        spec = json.loads(schema_filled)

        return OpenApiTool(
            name=name,
            description=description,
            spec=spec,
            auth=OpenApiAnonymousAuthDetails()
        )

    elif auth_type == "connection":
        connection_name = os.getenv("RENTCAST_CONNECTION")
        if not connection_name:
            raise EnvironmentError("Missing RENTCAST_CONNECTION in environment variables")

        schema_path = schema_dir / f"rentcast_{auth_type}.json"
        with open(schema_path, "r") as f:
            spec = json.loads(f.read())

        connection = client.connections.get(connection_name)

        return OpenApiTool(
            name=name,
            description=description,
            spec=spec,
            auth=OpenApiConnectionAuthDetails(
                security_scheme=OpenApiConnectionSecurityScheme(connection_id=connection.id)
            )
        )

    else:
        raise ValueError(f"Unsupported auth_type '{auth_type}'. Use 'anonymous' or 'connection'.")

