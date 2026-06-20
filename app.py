import json
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

# This automatically reads the .env file and loads the keys into os.environ
load_dotenv()

app = FastAPI()

# LangChain will now seamlessly find the GOOGLE_API_KEY loaded by load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Please set the GOOGLE_API_KEY or GEMINI_API_KEY in your .env file.")

# Initialize the LangChain Chat Model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=api_key,
    include_thoughts=True
)

chat_history = [
    SystemMessage(content="You are Jacob, an Intelligent Assistant who is very helpful and efficient. You will assist the user with their queries and provide information as needed.")
]

@app.get("/")
async def serve_ui():
    """Serves the frontend HTML file."""
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.post("/chat")
async def chat_endpoint(request: Request):
    """Handles the chat request and streams the LangChain response."""
    global chat_history
    data = await request.json()
    user_message = data.get("message", "")
    
    # Add user message to chat history
    chat_history.append(HumanMessage(content=user_message))

    async def event_stream():
        ai_response = ""  # Collect the AI response
        
        async for chunk in llm.astream(chat_history):
            content = chunk.content
            
            if isinstance(content, list):
                for block in content:
                    text = block.get("text", "")
                    if not text:
                        continue
                    
                    ai_response += text  # Accumulate response
                    is_thought = block.get("thought") is True or block.get("type") == "reasoning"
                    
                    if is_thought:
                        yield f"data: {json.dumps({'type': 'thought', 'content': text})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'text', 'content': text})}\n\n"
            
            elif isinstance(content, str) and content:
                ai_response += content  # Accumulate response
                yield f"data: {json.dumps({'type': 'text', 'content': content})}\n\n"
        
        # Add AI response to chat history
        chat_history.append(AIMessage(content=ai_response))
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    print("Starting server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
