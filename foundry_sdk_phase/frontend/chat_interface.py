# frontend/chat_interface.py
"""R.E.A.L-Analyst Gradio UI (no extra Send button)

Changes vs. previous revision
-----------------------------
* Removed the separate blue `Send` button — `gr.MultimodalTextbox` already
  provides its own submit icon.
* Message submission now relies solely on `user_box.submit(...)`.
"""

from __future__ import annotations

import gradio as gr
from gradio import ChatMessage
from typing import List, Dict, Any

from foundry_sdk_phase.backend.agent_chat_service import AgentChatService

chat_service = AgentChatService()

# ──────────────────────────────────────────────────────────────
#  Helper functions
# ──────────────────────────────────────────────────────────────

def _as_messages(dict_list):
    return [ChatMessage(role=d["role"], content=d["content"]) for d in dict_list]


def _parse_user_input(inp: Any):
    if isinstance(inp, dict):
        files_raw = inp.get("files", [])
        # Each item is already a str path; just use it directly
        file_paths = [f if isinstance(f, str) else f.name for f in files_raw]
        return inp.get("text", ""), file_paths
    return str(inp), []



# ──────────────────────────────────────────────────────────────
#  Streaming chat
# ──────────────────────────────────────────────────────────────

def chat_stream(user_raw: Any, history: List[ChatMessage]):
    history = history or []
    user_text, files = _parse_user_input(user_raw)
    if files:
        chat_service.upload_files(files)

    history.append(ChatMessage(role="user", content=user_text))
    yield history, None

    active: Dict[str, ChatMessage] = {}

    for evt_type, evt_data, *_ in chat_service.stream_chat(user_text):
        if evt_type == "thread.run.step.delta":
            step = evt_data.get("delta", {}).get("step_details", {})
            if step.get("type") == "tool_calls":
                for tc in step.get("tool_calls", []):
                    cid = tc.get("id") or str(tc.get("index"))
                    if cid not in active:
                        bubble = ChatMessage(role="assistant", content="", metadata={"title": f"🛠 {tc['type']}", "status": "pending"})
                        history.append(bubble)
                        active[cid] = bubble
                    if tc.get("function"):
                        active[cid].content = tc["function"].get("arguments", "")
            yield history, None

        elif evt_type == "thread.message.delta":
            chunk = "".join(c["text"].get("value", "") for c in evt_data["delta"]["content"])
            if not history or history[-1].role != "assistant":
                history.append(ChatMessage(role="assistant", content=chunk))
            else:
                history[-1].content += chunk
            yield history, None

        elif evt_type == "run_step" and evt_data["status"] == "completed":
            for msg in active.values():
                msg.metadata["status"] = "done"
            active.clear()
            yield history, None

    yield history, None


# ──────────────────────────────────────────────────────────────
#  Thread operations
# ──────────────────────────────────────────────────────────────

def create_new_chat(all_threads: list[str]):
    name = f"Thread {len(all_threads) + 1}"
    chat_service.create_thread(name)
    all_threads.append(name)
    return gr.update(choices=all_threads, value=name), [], all_threads, name


def switch_active_chat(sel: str):
    if not sel:
        return [], None
    chat_service.switch(sel)
    return _as_messages(chat_service.history(sel, plain=False)), sel


def delete_current_chat(cur: str, all_threads: list[str]):
    if not cur:
        return gr.update(choices=all_threads, value=None), [], all_threads, None
    chat_service.delete_thread(cur)
    all_threads.remove(cur)
    new_active = chat_service.current
    dd = gr.update(choices=all_threads, value=new_active)
    new_hist = _as_messages(chat_service.history(new_active, plain=False)) if new_active else []
    return dd, new_hist, all_threads, new_active


def initialize_app():
    chat_service.create_thread("Thread 1")
    threads = ["Thread 1"]
    return gr.update(choices=threads, value="Thread 1"), threads, "Thread 1"


# ──────────────────────────────────────────────────────────────
#  Theme & CSS
# ──────────────────────────────────────────────────────────────

brand_theme = (
    gr.themes.Default(primary_hue="blue", secondary_hue="blue", neutral_hue="gray", text_size="lg")
    .set(button_primary_background_fill="#0f6cbd", button_primary_text_color="#fff", body_background_fill="#f5f5f5")
)
CSS_HIDE_FOOTER = "footer {visibility: hidden;}"


# ──────────────────────────────────────────────────────────────
#  UI layout
# ──────────────────────────────────────────────────────────────

with gr.Blocks(theme=brand_theme, css=CSS_HIDE_FOOTER, fill_height=True) as demo:
    all_threads = gr.State([])
    current_thread = gr.State(None)

    gr.HTML("<h1 style='text-align:center;'>R.E.A.L-Analyst • Investment Advisor</h1>")

    with gr.Row(equal_height=False):
        with gr.Column(scale=1):
            new_btn = gr.Button("➕  New Chat", variant="secondary", size="sm")
            del_btn = gr.Button("🗑️  Delete Chat", variant="secondary", size="sm")
            thread_selector = gr.Dropdown(label="Conversations", choices=[], interactive=True)

        with gr.Column(scale=3):
            chatbot = gr.Chatbot(type="messages", show_label=False, height=620)
            user_box = gr.MultimodalTextbox(
                placeholder="Ask your real-estate question… (attach docs if needed)",
                show_label=False,
                file_types=[".pdf", ".txt", ".docx"],
            )

    # Initialise dropdown & states
    demo.load(initialize_app, outputs=[thread_selector, all_threads, current_thread])

    # Submit via builtin textbox send icon / Enter
    user_box.submit(chat_stream, [user_box, chatbot], [chatbot, user_box])

    new_btn.click(create_new_chat, [all_threads], [thread_selector, chatbot, all_threads, current_thread])
    del_btn.click(delete_current_chat, [current_thread, all_threads], [thread_selector, chatbot, all_threads, current_thread])
    thread_selector.change(switch_active_chat, thread_selector, [chatbot, current_thread])


if __name__ == "__main__":
    demo.launch()
