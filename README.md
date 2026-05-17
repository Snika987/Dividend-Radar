# Dividend Analyzer MCP

A remote MCP server that connects Claude Desktop to live Indian stock portfolio and dividend data.

Built using:

* FastMCP
* Zerodha Kite Connect APIs
* yfinance
* Python

The MCP can:

* fetch live portfolio holdings
* analyze dividend income
* show dividend history
* track recent dividend announcements

---

# Remote MCP Endpoint

```txt
https://dividend-radar.fastmcp.app/mcp
```

---

# Setup

## 1. Clone the repository

```bash
git clone <repo-url>
cd dividend-analyzer-mcp
```

---

## 2. Create virtual environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Mac/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install dependencies

```bash
uv pip install -r requirements.txt
```

---

## 4. Add environment variables

Create a `.env` file:

```env
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret
```

---

# Running Locally

```bash
uv run main.py
```
---
# Testing with MCP Inspector

After starting the server locally, run:
```
uv run fastmcp dev inspector main.py
```
This MCP never requires sharing brokerage credentials with anyone else.
