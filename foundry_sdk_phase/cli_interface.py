import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder

from init_agents import init_foundry_environment

def run_prompt_with_agent(client: AIProjectClient, agent_name: str, user_input: str):
    agent = next(agent for agent in client.agents.list_agents() if agent.name == agent_name)
    thread = client.agents.threads.create()
    message = client.agents.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_input
    )
    run = client.agents.runs.create_and_process(thread_id=thread.id, agent_id=agent.id)

    if run.status == "failed":
        print(f"[ERROR] Run failed: {run.last_error}")
        return

    messages = client.agents.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
    for msg in messages:
        if msg.role == "assistant" and msg.text_messages:
            print(f"\n🔍 Agent Response:\n{msg.text_messages[-1].text.value}\n")
            return

def main():
    print("Building R.E.A.L Agents CLI...")
    load_dotenv()
    AZURE_PROJECT_ENDPOINT = os.getenv("AZURE_PROJECT_ENDPOINT")
    if not AZURE_PROJECT_ENDPOINT:
        raise EnvironmentError("Missing AZURE_PROJECT_ENDPOINT in .env")

    credential = DefaultAzureCredential()
    client = AIProjectClient(endpoint=AZURE_PROJECT_ENDPOINT, credential=credential)

    init_foundry_environment(client)
    print("Foundry environment initialized successfully.")

    os.system('cls' if os.name == 'nt' else 'clear')
    print("Welcome to the R.E.A.L Agents CLI!")
    print("Type your question or type 'quit' to exit.\n")

    while True:
        user_prompt = input("sys> ")
        if user_prompt.lower() in {"quit", "exit"}:
            break
        if not user_prompt.strip():
            print("Please enter a prompt.")
            continue

        run_prompt_with_agent(client, "InvestmentAdvisorAgent", user_prompt)

if __name__ == "__main__":
    main()
