import os
import logging
from typing import Optional

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.cosmos.aio import CosmosClient
from azure.ai.project.aio import AIProjectClient
from azure.search.documents.aio import SearchClient
from semantic_kernel.kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AppConfig:
    """
    Application configuration class that loads settings from environment variables
    and provides centralized client management for Azure services.
    """
    def __init__(self):
        # Azure OpenAI / Chat Model Settings
        self.AZURE_OPENAI_ENDPOINT = self._get_required("AZURE_OPENAI_ENDPOINT")
        self.AZURE_OPENAI_DEPLOYMENT_NAME = self._get_required("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        self.AZURE_OPENAI_API_VERSION = self._get_optional("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")
        
        # Azure AI Project (Agent Service / Foundry) Settings
        self.AZURE_AI_PROJECT_ENDPOINT = self._get_required("AZURE_AI_PROJECT_ENDPOINT")
        self.AZURE_AI_SUBSCRIPTION_ID = self._get_required("AZURE_AI_SUBSCRIPTION_ID")
        self.AZURE_AI_RESOURCE_GROUP = self._get_required("AZURE_AI_RESOURCE_GROUP")
        self.AZURE_AI_PROJECT_NAME = self._get_required("AZURE_AI_PROJECT_NAME")
        self.AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME = self._get_optional("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", self.AZURE_OPENAI_DEPLOYMENT_NAME)

        # Cosmos DB Settings (for Agent Memory)
        self.COSMOSDB_ENDPOINT = self._get_required("COSMOSDB_ENDPOINT")
        self.COSMOSDB_DATABASE = self._get_optional("COSMOSDB_DATABASE", "real-estate-db")
        self.COSMOSDB_CONTAINER = self._get_optional("COSMOSDB_CONTAINER", "memory")
        
        # Azure AI Search Settings (for RAG)
        self.AZURE_SEARCH_ENDPOINT = self._get_required("AZURE_SEARCH_ENDPOINT")
        self.AZURE_SEARCH_API_KEY = self._get_required("AZURE_SEARCH_API_KEY")
        self.AZURE_SEARCH_INDEX_NAME = self._get_optional("AZURE_SEARCH_INDEX_NAME", "property-docs-index")

        # Cached clients and credentials
        self._credential = None
        self._token_provider = None
        self._cosmos_client = None
        self._ai_project_client = None
        self._search_client = None

    def _get_required(self, name: str, default: Optional[str] = None) -> str:
        value = os.getenv(name, default)
        if value is None:
            raise ValueError(f"Required environment variable '{name}' not found.")
        return value

    def _get_optional(self, name: str, default: str = "") -> str:
        return os.getenv(name, default)

    def get_credential(self) -> DefaultAzureCredential:
        if self._credential is None:
            self._credential = DefaultAzureCredential()
        return self._credential

    def get_token_provider(self):
        if self._token_provider is None:
            self._token_provider = get_bearer_token_provider(
                self.get_credential(), "https://cognitiveservices.azure.com/.default"
            )
        return self._token_provider

    def create_kernel(self) -> Kernel:
        """Creates a new Semantic Kernel instance with the primary chat service."""
        kernel = Kernel()
        chat_service = AzureChatCompletion(
            deployment_name=self.AZURE_OPENAI_DEPLOYMENT_NAME,
            endpoint=self.AZURE_OPENAI_ENDPOINT,
            api_version=self.AZURE_OPENAI_API_VERSION,
            azure_ad_token_provider=self.get_token_provider(),
        )
        kernel.add_service(chat_service)
        return kernel

    async def get_cosmos_client(self) -> CosmosClient:
        if self._cosmos_client is None:
            self._cosmos_client = CosmosClient(
                self.COSMOSDB_ENDPOINT, credential=self.get_credential()
            )
        return self._cosmos_client

    def get_ai_project_client(self) -> AIProjectClient:
        if self._ai_project_client is None:
            self._ai_project_client = AIProjectClient(
                subscription_id=self.AZURE_AI_SUBSCRIPTION_ID,
                resource_group_name=self.AZURE_AI_RESOURCE_GROUP,
                project_name=self.AZURE_AI_PROJECT_NAME,
                credential=self.get_credential(),
                endpoint=self.AZURE_AI_PROJECT_ENDPOINT
            )
        return self._ai_project_client
    
    async def get_search_client(self) -> SearchClient:
        if self._search_client is None:
            self._search_client = SearchClient(
                endpoint=self.AZURE_SEARCH_ENDPOINT,
                index_name=self.AZURE_SEARCH_INDEX_NAME,
                credential=AzureKeyCredential(self.AZURE_SEARCH_API_KEY)
            )
        return self._search_client

# Create a single, globally accessible instance of the config
config = AppConfig()