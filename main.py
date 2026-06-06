import os
import json
import time
import logging
from openai import OpenAI
from dotenv import load_dotenv
from tavily import TavilyClient
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import BaseMode

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

def validateInput(user_message:str)->str:
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

