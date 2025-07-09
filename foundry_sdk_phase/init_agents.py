import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from agent_definitions import get_all_agents
from setup_agent_tools import register_all_tools
# from foundry_sdk_phase.setup_agent_knowledge import load_all_knowledge

load_dotenv()

AZURE_PROJECT_ENDPOINT = os.getenv("AZURE_PROJECT_ENDPOINT")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")


def init_foundry_environment():
    if not AZURE_PROJECT_ENDPOINT or not MODEL_DEPLOYMENT_NAME:
        raise EnvironmentError("Missing AZURE_PROJECT_ENDPOINT or MODEL_DEPLOYMENT_NAME in .env")

    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=AZURE_PROJECT_ENDPOINT, credential=credential)

    print("Rendering agent templates...")
    agent_templates = get_all_agents()

    print("Checking for existing agents...")
    existing_agents = client.agents.list_agents()
    existing_agent_map = {agent.name: agent for agent in existing_agents}

    for agent in agent_templates:
        agent_name = agent["name"]
        instructions = agent["instructions"]

        if agent_name in existing_agent_map:
            print(f"Agent '{agent_name}' already exists (ID: {existing_agent_map[agent_name].id})")
        else:
            created_agent = client.agents.create_agent(
                name=agent_name,
                model=MODEL_DEPLOYMENT_NAME,
                instructions=instructions,
                tools=agent.get("tools", []),
            )
            print(f"Created agent '{created_agent.name}'")


    print("Registering tools...")
    register_all_tools(client)

    print("Foundry agent environment setup complete.")


if __name__ == "__main__":
    init_foundry_environment()
