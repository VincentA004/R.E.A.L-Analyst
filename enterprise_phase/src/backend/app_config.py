import os
import logging
from typing import Optional

from dotenv import load_dotenv
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential, ManagedIdentityCredential

# Load environment variables from .env file
load_dotenv()

class AppConfig:
    """Application configuration class that loads settings from environment variables."""

    def __init__(self):
        """Initialize the application configuration."""
        
        # --- Authentication Settings ---
        self.AZURE_TENANT_ID = self._get_optional("AZURE_TENANT_ID")
        self.AZURE_CLIENT_ID = self._get_optional("AZURE_CLIENT_ID")
        self.AZURE_CLIENT_SECRET = self._get_optional("AZURE_CLIENT_SECRET")
        self.APP_ENV = self._get_optional("APP_ENV", "dev")

        # --- Azure AI Agent Service Settings ---
        self.AZURE_AI_AGENT_ENDPOINT = self._get_required("AZURE_AI_AGENT_ENDPOINT")
        self.AZURE_AI_AGENT_API_KEY = self._get_required("AZURE_AI_AGENT_API_KEY")

        # --- Cosmos DB Settings (for BYO Storage) ---
        self.COSMOSDB_ENDPOINT = self._get_required("COSMOSDB_ENDPOINT")
        self.COSMOSDB_DATABASE = self._get_required("COSMOSDB_DATABASE", "enterprise_memory")
        
        # --- File Search (RAG) Settings ---
        self.AZURE_STORAGE_CONNECTION_STRING = self._get_required("AZURE_STORAGE_CONNECTION_STRING")

        # --- Cached Clients ---
        self._azure_credential = None
        self._cosmos_client = None
        self._cosmos_database = None

    def _get_required(self, name: str, default: Optional[str] = None) -> str:
        """Get a required configuration value."""
        value = os.environ.get(name)
        if value:
            return value
        if default:
            return default
        raise ValueError(f"Required environment variable '{name}' not found.")

    def _get_optional(self, name: str, default: str = "") -> str:
        """Get an optional configuration value."""
        return os.environ.get(name, default)

    def get_azure_credential(self):
        """
        Returns the appropriate async Azure credential based on the environment.
        - In 'dev' mode, it uses DefaultAzureCredential.
        - In 'prod' mode, it uses ManagedIdentityCredential.
        """
        if self._azure_credential is None:
            if self.APP_ENV == "dev":
                self._azure_credential = DefaultAzureCredential()
            else:
                self._azure_credential = ManagedIdentityCredential(client_id=self.AZURE_CLIENT_ID)
        return self._azure_credential

    def get_cosmos_database_client(self):
        """Get a cached async Cosmos DB client for the configured database."""
        try:
            if self._cosmos_client is None:
                self._cosmos_client = CosmosClient(
                    self.COSMOSDB_ENDPOINT, credential=self.get_azure_credential()
                )

            if self._cosmos_database is None:
                self._cosmos_database = self._cosmos_client.get_database_client(
                    self.COSMOSDB_DATABASE
                )
            return self._cosmos_database
        except Exception as exc:
            logging.error("Failed to create CosmosDB client: %s", exc)
            raise

# Create a global instance for easy access throughout the application
config = AppConfig()