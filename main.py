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
