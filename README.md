# 🧠 RecoverAI — AI Revenue Recovery Agent

> Razorpay Buildathon | Track 03: AI Revenue Recovery

A swarm of **6 AI agents** that detect failed payments, diagnose root causes using **RAG**, recover money through real **WhatsApp/SMS/Email/Voice** via **MCP tool-calling**, learn from outcomes, and generate compliance audit reports.

## 🏗️ Architecture

```
6 LangGraph Agents → 2 MCP Servers (12 tools) → Real APIs
     ↕                    ↕                        ↕
 Supabase (DB)      Pinecone (RAG)         Razorpay + Twilio + Resend
```

## 🚀 Quick Start

### 1. Setup
```bash
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Install Dependencies
```bash
cd backend && pip install -r requirements.txt
cd frontend && npm install
```

### 3. Database
- Create a Supabase project at [supabase.com](https://supabase.com)
- Run `backend/schema.sql` in the Supabase SQL Editor

### 4. Ingest RAG Documents
```bash
cd backend && python -m rag.ingest
```

### 5. Run Batch (ONCE before demo)
```bash
cd backend && python -m simulation.batch_runner
```

### 6. Start Development Servers
```bash
# Terminal 1 — Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

## 🤖 The 6 Agents

| # | Agent | Role |
|---|---|---|
| 1 | 🛡️ **Sentinel** | Detect & triage failures |
| 2 | 🔬 **Diagnostician** | Root cause analysis with RAG |
| 3 | 🎯 **Strategist** | Recovery planning + A/B testing |
| 4 | ⚖️ **Compliance** | 8 guardrail checks + debates |
| 5 | ⚡ **Executor** | Execute via MCP tools |
| 6 | 📊 **Analyst** | Learn + update playbook |

## 🔧 MCP Servers (12 Tools)

### Razorpay MCP Server (7 tools)
`create_payment_link` · `create_order` · `fetch_payment_details` · `fetch_order_payments` · `create_subscription` · `create_invoice` · `list_failed_payments`

### Communications MCP Server (5 tools)
`send_whatsapp` · `send_sms` · `send_email` · `make_voice_call` · `check_dnd_status`

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 + FastAPI |
| Agents | LangGraph StateGraph |
| LLM | Gemini 2.5 Flash |
| Tool Protocol | MCP (Model Context Protocol) |
| Database | Supabase (PostgreSQL + Realtime) |
| Vector DB | Pinecone (RAG) |
| Payments | Razorpay Test Mode |
| Messaging | Twilio (WhatsApp + SMS + Voice) |
| Email | Resend |
| Frontend | React 18 + Vite |
| PDF | WeasyPrint |

## 💰 Total Cost: ₹0

All services used on free tier.

---

Built for Razorpay Buildathon 2025 by Gagan Singhal.
