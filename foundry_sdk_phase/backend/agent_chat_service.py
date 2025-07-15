# backend/agent_chat_service.py
import time
from typing import Dict, List
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import ListSortOrder
from .init_agents import init_foundry


class AgentChatService:
    """
    A singleton-friendly service:
    • keeps one Azure client
    • holds agent_id
    • can create / switch threads quickly
    """

    def __init__(self):
        self.client, agent_map = init_foundry()
        self.agent_id = agent_map["InvestmentAdvisorAgent"].id

        # key = thread name  |  value = thread_id
        self.threads: Dict[str, str] = {}
        self.current: str | None = None

    # ----------  THREAD OPS  ----------
    def create_thread(self, name: str) -> None:
        """Create Azure thread and register it."""
        thread_id = self.client.agents.threads.create().id
        self.threads[name] = thread_id
        self.current = name

    def delete_thread(self, name: str) -> None:
        thread_id = self.threads.pop(name, None)
        if thread_id:
            self.client.agents.threads.delete(thread_id=thread_id)
        # choose another if any left
        self.current = next(iter(self.threads), None)

    def switch(self, name: str) -> None:
        if name in self.threads:
            self.current = name
        else:
            raise ValueError(f"Thread '{name}' not found")

    # ----------  CHAT OPS  ----------
    def _run(self, thread_id: str, user_input: str) -> str:
        self.client.agents.messages.create(
            thread_id=thread_id, role="user", content=user_input
        )
        run = self.client.agents.runs.create_and_process(
            thread_id=thread_id, agent_id=self.agent_id
        )

        # poll until completed/failed
        while run.status not in {"completed", "failed", "cancelled", "expired"}:
            time.sleep(1)
            run = self.client.agents.runs.get(thread_id=thread_id, run_id=run.id)

        if run.status != "completed":
            return f"[ERROR] Run ended with status: {run.status}"

        msgs = list(
            self.client.agents.messages.list(
                thread_id=thread_id, order=ListSortOrder.ASCENDING
            )
        )
        for m in reversed(msgs):
            if m.role == "assistant" and m.text_messages:
                return m.text_messages[-1].text.value.strip()
        return "[No assistant response found]"

    def send(self, user_input: str) -> str:
        if not self.current:
            return "[ERROR] No active thread."
        return self._run(self.threads[self.current], user_input)

    def history(self, name: str | None = None, *, plain: bool = True):
        """
        Returns either
          ["User: hello", "Assistant: …"]          # plain=True (default)
        or
          [{"role":"user","content":"hello"}, …]   # plain=False
        """
        name = name or self.current
        if not name:
            return []

        thread_id = self.threads[name]
        messages  = self.client.agents.messages.list(
            thread_id=thread_id,
            order=ListSortOrder.ASCENDING,
        )

        out = []
        for msg in messages:
            if msg.text_messages:                      # works for both roles now
                text = msg.text_messages[-1].text.value.strip()
                if plain:
                    out.append(f"{msg.role.title()}: {text}")
                else:
                    out.append({"role": msg.role, "content": text})
        return out


