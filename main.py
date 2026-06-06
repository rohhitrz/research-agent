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