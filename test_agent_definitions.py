
from agent_definitions import get_all_agents
 # Now this will work

def test_agent_definitions():
    try:
        agents = get_all_agents()
        assert isinstance(agents, list), "Expected a list of agents"

        for agent in agents:
            print(f"\n🔹 Agent: {agent['name']}")
            print("---- Rendered Instructions (first 300 chars) ----")
            print(agent["instructions"][:300], "...\n")

            assert "Role" in agent["instructions"], f"Missing 'Role' section in {agent['name']}"
            assert "Output Format" in agent["instructions"], f"Missing 'Output Format' in {agent['name']}"

        print(" All agents rendered successfully.")
    except Exception as e:
        print(f"Error during agent rendering: {e}")

if __name__ == "__main__":
    test_agent_definitions()
