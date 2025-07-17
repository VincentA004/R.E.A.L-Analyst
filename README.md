# R.E.A.L.-Analyst

**R.E.A.L.-Analyst (Real Estate Agentic Layer Analyst)** is an AI-native platform designed to automate and augment real estate market analysis using agent-based collaboration. The system leverages Microsoft’s Azure AI Foundry ecosystem to deliver intelligent, end-to-end insights across property valuation, zoning compliance, market trends, and investment strategy.

The long-term vision is to build a robust, multi-agent system capable of ingesting property documents, integrating with third-party data sources (e.g., RentCast, ATTOM), and autonomously generating professional-grade comparative market analyses (CMAs) and investment reports.

---

## Phase 1: Foundry SDK MVP (Minimal Viable Prototype)

The current version of the project represents **Phase 1**, a streamlined multi-agent prototype built using the `azure-ai-projects` and `azure-ai-agents` SDKs. Rather than full orchestration, Phase 1 registers supporting agents as callable tools within a primary agent — enabling modular, agentic behavior while keeping architecture minimal and developer-friendly.

### Agent Architecture

- **InvestmentAdvisor Agent** (Primary Agent)  
  Handles user interaction and thread management; calls sub-agents via tool usage

- **ValuationAgent** (Sub-agent)  
  Provides property valuation insights

- **ZoningAgent** (Sub-agent)  
  Analyzes zoning rules and regulatory context

### Key Capabilities

- Multi-agent structure via tool-based sub-agent registration  
- Thread-based memory and persistent history via Foundry APIs  
- Early tool usage and response streaming  
- Foundation for full orchestration and autonomy in future phases  

👉 **Technical implementation details for Phase 1 can be found [here](./foundry_sdk_phase/README.md).**


---

## Phase 2: Full Enterprise Agentic Platform (In Progress)

**Phase 2** transforms R.E.A.L.-Analyst into a fully cloud-native, production-grade, enterprise agentic application. It will leverage **Azure AI Foundry Agent Service** for hosting, **Semantic Kernel** for rich multi-agent orchestration, and fully integrated Azure infrastructure for scalability, security, and extensibility.

### Key Architecture Highlights

- **Semantic Kernel Orchestration**  
  Complex workflows and coordination across specialized agents  
  Support for reasoning, retries, tool chaining, and decision delegation

- **Azure AI Foundry Agent Service**  
  Full production hosting of containerized agents  
  Native observability, scaling, and lifecycle management

- **Custom Agentic Memory Layer**  
  Built on **Azure Cosmos DB** for structured thread-agent-user memory

- **Enterprise Document Intelligence**  
  Document ingestion and retrieval using **Azure Blob Storage** and Azure AI Search

- **Multitenant Deployment**  
  Designed to support multiple users/clients with isolated threads, memory, and data

This phase aims to bring a **SaaS-level, multi-tenant, intelligent automation system** to life — powering real estate professionals with fast, reliable, and deeply contextual AI agents.
