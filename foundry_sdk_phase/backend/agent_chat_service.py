# backend/agent_chat_service.py
import os, time, mimetypes
from typing import Dict, Generator, List

from azure.ai.agents.models import ListSortOrder, FilePurpose, FileState
from dotenv import load_dotenv

from .init_agents import init_foundry    # ← brings in template-render + tool registration

load_dotenv()


# ──────────────────────────────────────────────────────────────
#  SINGLETON INITIALISATION
# ──────────────────────────────────────────────────────────────
_client = None        # type: ignore
_agent_map: Dict[str, object] | None = None   # populated by init_foundry()


def _bootstrap():
    """
    Call init_foundry() exactly once for the whole process.
    Returns (client, agent_map)
    """
    global _client, _agent_map
    if _client is None or _agent_map is None:
        _client, _agent_map = init_foundry()
    return _client, _agent_map


# ──────────────────────────────────────────────────────────────
#  MAIN SERVICE
# ──────────────────────────────────────────────────────────────
class AgentChatService:
    """
    • Runs init_foundry() once (if not already run)
    • Exposes streaming chat, thread ops, file upload
    """

    def __init__(self):
        self.client, agent_map = _bootstrap()
        # Pick the top-level orchestrator
        self.agent_id = agent_map["InvestmentAdvisorAgent"].id

        # {thread_name: thread_id}
        self.threads: Dict[str, str] = {}
        self.current: str | None = None

        # per-session vector store for user uploads
        self._vector_store_id: str | None = None
        
    # backend/agent_chat_service.py
    def _attach_vector_store_to_zoning(self, vs_id: str):
        """Wire the newest vector-store to ZoningAdvisorAgent’s file_search tool."""
        # grab the zoning agent
        zoning = next(
            (a for a in self.client.agents.list_agents() if a.name == "ZoningAdvisorAgent"),
            None,
        )
        if zoning is None:
            return

        # current tool_resources → update file_search vector_store_ids
        resources = zoning.tool_resources or {}
        fs_cfg = resources.get("file_search", {})
        current_ids = set(fs_cfg.get("vector_store_ids", []))
        if vs_id in current_ids:
            return                              # already attached

        fs_cfg["vector_store_ids"] = list(current_ids | {vs_id})
        resources["file_search"] = fs_cfg

        # push update
        self.client.agents.update_agent(
            agent_id=zoning.id,
            tools=zoning.tools,          # ← include existing tools list
            tool_resources=resources,
        )




    def upload_files(self, file_paths: list[str]) -> None:
        """
        Upload docs and build a private vector store (new store per upload).
        Compatible with current azure-ai-agents SDK.
        """
        if not file_paths:
            return

        file_ids: list[str] = []
        for fp in file_paths:
            info = self.client.agents.files.upload(file_path=fp, purpose="assistants")
            while info.status != FileState.PROCESSED:     # poll
                time.sleep(1)
                info = self.client.agents.files.get(info.id)
            file_ids.append(info.id)

        # ALWAYS create a fresh vector store for this batch
        store = self.client.agents.vector_stores.create_and_poll(
            file_ids=file_ids,
            name=f"user-store-{int(time.time())}",
        )
        self._vector_store_id = store.id
        self._attach_vector_store_to_zoning(store.id)

        # keep the latest store id so the agent’s file_search tool can see it
        self._vector_store_id = store.id

    # ---------- THREAD OPS ----------
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

    # ---------- STREAMING CHAT ----------
    def _stream(
        self, thread_id: str, user_input: str
    ) -> Generator[tuple[str, dict], None, None]:
        """Emit (event_type, event_data) tuples as Azure streams them."""
        self.client.agents.messages.create(
            thread_id=thread_id, role="user", content=user_input
        )
        with self.client.agents.runs.stream(
            thread_id=thread_id, agent_id=self.agent_id
        ) as stream:
            for item in stream:
                yield item  # (event_type, event_data, …)

    def stream_chat(
        self, user_input: str
    ) -> Generator[tuple[str, dict], None, None]:
        if not self.current:
            raise RuntimeError("No active thread.")
        thread_id = self.threads[self.current]
        yield from self._stream(thread_id, user_input)

    # ---------- HISTORY ----------
        # ---------- HISTORY ----------
    def history(self, name: str | None = None, *, plain: bool = True):
        """
        Returns either:
            ["User: …", "Assistant: …"]                 # plain=True (default)
        or:
            [{"role": "user", "content": …}, …]         # plain=False
        """
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
            # skip messages with no text payload (e.g. pure tool-call stubs)
            if not getattr(m, "text_messages", None):
                continue
            text = m.text_messages[-1].text.value.strip()
            if plain:
                out.append(f"{m.role.title()}: {text}")
            else:
                out.append({"role": m.role, "content": text})
        return out

