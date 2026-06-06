import os
import json
import time
import logging
from openai import OpenAI
from dotenv import load_dotenv
from tavily import TavilyClient
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

load_dotenv()
client= OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tavily= TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# ─── LOGGING ──────────────────────────────────────────────────────────────────

logging. basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()

    ]
)
logger=logging.getLogger(__name__)

# ─── FASTAPI APP ──────────────────────────────────────────────────────────────

app=FastAPI(title="Research Agent")

# ─── MEMORY ───────────────────────────────────────────────────────────────────

MEMORY_FILE = "memory.json"


def load_memory()-> list:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    
    return [{'role':'system', 'content': "You are a helpful research agent. Use web search to find accurate, current information. Always be concise and factual. If you use the calculator, show your working."}]

def save_memory(messages: list)->list:
    serializable=[]
    for m in messages:
        if hasattr(m, "model_dump"):
            serializable.append(m.model_dump())
        else:
            serializable.append(m)
    
    with open(MEMORY_FILE, 'w') as f:
        json.dump(serializable, f, indent=2)

# ─── INPUT VALIDATION ─────────────────────────────────────────────────────────

def validate_input(user_message:str)->str:
    if len(user_message)>1000:
        raise ValueError("Input too long, Max 1000 charcters")
    
    suspicious= ["ignore all instructions","ignore previous","new instruction", "disregard", "you are now"]

    lower=user_message.lower()
    for phrase in suspicious:
        if phrase in lower:
            raise ValueError("Invalid input detected.")
    
    return user_message.strip()

# ─── TOOLS ────────────────────────────────────────────────────────────────────

def web_search(query: str)->str:
    try:
        response=TavilyClient.search(query=query, max_results=3)
        results=[]
        for r in response["results"]:
            results.append(f"Title: {r['title']}\nURL: {r['url']}\nSummary: {r['content']}\n")
        return "\n---\n".join(results)
    except Exception as e:
        logger.error(f"web search failed: {e}")
        return f"TOOL_ERROR: Web search failed — {str(e)}. Use your training data instead."

def calculator(expression: str)->str:
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current, real-time information. Use this for news, prices, recent events, or anything that needs up to date data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a math expression e.g. 2 + 2 or 10 * 5",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "A math expression to evaluate"}
                },
                "required": ["expression"]
            }
        }
    }
]

tool_map = {
    "web_search": web_search,
    "calculator": calculator,
}

# ─── LLM WITH RETRY ───────────────────────────────────────────────────────────

def call_llm_with_retry(messages: list, max_retries: int=3):

    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                timeout=30
            )
        except Exception as e:
            if attempt==max_retries-1:
                raise e
            wait= 2 ** attempt
            logger.warning(f"LLM call failed, retrying in {wait}s: {e}")
            time.sleep(wait)


# ─── AGENT ────────────────────────────────────────────────────────────────────

def run_agent(user_message: str)->str:
    logger.info(f"User: {user_message[:50]}")

    # Load memory from disk
    messages=load_memory()

    messages.append({"role":"user", "content": user_message})

    steps=0
    total_tokens=0
    tools_used=[]

    while True:
        # infinite Loop Protection
        if steps >=10:
            logger.warning("Max  steps reached")
            return{
                "response": "I needed too many steps for this. Try a simpler question.",
                "tokens": total_tokens,
                "cost": round((total_tokens / 1_000_000) * 0.15, 4),
                "tools_used": tools_used,
                "steps": steps
            }
        
        steps+=1
        response= call_llm_with_retry(messages)
        total_tokens+=response.usage.total_tokens

        assistant_message=response.choices[0].message
        messages.append(assistant_message)

        if assistant_message.tool_calls:
            for tool_call in assistant_message.tool_calls:
                tool_name=tool_call.function.name
                tool_args=json.loads(tool_call.function.arguments)

                logger.info(f"Tool: {tool_name}-{tool_args}")
                tools_used.append(tool_name)

                tool_result = tool_map[tool_name](**tool_args)

                messages.append({
                    "role": "tool",
                    "content": tool_result,
                    "tool_call_id": tool_call.id
                })
        
        else:
            save_memory(messages)

            cost=round((total_tokens/1_000_000)*0.15,4)
            logger.info(f"Done — {steps} steps, {total_tokens} tokens, ${cost}")

            return {
                "response": assistant_message.content,
                "tokens": total_tokens,
                "cost": cost,
                "tools_used": tools_used,
                "steps": steps
            }

# ─── API ROUTES ───────────────────────────────────────────────────────────────

class chatRequest(BaseModel):
    message: str

@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

@app.post("/chat")
def chat(request: chatRequest):
    # validate input
    try:
        message=validate_input(request.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Run agent
    try:
        result=run_agent(message)
        return result
    except Exception as e:
        logger.error(f"Agent error: {e}")
        raise HTTPException(status_code=500, detail="Agent encountered an error. Please try again.")

@app.delete("/memory")
def clear_memory():
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
    logger.info("Memory cleared")
    return {"message": "Memory cleared successfully"}








    

    