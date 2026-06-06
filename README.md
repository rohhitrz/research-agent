# 🔍 Research Agent

A production-ready AI agent built from scratch with tool use, persistent memory, 
cost tracking, and a FastAPI backend. Deployable as a domain-specific research 
assistant for any vertical.

## Demo

> Ask it anything — it searches the web, does math, remembers your conversation, 
> and shows you exactly what it did and what it cost.

![Research Agent Demo](demo.png)

## What makes this different from a chatbot

| Feature | ChatGPT | This Agent |
|---------|---------|------------|
| Tool use | Fixed | Fully customizable |
| Memory | Session only | Persistent across sessions |
| Cost visibility | None | Per-message token + cost tracking |
| Source code | Closed | You own every line |
| Extensible | No | Add any tool or domain |

## Architecture

Browser (HTML/JS)
│
│ POST /chat
▼
FastAPI Backend
│
├── Input validation + prompt injection defence
├── Retry logic with exponential backoff
├── Cost + token tracking
├── Persistent memory (JSON)
└── Agent Loop (ReAct — Reason, Act, Observe)
│
├── web_search → Tavily (real-time web)
└── calculator → math expressions


## Features

- **ReAct agent loop** — LLM reasons, acts, observes in a loop until goal is complete
- **Real web search** — Tavily integration for live internet access
- **Persistent memory** — conversation history saved across sessions
- **Cost tracking** — token usage and estimated cost shown per message
- **Input validation** — length limits and prompt injection defence
- **Retry logic** — exponential backoff on API failures
- **Infinite loop protection** — max steps guard
- **Structured logging** — every run logged to file for debugging
- **Clear memory** — one-click session reset

## Tech Stack

- **Backend** — Python, FastAPI, Uvicorn
- **LLM** — OpenAI GPT-4o-mini
- **Search** — Tavily API
- **Frontend** — HTML, CSS, Vanilla JS
- **Memory** — JSON persistence

## Getting Started

### Prerequisites
- Python 3.10+
- OpenAI API key — [platform.openai.com](https://platform.openai.com)
- Tavily API key — [tavily.com](https://tavily.com) (free tier)

### Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/research-agent.git
cd research-agent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install openai python-dotenv tavily-python fastapi uvicorn
```

### Configuration

Create a `.env` file in the root directory:

OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here


### Run

```bash
uvicorn main:app --reload
```

Open [http://localhost:8000](http://localhost:8000)

## How it works

Every user message triggers the ReAct loop:
REASON  — LLM reads the goal + full conversation history
and decides what to do next
ACT     — Picks and calls a tool (web_search or calculator)
OBSERVE — Tool result is added back to context
REPEAT  — Until LLM decides it has enough to answer
RESPOND — Final answer returned to user


The entire conversation is saved to `memory.json` after each run,
so the agent remembers context across sessions.

## Extending this agent

This architecture is domain-agnostic. Swap the tools to build:

- **Internal knowledge agent** — replace web_search with your docs/database
- **Legal research agent** — connect to a legal database
- **Sales agent** — connect to your CRM
- **Coding assistant** — connect to your codebase
- **Financial agent** — connect to market data APIs

## Project Structure

research-agent/
├── main.py          # FastAPI app + agent logic
├── index.html       # Frontend
├── memory.json      # Conversation history (auto-generated)
├── agent.log        # Runtime logs (auto-generated)
├── .env             # API keys (never committed)
├── .gitignore
└── README.md


