# chat_api.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.agent_chat_service import AgentChatService

app = FastAPI(
    title="R.E.A.L. Agent API",
    description="Interact with the InvestmentAdvisorAgent via Azure AI Foundry.",
    version="1.0.0"
)

# Service instance
chat = AgentChatService()
thread_active = True


class ChatRequest(BaseModel):
    message: str


@app.post("/chat", summary="Send a message to the agent")
def send_chat_message(req: ChatRequest):
    if not thread_active or chat.thread_id is None:
        raise HTTPException(status_code=400, detail="Thread has been deleted. Call /reset to start a new one.")
    try:
        response = chat.send_message(req.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history", summary="Get the current thread's message history")
def get_history():
    if not thread_active or chat.thread_id is None:
        raise HTTPException(status_code=400, detail="Thread has been deleted. Call /reset to start a new one.")
    try:
        history = chat.get_history()
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset", summary="Create a new thread")
def reset_thread():
    global thread_active
    try:
        chat.reset_thread()
        thread_active = True
        return {"status": "Thread reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/thread", summary="Delete the current thread")
def delete_thread():
    global thread_active
    try:
        chat.delete_thread()
        thread_active = False
        return {"status": "Thread deleted. Please POST to /reset to start a new one."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
