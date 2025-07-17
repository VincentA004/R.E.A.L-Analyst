# R.E.A.L.-Analyst · Foundry SDK Phase

This directory contains the Phase 1 MVP implementation of **R.E.A.L.-Analyst**, a real estate market analysis platform built using the **Azure AI Foundry Project SDK**. It showcases a minimal yet functional multi-agent architecture where subagents are registered as tools under a primary agent.

This prototype lays the foundation for a full enterprise-grade platform, proving out key concepts like:

- Agent registration and orchestration using the Foundry SDK
- Tool-based subagent delegation
- File upload and vector store search
- Interactive frontend (Gradio) and CLI control

## 🧠 Agent Architecture

- **InvestmentAdvisorAgent** (Main Agent)  
  Acts as the user-facing agent. It routes queries to specialized subagents via tool calls.

- **ValuationExpertAgent** (Sub-agent)  
  Handles property valuation using internal vector knowledge and external APIs (e.g., RentCast).

- **ZoningAdvisorAgent** (Sub-agent)  
  Analyzes zoning compliance using internal ordinance data and Bing search.

Each agent is initialized with custom instructions defined in Jinja2 templates and registered via the SDK.

---

## 📁 File Structure

```
foundry_sdk_phase/
├── backend/
│   ├── agent_definitions.py         # Loads and renders prompt templates
│   ├── setup_agent_tools.py         # Registers tools (APIs, Bing, subagents)
│   ├── init_agents.py               # Orchestrates agent creation and setup
│   ├── agent_chat_service.py        # Core chat + vector upload logic
│   ├── chat_api.py                  # FastAPI interface (optional REST layer)
│   ├── openapi_schemas/             # RentCast OpenAPI specs
│   └── prompt_templates/           # Agent-specific Jinja2 prompt templates
│
├── frontend/
│   ├── chat_interface.py            # Gradio streaming UI
│   └── cli_interface.py             # Lightweight terminal interface
```

## 🔍 Technical Highlights

This prototype demonstrates a clean, modular implementation of an AI-native, multi-agent architecture using Microsoft’s Azure AI Foundry SDK stack. The design is intended to be extendable, production-aligned, and cloud-native from day one.

### ✔️ Agent Design and Delegation

- The **InvestmentAdvisorAgent** serves as the system's central decision-maker.  
- It routes domain-specific queries to two tool-registered subagents:
  - **ValuationExpertAgent**: Estimates property value using vector search and external APIs.
  - **ZoningAdvisorAgent**: Assesses compliance with local land use regulations using both internal knowledge and real-time search.

### ✔️ Vector Store and Document Intelligence

- The system attaches a persistent vector store to the ZoningAdvisorAgent.
- Users can upload PDF, TXT, or DOCX files via the frontend.
- Uploaded documents are automatically indexed and associated with the vector store, allowing for contextual retrieval during queries.

### ✔️ Toolchain Integration

- Tool registration is fully automated using the Foundry SDK:
  - **ConnectedAgentTool**: For inter-agent tool calls.
  - **OpenAPITool**: For external services like RentCast.
  - **FileSearchTool** and **BingGroundingTool**: For local document and web-based retrieval.

### ✔️ User Interfaces

- **Gradio UI**: A clean, responsive web interface with streaming assistant replies, file upload, and thread switching.
- **CLI Interface**: Lightweight and fully scriptable; supports multiple threads, history view, and direct LLM interaction.

### ✔️ Project Structure

Code is separated into `backend/` and `frontend/` modules for clean separation of concerns, with `agent_chat_service.py` acting as the interface layer between orchestration logic and the user-facing components.

This phase is designed to be minimal yet idiomatic, aligning with production-ready engineering practices while keeping the codebase highly readable and extensible.

## ⚙️ Setup & Environment Configuration

This project requires Python 3.11+ and access to an Azure AI Foundry project with agents enabled.

### 1. Install Dependencies

We recommend using a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **Note:** `requirements.txt` should include:
> - `azure-ai-projects`
> - `azure-ai-agents`
> - `jinja2`
> - `python-dotenv`
> - `gradio` (for frontend)
> - `fastapi` & `uvicorn` (optional: if using `chat_api.py`)

---

### 2. Environment Variables

Create a `.env` file at the root of the `foundry_sdk_phase/` directory:

```ini
AZURE_PROJECT_ENDPOINT=https://<your-foundry-endpoint>
MODEL_DEPLOYMENT_NAME=gpt-4o  # or gpt-35-turbo, etc.

BING_CONNECTION_NAME=<your-bing-connection-name>
RENTCAST_AUTH_MODE=anonymous  # or 'connection'
RENTCAST_API_KEY={{optional_if_anonymous}}
RENTCAST_CONNECTION={{optional_if_connection}}
```

Ensure the Azure environment is already configured with:
- A registered model deployment
- A Bing search connection (via Azure Connections)
- (Optional) RentCast API access or connection object

---

### 3. Initialize the Agent Environment

Run the following to bootstrap all agents and register tools:

```bash
python backend/init_agents.py
```

This will:
- Render prompt templates from `prompt_templates/`
- Create agents in your Azure AI Foundry project
- Register tools and link subagents


## 💬 Running the Application

This prototype supports two interfaces for interacting with the agent system: a command-line interface and a Gradio-powered web UI. Both communicate through the same underlying `AgentChatService` and support multi-threaded session management.

---

### ▶️ Option 1: Web Interface (Gradio)

Launch the Gradio chat UI:

```bash
python frontend/chat_interface.py
```

Features:
- Live streaming of assistant responses
- File upload support (`.pdf`, `.txt`, `.docx`)
- Create, switch, and delete threads
- Displays tool call execution (e.g., subagent delegation)

Once launched, access the interface at:  
[http://localhost:7860](http://localhost:7860)

---

### ▶️ Option 2: Command-Line Interface (CLI)

Start the terminal-driven chat client:

```bash
python frontend/cli_interface.py
```

Available commands:
- `new` – Create a new chat thread
- `ls` – List all threads
- `switch <name>` – Change active thread
- `history` – Show message history for current thread
- `delete` / `delete -A` – Remove one or all threads
- Any other input is passed directly to the LLM agent

This lightweight interface is ideal for testing or scripting multi-threaded sessions.

---

## 📌 Roadmap & Future Work

This MVP sets the stage for a more advanced, production-grade system in **Phase 2**, which will introduce:

- ✅ **Semantic Kernel Integration**  
  Rich orchestration logic across agents, tool chaining, retry policies, and complex workflows.

- ✅ **Cosmos DB–backed Agentic Memory**  
  Persistent, structured memory organized by user, thread, and agent — enabling personalized, multi-turn reasoning.

- ✅ **Azure Blob Storage + Search**  
  Scalable document ingestion, semantic search, and vector indexing for enterprise-level document intelligence.

- ✅ **Multitenant Hosting via Azure AI Agent Service**  
  Full cloud-native deployment with agent lifecycle management, observability, and horizontal scaling.

---

## 📎 Additional Notes

- All prompts are modular Jinja2 templates and can be extended with domain-specific logic.
- Tools and connections are dynamically registered and fully configurable.
- This codebase is designed for clarity, reproducibility, and extensibility — suitable for both prototyping and real-world deployments.

---

## 🧠 License & Contributions

This repository is under active development. Contributions are welcome as the architecture evolves toward a scalable, cloud-native, agentic platform for real estate intelligence.

---

