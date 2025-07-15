# frontend/gradio_chat.py
import gradio as gr
from foundry_sdk_phase.backend.agent_chat_service import AgentChatService

# ──────────────────────────────────────────────────────────────
#  SINGLETON SERVICE
# ──────────────────────────────────────────────────────────────
chat_service = AgentChatService()            # one client; threads switch internally


# ──────────────────────────────────────────────────────────────
#  CHAT SEND
# ──────────────────────────────────────────────────────────────
def chat_fn(user_msg: str, history: list[dict]):
    history.append({"role": "user", "content": user_msg})
    yield history, ""                                         # clear textbox

    assistant_reply = chat_service.send(user_msg)
    history.append({"role": "assistant", "content": assistant_reply})
    yield history, ""


# ──────────────────────────────────────────────────────────────
#  THREAD HANDLERS
# ──────────────────────────────────────────────────────────────
def create_new_chat(all_threads: list[str]):
    name = f"Thread {len(all_threads) + 1}"
    chat_service.create_thread(name)
    all_threads.append(name)
    return (
        gr.Dataset(samples=[[t] for t in all_threads]),
        [],                          # empty chat window
        all_threads,
        name,
    )


def switch_active_chat(evt: gr.SelectData):
    name = evt.value[0]
    chat_service.switch(name)
    hist = chat_service.history(name, plain=False)            # ← dict format
    return hist, name


def delete_current_chat(current_thread: str, all_threads: list[str]):
    if not current_thread:
        return gr.Dataset(samples=[[t] for t in all_threads]), [], all_threads, current_thread

    chat_service.delete_thread(current_thread)
    all_threads.remove(current_thread)

    new_active = chat_service.current
    new_history = (
        chat_service.history(new_active, plain=False) if new_active else []
    )
    return (
        gr.Dataset(samples=[[t] for t in all_threads]),
        new_history,
        all_threads,
        new_active,
    )


def initialize_app():
    chat_service.create_thread("Thread 1")
    threads = ["Thread 1"]
    return (
        gr.Dataset(samples=[[t] for t in threads]),
        threads,
        "Thread 1",
    )


# ──────────────────────────────────────────────────────────────
#  GRADIO UI
# ──────────────────────────────────────────────────────────────
with gr.Blocks(theme=gr.themes.Default()) as demo:
    all_threads = gr.State([])        # list[str]
    current_thread = gr.State(None)   # str | None

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("<h1>R.E.A.L.-Analyst</h1>")
            new_btn = gr.Button("➕ New Chat", variant="secondary")

            thread_selector = gr.Dataset(
                components=["text"],
                label="Conversations",
                samples=[],
                samples_per_page=10,
            )

            del_btn = gr.Button("🗑️ Delete Chat", variant="secondary")

        with gr.Column(scale=3):
            gr.Markdown("<h2>💬 R.E.A.L.-Analyst — Investment Advisor</h2>")
            chatbot = gr.Chatbot(type="messages", show_label=False, height=600)
            with gr.Row():
                user_box = gr.Textbox(
                    placeholder="Ask your real-estate question…",
                    show_label=False,
                    scale=4,
                    container=False,
                )
                send_btn = gr.Button("Send", variant="primary", scale=1, min_width=150)

    # Initial load
    demo.load(initialize_app,
              outputs=[thread_selector, all_threads, current_thread])

    # Send message
    send_btn.click(chat_fn, [user_box, chatbot], [chatbot, user_box])
    user_box.submit(chat_fn, [user_box, chatbot], [chatbot, user_box])

    # New / delete chat
    new_btn.click(create_new_chat, [all_threads],
                  [thread_selector, chatbot, all_threads, current_thread])

    del_btn.click(delete_current_chat,
                  [current_thread, all_threads],
                  [thread_selector, chatbot, all_threads, current_thread])

    # Switch chat
    thread_selector.select(
        switch_active_chat,
        outputs=[chatbot, current_thread],
    )

if __name__ == "__main__":
    demo.launch()
