# In src/backend/models/messages_kernel.py

from enum import Enum

class AgentType(str, Enum):
    
    # --- ADD THE NEW ONES ---
    USER_PROXY = "User_Proxy_Agent"              # Represents the human user in the chat
    PLANNER = "Planner_Agent"                    # The orchestrator
    INVESTMENT_ANALYST = "Investment_Analyst_Agent"  # The main expert
    VALUATION = "Valuation_Agent"                # The appraiser
    ZONING_COMPLIANCE = "Zoning_Compliance_Agent"    # The inspector
    DOCUMENT_RETRIEVAL = "Document_Retrieval_Agent"  # The RAG specialist

    # Keep these if they are used by the core logic
    GROUP_CHAT_MANAGER = "Group_Chat_Manager"