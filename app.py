import json
import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
from pr_analyzer import PRAnalysisEngine

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

# Initialize PR Analysis Engine
pr_engine = PRAnalysisEngine(api_key=api_key)

# Store for human intervention approvals
human_interventions = {}

chat_history = [
    SystemMessage(content="You are Jacob, an Intelligent Assistant who is very helpful and efficient. You will assist the user with their queries and provide information as needed.")
]

@app.get("/")
async def serve_ui():
    """Serves the frontend HTML file."""
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.post("/analyze-pr")
async def analyze_pr(request: Request):
    """
    Analyzes a PR and generates:
    1. Technical Documentation
    2. Threat Modeling Report
    3. Mind Map
    
    Fetches PR details from GitHub if PR URL is provided
    Returns streaming responses for each analysis task
    """
    data = await request.json()
    
    # Get PR details from GitHub
    owner = data.get("owner")
    repo = data.get("repo")
    pr_number = data.get("pr_number")
    
    async def event_stream():
        try:
            # Fetch PR details from GitHub
            yield f"data: {json.dumps({'type': 'status', 'message': 'Fetching PR details from GitHub...', 'step': 'fetch_pr'})}\n\n"
            
            pr_info = await pr_engine.mcp_manager.fetch_pr_details(owner, repo, pr_number)
            
            # Build message to avoid nested f-string quote conflicts
            pr_title = pr_info.get('title', 'Unknown')
            analysis_msg = f"Analyzing PR #{pr_number}: {pr_title}..."
            yield f"data: {json.dumps({'type': 'status', 'message': analysis_msg, 'step': 'start_analysis'})}\n\n"
            
            # Check existing files first
            yield f"data: {json.dumps({'type': 'status', 'message': 'Checking for existing analysis...', 'step': 'check_existing'})}\n\n"
            
            # Run parallel analysis
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting parallel PR analysis...', 'step': 'start_parallel'})}\n\n"
            
            analysis_results = await pr_engine.analyze_pr(pr_info)
            
            # Stream each result
            techno_data = {'type': 'techno_doc', 'content': analysis_results['techno_doc']['content'], 'status': analysis_results['techno_doc']['status'], 'is_update': analysis_results['techno_doc']['is_update']}
            yield f"data: {json.dumps(techno_data)}\n\n"
            
            threat_data = {'type': 'threat_report', 'content': analysis_results['threat_report']['content'], 'status': analysis_results['threat_report']['status'], 'is_update': analysis_results['threat_report']['is_update']}
            yield f"data: {json.dumps(threat_data)}\n\n"
            
            mindmap_data = {'type': 'mindmap', 'content': analysis_results['mindmap']['content'], 'status': analysis_results['mindmap']['status'], 'is_update': analysis_results['mindmap']['is_update']}
            yield f"data: {json.dumps(mindmap_data)}\n\n"
            
            yield f"data: {json.dumps({'type': 'status', 'message': 'Analysis complete. Please review and approve changes.', 'step': 'complete'})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/approve-changes")
async def approve_changes(request: Request):
    """
    Handles human approval for generated files
    Stores approval status for follow-up processes
    """
    data = await request.json()
    pr_number = data.get("pr_number")
    approved_items = data.get("approved_items", [])
    
    human_interventions[pr_number] = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "approved": approved_items,
        "notes": data.get("notes", "")
    }
    
    return {
        "status": "approved",
        "pr_number": pr_number,
        "approved_items": approved_items,
        "message": f"Changes approved for PR #{pr_number}"
    }

@app.post("/reject-changes")
async def reject_changes(request: Request):
    """
    Handles rejection or modification requests for generated files
    Allows human to provide feedback for regeneration
    """
    data = await request.json()
    pr_number = data.get("pr_number")
    reason = data.get("reason", "No reason provided")
    
    human_interventions[pr_number] = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "rejected": True,
        "reason": reason
    }
    
    return {
        "status": "rejected",
        "pr_number": pr_number,
        "reason": reason,
        "message": "Changes rejected. Please provide feedback for regeneration."
    }

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
