# foundry_sdk_phase/backend/agent_chat_service.py
import os
import time
from typing import Dict, Generator, List, Tuple

from azure.ai.agents.models import ListSortOrder, FileState
from dotenv import load_dotenv

from .init_agents import init_foundry

load_dotenv()
_client = None
_agent_map: Dict[str, object] | None = None
PERSISTENT_VECTOR_STORE_NAME = "real_agents_main_store"

def _bootstrap():
    global _client, _agent_map
    if _client is None or _agent_map is None:
        _client, _agent_map = init_foundry()
    return _client, _agent_map

class AgentChatService:
    def __init__(self):
        """Initializes the service without creating a vector store."""
        self.client, agent_map = _bootstrap()
        self.agent_id = agent_map["InvestmentAdvisorAgent"].id
        self.threads: Dict[str, str] = {}
        self.current: str | None = None
        self.vector_store_id: str | None = None

    def _attach_vector_store_to_zoning(self, vs_id: str):
        """Attaches a single vector store to the ZoningAdvisorAgent."""
        print(f"Attaching vector store {vs_id} to ZoningAdvisorAgent...")
        zoning = next((a for a in self.client.agents.list_agents() if a.name == "ZoningAdvisorAgent"), None)
        if zoning is None:
            print("ZoningAdvisorAgent not found.")
            return

        resources = zoning.tool_resources or {}
        fs_cfg = resources.get("file_search", {})
        
        fs_cfg["vector_store_ids"] = [vs_id]
        resources["file_search"] = fs_cfg

        self.client.agents.update_agent(
            agent_id=zoning.id,
            tools=zoning.tools,
            tool_resources=resources,
        )
        print("Attachment successful.")

    def upload_files(self, file_paths: list[str]) -> None:
        """
        On first call, finds or creates a persistent vector store.
        Then, uploads files and adds them to that store.
        """
        if not file_paths:
            return
            
        if self.vector_store_id is None:
            print(f"First upload of session. Looking for persistent vector store '{PERSISTENT_VECTOR_STORE_NAME}'...")
            all_stores = self.client.agents.vector_stores.list()
            store = next((s for s in all_stores if s.name == PERSISTENT_VECTOR_STORE_NAME), None)

            if store:
                print(f"Found existing vector store with ID: {store.id}")
                self.vector_store_id = store.id
            else:
                print("No existing store found. Creating a new one...")
                store = self.client.agents.vector_stores.create(name=PERSISTENT_VECTOR_STORE_NAME)
                print(f"Created new vector store with ID: {store.id}")
                self.vector_store_id = store.id
            
            self._attach_vector_store_to_zoning(self.vector_store_id)

        print(f"Uploading {len(file_paths)} file(s)...")
        file_ids: list[str] = []
        for fp in file_paths:
            info = self.client.agents.files.upload(file_path=fp, purpose="assistants")
            while True:
                info = self.client.agents.files.get(info.id)
                if info.status == FileState.PROCESSED:
                    file_ids.append(info.id)
                    break
                elif info.status in [FileState.FAILED, FileState.CANCELLED]:
                    print(f"File {fp} failed to process.")
                    break
                time.sleep(1)
        
        if not file_ids:
            print("No files were successfully processed for upload.")
            return

        print(f"Adding {len(file_ids)} file(s) to vector store {self.vector_store_id}...")
        
        for file_id in file_ids:
            # --- FINAL FIX: Pass file_id inside the 'body' dictionary ---
            self.client.agents.vector_store_files.create_and_poll(
                vector_store_id=self.vector_store_id,
                body={"file_id": file_id}
            )

    def create_thread(self, name: str) -> None:
        thread_id = self.client.agents.threads.create().id
        self.threads[name] = thread_id
        self.current = name

    def delete_thread(self, name: str) -> None:
        tid = self.threads.pop(name, None)
        if tid:
            self.client.agents.threads.delete(thread_id=tid)
        self.current = next(iter(self.threads), None)

    def switch(self, name: str) -> None:
        if name not in self.threads:
            raise ValueError(f"Thread '{name}' not found")
        self.current = name

    def _stream(self, thread_id: str, user_input: str) -> Generator[Tuple, None, None]:
        self.client.agents.messages.create(
            thread_id=thread_id, role="user", content=user_input
        )
        with self.client.agents.runs.stream(
            thread_id=thread_id, agent_id=self.agent_id
        ) as stream:
            yield from stream

    def stream_chat(self, user_input: str) -> Generator[Tuple, None, None]:
        if not self.current:
            raise RuntimeError("No active thread.")
        thread_id = self.threads[self.current]
        yield from self._stream(thread_id, user_input)

    def history(self, name: str | None = None, *, plain: bool = True):
        name = name or self.current
        if not name:
            return []
        thread_id = self.threads[name]
        msgs = self.client.agents.messages.list(
            thread_id=thread_id,
            order=ListSortOrder.ASCENDING,
        )
        out = []
        for m in msgs:
            if not getattr(m, "text_messages", None):
                continue
            text = m.text_messages[-1].text.value.strip()
            if plain:
                out.append(f"{m.role.title()}: {text}")
            else:
                out.append({"role": m.role, "content": text})
        return out