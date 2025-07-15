import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder

from foundry_sdk_phase.backend import init_foundry_environment

def run_prompt_with_agent(client: AIProjectClient, agent_id: str, thread_id: str, user_input: str):
    client.agents.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input
    )

    run = client.agents.runs.create_and_process(thread_id=thread_id, agent_id=agent_id)

    if run.status == "failed":
        print(f"[ERROR] Run failed: {run.last_error}")
        return

    messages = client.agents.messages.list(thread_id=thread_id, order=ListSortOrder.ASCENDING)
    for msg in messages:
        if msg.role == "assistant" and msg.text_messages:
            print(f"\nR.E.A.L> {msg.text_messages[-1].text.value}\n")
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

    # Get agent and create thread once
    agent = next(agent for agent in client.agents.list_agents() if agent.name == "InvestmentAdvisorAgent")
    thread = client.agents.threads.create()

    while True:
        user_prompt = input("USER> ")
        if user_prompt.lower() in {"quit", "exit"}:
            break
        if not user_prompt.strip():
            print("Please enter a prompt.")
            continue

        run_prompt_with_agent(client, agent.id, thread.id, user_prompt)

if __name__ == "__main__":
    main()
