<p align="center">
  <img src="https://img.shields.io/badge/Razorpay-Buildathon_2025-002970?style=for-the-badge&logo=razorpay&logoColor=white" />
  <img src="https://img.shields.io/badge/Track_03-AI_Revenue_Recovery-6366f1?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Agents-6_LangGraph_Swarm-22c55e?style=for-the-badge" />
  <img src="https://img.shields.io/badge/MCP_Tools-12-f59e0b?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Cost-₹0-ef4444?style=for-the-badge" />
</p>

<h1 align="center">🧠 RecoverAI</h1>
<h3 align="center">Autonomous AI Revenue Recovery Agent Platform</h3>
<p align="center"><em>A production-grade, self-learning multi-agent system that autonomously detects failed payments, diagnoses root causes via RAG, orchestrates intelligent recovery through real omni-channel communication (WhatsApp, SMS, Email, Voice), and continuously optimizes strategies with reinforcement learning — all while enforcing RBI/TRAI compliance at every step.</em></p>

<p align="center">
  <a href="#-architecture"><img src="https://img.shields.io/badge/Architecture-HLD-blue?style=flat-square" /></a>
  <a href="#-the-7-ai-agents"><img src="https://img.shields.io/badge/Agents-7_Autonomous-green?style=flat-square" /></a>
  <a href="#-mcp-servers--12-tools"><img src="https://img.shields.io/badge/MCP-12_Tools-orange?style=flat-square" /></a>
  <a href="#-rag-knowledge-engine-4-knowledge-bases"><img src="https://img.shields.io/badge/RAG-4_Knowledge_Bases-purple?style=flat-square" /></a>
  <a href="#-quick-start"><img src="https://img.shields.io/badge/Setup-5_min-red?style=flat-square" /></a>
</p>

---

## 🎯 Problem Statement

> **"Find revenue that's slipping away and win it back"** — Razorpay Buildathon Track 03

Indian merchants lose **₹18,000 Cr+ annually** to failed payments, abandoned checkouts, and overdue invoices. Existing solutions are rule-based, single-channel, and lack intelligence. RecoverAI solves this with **autonomous AI agents** that think, debate, act, and learn — recovering revenue 24/7 without human intervention.

### Why RecoverAI Wins

| Pain Point | Traditional Tools | RecoverAI |
|---|---|---|
| **Detection** | Manual monitoring | Real-time AI sentinel with anomaly detection |
| **Diagnosis** | Generic error codes | RAG-powered root cause analysis with bank outage correlation |
| **Strategy** | Static rules | Gemini AI + Thompson Sampling A/B testing |
| **Compliance** | No guardrails | 8-check gate with inter-agent debates & legal citations |
| **Execution** | Single channel | Omni-channel (WhatsApp + SMS + Email + Voice + Auto-Retry) |
| **Learning** | None | Continuous RAG playbook updates + reinforcement loop |
| **Languages** | English only | Hindi / Hinglish / English (geo-aware auto-selection) |
| **Two-Way Chat** | ❌ | ✅ Real-time Gemini-powered conversational recovery |

---

## 🏗️ Architecture

### High-Level Design (HLD)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        RecoverAI — System Architecture                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐    ┌──────────────────────────────────────────────────────┐  │
│  │   React 18    │    │           FastAPI Backend (Python 3.11)              │  │
│  │   + Vite      │◄──►│  ┌──────────────────────────────────────────────┐  │  │
│  │   + D3.js     │    │  │         LangGraph StateGraph Swarm           │  │  │
│  │   + Recharts  │    │  │                                              │  │  │
│  │   + Framer    │    │  │  Sentinel → Diagnostician → Strategist      │  │  │
│  │   Motion      │    │  │       → Compliance → Executor → Analyst     │  │  │
│  │               │    │  │                                              │  │  │
│  │  ┌──────────┐ │    │  │  + Conversational Agent (Two-Way WhatsApp)  │  │  │
│  │  │ Supabase │ │    │  └──────────────┬───────────────────────────────┘  │  │
│  │  │ Realtime │ │    │                 │                                    │  │
│  │  └──────────┘ │    │      ┌──────────┴──────────┐                        │  │
│  └──────────────┘    │      ▼                      ▼                        │  │
│                       │  ┌────────────┐    ┌────────────────┐               │  │
│                       │  │  Razorpay  │    │     Comms      │               │  │
│                       │  │ MCP Server │    │  MCP Server    │               │  │
│                       │  │ (7 tools)  │    │  (5 tools)     │               │  │
│                       │  └─────┬──────┘    └───────┬────────┘               │  │
│                       └────────┼───────────────────┼────────────────────────┘  │
│                                │                   │                            │
│  ┌─────────────────────────────┼───────────────────┼──────────────────────────┐│
│  │                     Cloud Services Layer                                   ││
│  │                                                                             ││
│  │  ┌───────────┐ ┌──────────┐ ┌────────┐ ┌───────┐ ┌────────┐ ┌──────────┐ ││
│  │  │ Razorpay  │ │ Pinecone │ │ Wabery │ │Twilio │ │ Resend │ │ Gemini   │ ││
│  │  │ Test Mode │ │ (RAG)    │ │ (WA)   │ │(SMS/  │ │ (Email)│ │ 3.1 Flash││
│  │  │ Payments  │ │ 4 KB     │ │ 2-Way  │ │Voice) │ │        │ │ + Embed  │ ││
│  │  └───────────┘ └──────────┘ └────────┘ └───────┘ └────────┘ └──────────┘ ││
│  │  ┌───────────┐ ┌──────────┐ ┌──────────┐                                  ││
│  │  │ Fast2SMS  │ │  MSG91   │ │ Supabase │                                  ││
│  │  │ (SMS-IN)  │ │ (CPaaS)  │ │ Postgres │                                  ││
│  │  └───────────┘ └──────────┘ └──────────┘                                  ││
│  └────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Agent Swarm Pipeline — Sequence Diagram

```
┌─────────┐  ┌──────────┐  ┌───────────────┐  ┌───────────┐  ┌────────────┐  ┌──────────┐  ┌─────────┐
│ Razorpay│  │ Sentinel │  │ Diagnostician │  │ Strategist│  │ Compliance │  │ Executor │  │ Analyst │
│ Webhook │  │ Agent 1  │  │   Agent 2     │  │  Agent 3  │  │  Agent 4   │  │ Agent 5  │  │ Agent 6 │
└────┬────┘  └────┬─────┘  └──────┬────────┘  └─────┬─────┘  └─────┬──────┘  └────┬─────┘  └────┬────┘
     │            │               │                  │              │              │             │
     │ payment.   │               │                  │              │              │             │
     │ failed     │               │                  │              │              │             │
     │───────────►│               │                  │              │              │             │
     │            │ Urgency Score │                  │              │              │             │
     │            │ + Fingerprint │                  │              │              │             │
     │            │ + LTV Triage  │                  │              │              │             │
     │            │──────────────►│                  │              │              │             │
     │            │               │ RAG: Error Codes │              │              │             │
     │            │               │ + Bank Outage    │              │              │             │
     │            │               │   Correlation    │              │              │             │
     │            │               │ + Gemini LLM     │              │              │             │
     │            │               │──────────────────►              │              │             │
     │            │               │                  │ RAG:Playbook │              │             │
     │            │               │                  │ + A/B Test   │              │             │
     │            │               │                  │ + Thompson   │              │             │
     │            │               │                  │   Sampling   │              │             │
     │            │               │                  │─────────────►│              │             │
     │            │               │                  │              │ 8 Guardrails│              │
     │            │               │                  │              │ + Debates   │              │
     │            │               │                  │              │ + RAG Legal │              │
     │            │               │                  │              ├─approved───►│             │
     │            │               │                  │              │              │ MCP Tools  │
     │            │               │                  │              │              │ + Razorpay │
     │            │               │                  │              │              │ + WhatsApp │
     │            │               │                  │              │              │ + SMS/Email│
     │            │               │                  │              │              │ + Voice    │
     │            │               │                  │              │              │────────────►│
     │            │               │                  │              │              │             │ Update
     │            │               │                  │              │              │             │ RAG
     │            │               │                  │              │              │             │ Playbook
     │            │               │                  │              │              │             │ + A/B
     │            │               │                  │              │              │             │ Stats
```

### Two-Way WhatsApp Conversational Recovery Flow

```
┌──────────┐     ┌─────────────────┐     ┌─────────────────────┐     ┌───────────┐
│ Customer │     │  Wabery Cloud   │     │  Conversational AI  │     │ Supabase  │
│ WhatsApp │     │  WhatsApp API   │     │  Agent (Gemini LLM) │     │    DB     │
└────┬─────┘     └───────┬─────────┘     └──────────┬──────────┘     └─────┬─────┘
     │                   │                          │                      │
     │  Customer types   │                          │                      │
     │  "kal pay karunga"│                          │                      │
     │──────────────────►│                          │                      │
     │                   │  Polling Listener (3s)   │                      │
     │                   │─────────────────────────►│                      │
     │                   │                          │ NLU Intent:          │
     │                   │                          │ promise_to_pay       │
     │                   │                          │ Date: tomorrow       │
     │                   │                          │──────────────────────►│
     │                   │                          │   INSERT promise     │
     │                   │                          │   UPDATE txn status  │
     │                   │  AI Reply (Hinglish)     │                      │
     │                   │◄─────────────────────────│                      │
     │  "Koi baat nahi!  │                          │                      │
     │   Hum aapko kal   │                          │                      │
     │   remind karenge" │                          │                      │
     │◄──────────────────│                          │                      │
     │                   │                          │                      │
     │  ┌─── Next Day (Promise Date) ───────────────┐                     │
     │  │  Reminder Scheduler Daemon (30s loop)     │                     │
     │  │  auto-dispatches follow-up via WhatsApp   │                     │
     │  └───────────────────────────────────────────┘                     │
```

### Compliance Gate — Agent Debate Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                  COMPLIANCE OFFICER (Agent 4)                        │
│                  8-Check Guardrail Gate                               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │ CHECK 1: Opt-Out          → HARD BLOCK    [Consumer Act 2019]  │ │
│  │ CHECK 2: Active Dispute   → HARD BLOCK    [RBI Ombudsman 2021] │ │
│  │ CHECK 3: DND Registry     → SOFT MODIFY   [TRAI DND 2018]     │ │
│  │ CHECK 4: Time Window      → SOFT MODIFY   [TRAI TCCCPR 2018]  │ │
│  │ CHECK 5: Retry Limit      → HARD BLOCK    [Internal Policy]   │ │
│  │ CHECK 6: Frequency Cap    → HARD BLOCK    [Industry Practice] │ │
│  │ CHECK 7: Cool-Off Period  → HARD BLOCK    [Industry Practice] │ │
│  │ CHECK 8: High-Value Tag   → ADVISORY      [Analytics Only]    │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                           │                                          │
│                    ┌──────┴──────┐                                   │
│                    │   Verdict   │                                   │
│                    ├─────────────┤                                   │
│                    │  approved   │──► Execute recovery action        │
│                    │  modified   │──► Execute with channel swap      │
│                    │  blocked    │──► Log exception + Gemini debate  │
│                    └─────────────┘                                   │
│                                                                      │
│  On BLOCK: Gemini AI generates legal debate with RBI/TRAI citations │
│  On MODIFY: Static debate template (no LLM call — optimized)       │
└──────────────────────────────────────────────────────────────────────┘
```

### RAG Knowledge Engine Pipeline

```
┌──────────────────────────────────────────────────────────────────────┐
│              Pinecone Vector DB (4 Knowledge Bases)                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────────────────────────────┐ │
│  │ KB1: Error Codes  │  │  24 Razorpay error codes with bank-     │ │
│  │ (error_codes)     │  │  specific diagnosis & recovery actions  │ │
│  └──────────────────┘  └──────────────────────────────────────────┘ │
│  ┌──────────────────┐  ┌──────────────────────────────────────────┐ │
│  │ KB2: Compliance   │  │  10 RBI/TRAI/Consumer Protection rules  │ │
│  │ (compliance)      │  │  with legal citations & section numbers │ │
│  └──────────────────┘  └──────────────────────────────────────────┘ │
│  ┌──────────────────┐  ┌──────────────────────────────────────────┐ │
│  │ KB3: Playbook     │  │  Self-evolving — Analyst agent writes   │ │
│  │ (recovery_       │  │  successful AND failed recovery cases    │ │
│  │  playbook)       │  │  for Strategist to learn from            │ │
│  └──────────────────┘  └──────────────────────────────────────────┘ │
│  ┌──────────────────┐  ┌──────────────────────────────────────────┐ │
│  │ KB4: Customer     │  │  Customer behavior patterns, segment    │ │
│  │ Context           │  │  preferences, and channel affinities    │ │
│  └──────────────────┘  └──────────────────────────────────────────┘ │
│                                                                      │
│  Embedding Model: gemini-embedding-001 (3072-dim)                   │
│  Similarity: Cosine | Cloud: AWS us-east-1 (Serverless)             │
└──────────────────────────────────────────────────────────────────────┘
```

### Database Schema (Entity-Relationship)

```
┌──────────────┐       ┌──────────────────┐       ┌────────────────┐
│  customers   │       │  transactions    │       │recovery_actions│
├──────────────┤       ├──────────────────┤       ├────────────────┤
│ id (PK)      │◄──────│ customer_id (FK) │       │ id (PK)        │
│ name         │       │ id (PK)          │◄──────│ transaction_id │
│ email        │       │ razorpay_order_id│       │ agent          │
│ phone        │       │ amount           │       │ action         │
│ segment      │       │ product_name     │       │ details (JSONB)│
│ lifetime_val │       │ status           │       │ rag_citations  │
│ pref_language│       │ failure_reason   │       │ duration_ms    │
│ pref_channel │       │ error_code       │       │ created_at     │
│ on_dnd       │       │ recovery_status  │       └────────────────┘
│ opted_out    │       │ recovery_amount  │
│ is_live_demo │       │ attempt_count    │       ┌────────────────┐
└──────────────┘       │ is_outage_related│       │ agent_debates  │
                       │ is_live_demo     │       ├────────────────┤
                       │ recovered_at     │       │ id (PK)        │
                       └──────────────────┘       │ transaction_id │
                              │                   │ proposer       │
                              │                   │ reviewer       │
                 ┌────────────┤                   │ objection      │
                 │            │                   │ resolution     │
        ┌────────┴──────┐  ┌──┴──────────────┐   │ citation       │
        │promise_to_pay │  │channel_messages │   └────────────────┘
        ├───────────────┤  ├─────────────────┤
        │ id (PK)       │  │ id (PK)         │   ┌────────────────┐
        │ transaction_id│  │ transaction_id  │   │   ab_tests     │
        │ customer_id   │  │ customer_id     │   ├────────────────┤
        │ promise_date  │  │ channel         │   │ id (PK)        │
        │ promise_amount│  │ language        │   │ failure_type   │
        │ status        │  │ message_content │   │ variant_a/b    │
        │ fulfilled_at  │  │ payment_link_url│   │ successes/trial│
        └───────────────┘  │ external_id     │   │ p_value        │
                           │ status          │   │ winner         │
                           └─────────────────┘   └────────────────┘

7 Tables | 5 with Supabase Realtime | 7 Optimized Indexes
```

---

## 🤖 The 7 AI Agents

RecoverAI deploys a **swarm of 7 autonomous AI agents** orchestrated as a **LangGraph StateGraph DAG**. Each agent has a specialized role, its own Gemini LLM instance, and access to domain-specific RAG knowledge bases.

| # | Agent | Icon | Role | Intelligence |
|---|---|---|---|---|
| 1 | **Sentinel** | 🛡️ | Detection & Triage | Multi-dimensional urgency scoring (amount × LTV × recency × recoverability), failure fingerprinting for deduplication, bank outage correlation |
| 2 | **Diagnostician** | 🔬 | Root Cause Analysis | RAG-powered error code lookup (KB1), bank outage radar (correlation across transactions), Gemini LLM diagnosis with confidence scoring |
| 3 | **Strategist** | 🎯 | Recovery Planning | Gemini AI strategy inference, RAG playbook retrieval (KB3), Thompson Sampling A/B testing, dynamic incentive generation, AI voice script composition |
| 4 | **Compliance Officer** | ⚖️ | 8-Check Guardrail Gate | Opt-out, DND, time window, retry limit, frequency cap, cool-off, dispute, high-value advisory — with Gemini-powered inter-agent debates and RBI/TRAI legal citations (KB2) |
| 5 | **Executor** | ⚡ | Action Execution | MCP tool-calling across 2 servers (12 tools), real Razorpay payment link generation, omni-channel message dispatch (WhatsApp, SMS, Email, Voice, Auto-Retry) |
| 6 | **Analyst** | 📊 | Learning & Optimization | Post-recovery RAG playbook updates, A/B test statistics with statistical significance detection, Gemini-powered pattern analysis, reinforcement learning loop |
| 7 | **Conversational Agent** | 💬 | Two-Way WhatsApp AI | Real-time Gemini NLU intent classification (6 intents), promise-to-pay date extraction (Hindi/Hinglish/English), empathetic context-aware reply generation, auto-recovery confirmation |

### Agent Communication Flow

```
                    ┌──────────────────────────────────┐
                    │   LangGraph StateGraph (DAG)     │
                    │                                  │
                    │   Entry ──► Sentinel ──► Diagnostician
                    │                             │
                    │                        Strategist
                    │                             │
                    │                        Compliance
                    │                        /        \
                    │                 approved      blocked
                    │                    │              │
                    │              Executor          Analyst ──► END
                    │                    │
                    │               Analyst ──► END
                    └──────────────────────────────────┘
```

---

## 🔧 MCP Servers — 12 Tools

RecoverAI implements the **Model Context Protocol (MCP)** — the emerging open standard for AI agent tool-calling. Two MCP servers expose 12 tools that agents invoke autonomously.

### Razorpay MCP Server (`razorpay-recovery`) — 7 Tools

| Tool | Description | API |
|---|---|---|
| `tool_create_payment_link` | Generate 1-click recovery payment links with customer prefill | Razorpay Payment Links API |
| `tool_create_order` | Create Razorpay orders for checkout recovery | Razorpay Orders API |
| `tool_fetch_payment_details` | Fetch real-time payment status for confirmation | Razorpay Payments API |
| `tool_fetch_order_payments` | List all payment attempts for an order | Razorpay Orders API |
| `tool_create_subscription` | Create subscriptions for mandate recovery | Razorpay Subscriptions API |
| `tool_create_invoice` | Generate B2B invoices for overdue recovery | Razorpay Invoices API |
| `tool_list_failed_payments` | Query failed payments in a date range | Razorpay Payments API |

### Communications MCP Server (`comms-recovery`) — 5 Tools

| Tool | Description | Provider |
|---|---|---|
| `tool_send_whatsapp` | Send real WhatsApp messages with payment links | Wabery (WhatsApp Cloud API) |
| `tool_send_sms` | Send SMS with auto-fallback chain (Fast2SMS → MSG91 → Twilio) | Multi-provider smart router |
| `tool_send_email` | Send styled HTML transactional emails | Resend |
| `tool_make_voice_call` | AI-powered voice calls with dynamic Hinglish TTS | Twilio (Twimlet TTS) |
| `tool_check_dnd_status` | Check TRAI DND registry status | Supabase (Customer DB) |

---

## 🧠 RAG Knowledge Engine (4 Knowledge Bases)

RecoverAI uses **Retrieval-Augmented Generation (RAG)** with **Pinecone** as the vector database and **Google's gemini-embedding-001** (3072-dimensional) for semantic embeddings.

| KB | Namespace | Agent Consumer | Documents | Type |
|---|---|---|---|---|
| **KB1** | `error_codes` | Diagnostician | 24 Razorpay error codes with bank-specific context | Static (ingested once) |
| **KB2** | `compliance` | Compliance Officer | 10 RBI/TRAI/Consumer Protection regulations | Static (ingested once) |
| **KB3** | `recovery_playbook` | Strategist | Successful & failed recovery case studies | **Self-evolving** (Analyst writes after every case) |
| **KB4** | `customer_context` | Sentinel | Customer behavior patterns & preferences | **Self-evolving** (populated during batch) |

### Key RAG Innovation: Self-Evolving Playbook (KB3)

Unlike static rule-based systems, RecoverAI's **KB3: Recovery Playbook** is a **self-evolving knowledge base** that learns from every recovery attempt:

1. **Analyst Agent** writes every case outcome (success AND failure) as a document into KB3
2. **Strategist Agent** queries KB3 for similar past cases before planning strategy
3. Over time, the system builds **institutional memory** — what works for which failure type, bank, segment, channel, language, and amount range
4. Failed strategies are also stored so the Strategist learns **what NOT to do**

This creates a **reinforcement learning loop** where the system continuously improves without human intervention.

---

## 📡 Omni-Channel Communication Stack

RecoverAI supports **6 real communication channels** with intelligent routing:

```
                    ┌────────────────────────────────────┐
                    │    Smart Channel Router             │
                    │                                    │
                    │  ┌─ WhatsApp (Wabery Cloud API)    │ ← Two-way, Real-time AI replies
                    │  ├─ SMS (Fast2SMS → MSG91 → Twilio)│ ← 3-provider fallback chain
                    │  ├─ Email (Resend)                  │ ← Styled HTML with payment CTA
                    │  ├─ Voice (Twilio Twimlet TTS)      │ ← Dynamic Hinglish AI voice calls
                    │  ├─ Auto-Retry (Razorpay)           │ ← Silent payment link regeneration
                    │  └─ Payment Link (Razorpay)         │ ← 1-click recovery links
                    │                                    │
                    │  Language: Hindi / Hinglish / English│
                    │  DND-aware | Time-window enforced   │
                    └────────────────────────────────────┘
```

### Multi-Language Support

| Language | Geo-Target Cities | Template Example |
|---|---|---|
| **Hinglish** | Mumbai, Delhi, Pune, Noida, Gurgaon, Ahmedabad | "Aapka ₹4,299 ka payment fail ho gaya. Yahan se complete karein" |
| **Hindi** | Lucknow, Jaipur, Varanasi, Bhopal, Patna, Indore | "आपका ₹4,299 का भुगतान प्रोसेस नहीं हो पाया" |
| **English** | Bangalore, Chennai, Hyderabad, Kolkata, Kochi | "Your payment of ₹4,299 couldn't be processed" |

---

## 🔬 A/B Testing with Thompson Sampling

RecoverAI uses **Bayesian Thompson Sampling** for multi-armed bandit A/B testing — a mathematically optimal exploration-exploitation strategy that converges faster than traditional A/B tests:

```
┌──────────────────────────────────────────────────────────────┐
│               Thompson Sampling A/B Engine                    │
│                                                               │
│  For each failure_type:                                       │
│    1. Maintain Beta(α, β) distributions for each variant      │
│    2. Sample from each distribution                           │
│    3. Select variant with highest sample                      │
│    4. After execution, update α (success) or β (failure)      │
│    5. Significance test: >30 trials + >10% difference         │
│                                                               │
│  Active Experiments:                                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ card_expired:        WhatsApp vs SMS                     │ │
│  │ checkout_abandoned:  WhatsApp vs Email                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  Winner auto-promotes to default strategy                    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎬 5 Live Demo Scenarios

Each scenario triggers a **real end-to-end recovery flow** — agents process in real-time, send actual WhatsApp/SMS/Email/Voice to your phone, and generate real Razorpay payment links.

| # | Scenario | Failure | Agent Path | Real Channel |
|---|---|---|---|---|
| 1 | 💳 **Card Expired** | `card_expired` | Full 6-agent → WhatsApp with payment link | Real WhatsApp message arrives |
| 2 | 📄 **B2B Invoice Overdue** | `invoice_overdue` | 6-agent → Voice Call (Hinglish AI TTS) + Email | Real phone call + email arrives |
| 3 | 🛒 **Checkout Abandoned** | `checkout_abandoned` | 6-agent → Email first + WhatsApp follow-up + coupon | Real email with dynamic discount |
| 4 | ❌ **Opted-Out Customer** | `card_expired` + `opted_out=true` | 6-agent → Compliance BLOCKS ALL → Gemini debate | Agent debate with legal citation |
| 5 | 🏦 **Bank Decline / Outage** | `bank_decline` | 6-agent → Auto-retry + outage radar correlation | Real WhatsApp with retry link |

### Razorpay Checkout Integration

RecoverAI features **native Razorpay Checkout integration** — the frontend opens a real Razorpay payment popup. When payment fails (intentionally for demo), the `payment.failed` event automatically triggers the 6-agent swarm pipeline.

---

## 💬 Two-Way WhatsApp — Conversational Recovery

RecoverAI doesn't just send messages — it **understands and responds** to customer replies in real-time using Gemini-powered Natural Language Understanding:

### 6 Customer Intent Categories

| Intent | Example Messages | AI Action |
|---|---|---|
| `promise_to_pay` | "kal pay karunga", "10 sept ko", "next Friday", "salary ke baad" | Extract date (Hindi/Hinglish/English), create promise in DB, schedule reminder |
| `payment_done` | "already paid", "ho gaya", "kar diya" | Mark recovered, trigger Analyst learning, confetti! |
| `will_pay_now` | "send link", "abhi karta hu" | Fetch latest Razorpay link, send instantly |
| `need_help` | "why did it fail?", "kya hua?" | Explain failure reason, offer alternatives |
| `opt_out` | "STOP", "don't message" | Respect opt-out, update DB, block further comms |
| `other` | "hello", "thanks" | Friendly response with payment link |

### Promise-to-Pay Scheduler Daemon

A background daemon (`reminder_scheduler.py`) runs every 30 seconds, checking for promises whose `promise_date` has arrived:

- Fetches the latest Razorpay payment link from `channel_messages`
- Generates a friendly Hinglish reminder
- Dispatches via the customer's preferred channel (WhatsApp/Email/SMS)
- Marks the promise as fulfilled and logs the complete audit trail

---

## 📊 Real-Time Dashboard

A full-featured **React 18 dashboard** with real-time updates via **Supabase Realtime**:

| Component | Description |
|---|---|
| **Metric Cards** | At-risk, processing, recovered, exceptions — live counters with animated transitions |
| **Live Agent Feed** | Real-time scrolling feed of agent actions (Sentinel → Diagnostician → ...) with duration badges |
| **Swarm Topology** | Animated D3.js network graph showing agent interconnections |
| **Recovery Funnel** | D3-Sankey visualization: At Risk → Detected → Recovered / Exception |
| **Pattern Radar** | Bank outage detection, failure clusters, payment rail analysis, high-value alerts |
| **Pattern Deep Dive** | Comprehensive multi-dimensional failure analytics with bank health status, root cause breakdown, payment rail performance |
| **Live Demo Buttons** | One-click scenario triggers with Razorpay Checkout popup integration |
| **Promise Tracker** | Real-time promise-to-pay monitoring with status badges and countdown timers |
| **A/B Test Results** | Live experiment tracking with variant performance comparison |
| **Language Stats** | Recovery performance breakdown by Hindi/Hinglish/English |
| **Agent Debate View** | Full transparency into Strategist ↔ Compliance debates with legal citations |
| **Exception Report** | Blocked transactions with compliance reasons and debate records |
| **Transaction Deep Dive** | Per-transaction agent timeline with all 6 agent outputs |
| **War Room** | Emergency command center for bank outage management |
| **PDF Audit Report** | Downloadable compliance audit report (WeasyPrint HTML → PDF) |
| **Cover Page** | Branded landing page for demo presentations |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.11 + FastAPI | High-performance async REST API |
| **Agent Orchestration** | LangGraph StateGraph | Directed acyclic graph (DAG) for multi-agent workflows |
| **LLM** | Gemini 3.1 Flash Lite | Sub-3s latency inference for real-time agent decisions |
| **Embeddings** | gemini-embedding-001 | 3072-dimensional embeddings for semantic search |
| **Tool Protocol** | MCP (Model Context Protocol) | Standardized AI agent tool-calling interface |
| **Vector Database** | Pinecone (Serverless) | 4-namespace RAG knowledge engine |
| **Database** | Supabase (PostgreSQL) | Cloud-native relational DB with Realtime pub/sub |
| **Payments** | Razorpay (Test Mode) | Payment links, orders, subscriptions, invoices, webhooks |
| **WhatsApp** | Wabery (Cloud API) | Live two-way bidirectional WhatsApp messaging |
| **SMS** | Fast2SMS + MSG91 + Twilio | 3-provider fallback chain for India SMS delivery |
| **Email** | Resend | Transactional email with styled HTML templates |
| **Voice** | Twilio (Twimlet TTS) | Dynamic Hinglish AI voice call reminders |
| **Frontend** | React 18 + Vite | Single-page application with hot module replacement |
| **Visualization** | D3.js + Recharts + Framer Motion | Interactive charts, Sankey diagrams, network graphs |
| **Realtime** | Supabase Realtime (WebSocket) | Live dashboard updates without polling |
| **PDF** | WeasyPrint + Jinja2 | Compliance audit report generation |
| **State Management** | React Hooks + Axios | Lightweight data fetching with custom hooks |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Free accounts on: Supabase, Pinecone, Razorpay (test mode), Twilio, Wabery, Resend, Google AI Studio

### 1. Clone & Setup

```bash
git clone https://github.com/Gagan202005/recover-ai.git
cd recover-ai
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Install Dependencies

```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend
cd ../frontend && npm install
```

### 3. Database Setup

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Run `backend/schema.sql` in the Supabase SQL Editor
3. This creates 7 tables with Realtime enabled and optimized indexes

### 4. Ingest RAG Documents (One-Time)

```bash
cd backend && python -m rag.ingest
```

This creates the Pinecone index and ingests 24 error codes + 10 compliance rules.

### 5. Run Batch Processing (One-Time, Pre-Demo)

```bash
cd backend && python -m simulation.batch_runner
```

This generates 50 customers + 200 transactions, processes them through the 6-agent swarm, and trains the RAG playbook.

### 6. Start Development Servers

```bash
# Terminal 1 — Backend
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

### 7. (Optional) Webhook Tunnel

```bash
ngrok http 8000
```

Set the ngrok URL in your Razorpay Dashboard → Webhooks → `https://your-ngrok.ngrok.io/api/webhooks/razorpay`

---

## 📁 Project Structure

```
recover-ai/
├── backend/
│   ├── agents/                     # 7 AI Agent Modules
│   │   ├── sentinel.py             # Agent 1: Detection & Triage
│   │   ├── diagnostician.py        # Agent 2: RAG Root Cause Analysis
│   │   ├── strategist.py           # Agent 3: Gemini AI Strategy + A/B Testing
│   │   ├── compliance.py           # Agent 4: 8-Check Guardrail Gate + Debates
│   │   ├── executor.py             # Agent 5: MCP Tool Execution
│   │   ├── analyst.py              # Agent 6: Learning & Optimization
│   │   ├── conversational_agent.py # Agent 7: Two-Way WhatsApp AI
│   │   ├── swarm.py                # LangGraph StateGraph Orchestrator
│   │   └── state.py                # Shared Agent State Schema
│   ├── mcp_servers/                # Model Context Protocol Servers
│   │   ├── razorpay_server.py      # 7 Razorpay payment tools
│   │   └── comms_server.py         # 5 communication tools
│   ├── rag/                        # RAG Knowledge Engine
│   │   ├── pinecone_client.py      # 4-namespace vector search
│   │   ├── embeddings.py           # gemini-embedding-001 wrapper
│   │   ├── ingest.py               # Document ingestion pipeline
│   │   └── data/                   # Knowledge base source files
│   │       ├── error_codes.json    # 24 Razorpay error codes
│   │       └── compliance_rules.json # 10 RBI/TRAI regulations
│   ├── channels/                   # Multi-Channel Communication
│   │   ├── razorpay_client.py      # Razorpay SDK wrapper
│   │   ├── wabery_client.py        # WhatsApp Cloud API (Wabery)
│   │   ├── wabery_listener.py      # Two-Way WhatsApp Polling Listener
│   │   ├── twilio_client.py        # SMS + Voice (Twilio)
│   │   ├── fast2sms_client.py      # Quick SMS (India, no DLT)
│   │   ├── msg91_client.py         # SMS + WhatsApp (MSG91 CPaaS)
│   │   ├── email_client.py         # Transactional Email (Resend)
│   │   ├── sms_router.py           # Smart 3-provider SMS fallback
│   │   └── message_templates.py    # Hindi/Hinglish/English templates
│   ├── api/                        # FastAPI REST Endpoints
│   │   ├── dashboard.py            # Metrics, agent feed, patterns, A/B tests
│   │   ├── simulation.py           # Live demo + Razorpay Checkout flow
│   │   ├── transactions.py         # Transaction CRUD + deep dive
│   │   ├── reports.py              # PDF audit report generation
│   │   └── webhooks.py             # Razorpay + Twilio + Wabery webhooks
│   ├── simulation/                 # Demo & Testing
│   │   ├── data_generator.py       # 50 customers + 200 transactions
│   │   ├── batch_runner.py         # Full swarm batch processor
│   │   ├── live_scenarios.py       # 5 live demo scenarios
│   │   └── reminder_scheduler.py   # Promise-to-pay follow-up daemon
│   ├── reports/                    # Audit Report Generation
│   │   └── pdf_generator.py        # WeasyPrint HTML → PDF
│   ├── main.py                     # FastAPI app + background services
│   ├── config.py                   # Pydantic settings loader
│   ├── database.py                 # Supabase client + helpers
│   ├── schema.sql                  # 7 tables + indexes + Realtime
│   ├── requirements.txt            # Python dependencies
│   └── test_backend.py             # Comprehensive test suite
├── frontend/
│   ├── src/
│   │   ├── components/             # 15 React Components
│   │   │   ├── MetricCards.jsx     # Dashboard metric cards
│   │   │   ├── LiveAgentFeed.jsx   # Real-time agent action stream
│   │   │   ├── LiveDemoButtons.jsx # 5 scenario trigger buttons
│   │   │   ├── SwarmTopology.jsx   # D3.js agent network graph
│   │   │   ├── PatternCards.jsx    # Failure pattern alerts
│   │   │   ├── PatternDeepDive.jsx # Multi-dimensional analytics
│   │   │   ├── PromiseTracker.jsx  # Promise-to-pay monitor
│   │   │   ├── ABTestResults.jsx   # A/B test dashboard
│   │   │   ├── LanguageStats.jsx   # Multi-language performance
│   │   │   ├── AgentDebateView.jsx # Compliance debate viewer
│   │   │   ├── ExceptionReport.jsx # Exception queue
│   │   │   ├── TransactionDeepDive.jsx # Per-transaction timeline
│   │   │   ├── WarRoom.jsx         # Bank outage command center
│   │   │   ├── CoverPage.jsx       # Presentation landing page
│   │   │   └── Confetti.jsx        # Recovery celebration animation
│   │   ├── hooks/                  # Custom React hooks
│   │   ├── utils/                  # Utility functions
│   │   ├── App.jsx                 # Main app with routing
│   │   └── index.css               # Global styles
│   ├── index.html                  # Entry point
│   ├── vite.config.js              # Vite configuration
│   └── package.json                # Node dependencies
├── .env.example                    # Environment variable template
├── Makefile                        # Development shortcuts
└── README.md                       # This file
```

---

## 🔑 Key Technical Innovations

### 1. Self-Evolving RAG Playbook
The Analyst agent writes every recovery outcome (success AND failure) into Pinecone KB3. The Strategist agent queries this before planning. Over time, the system builds **institutional memory** — a living playbook that improves with every transaction.

### 2. Inter-Agent Debates with Legal Citations
When the Compliance Officer blocks a recovery action, it doesn't just say "no" — it generates a **Gemini-powered legal debate** with specific RBI/TRAI regulation citations, creating a full audit trail for regulatory compliance.

### 3. Thompson Sampling for Channel Optimization
Instead of static A/B tests, RecoverAI uses **Bayesian Thompson Sampling** — a multi-armed bandit algorithm that dynamically balances exploration vs. exploitation, converging to the optimal channel faster.

### 4. Multi-Provider SMS Fallback Chain
SMS delivery in India is notoriously unreliable. RecoverAI implements a **3-provider fallback chain**: Fast2SMS → MSG91 → Twilio, ensuring maximum delivery rate for payment recovery messages.

### 5. Real-Time Bidirectional WhatsApp AI
Not just outbound messages — RecoverAI **continuously polls** for incoming WhatsApp replies (every 3 seconds), classifies intent with Gemini NLU, and responds with context-aware empathetic replies — all in real-time.

### 6. Bank Outage Radar
The Diagnostician agent correlates failures across transactions to detect **bank gateway outages** (≥4 failures from the same bank in 30 minutes), automatically switching to delayed auto-retry strategies.

### 7. Compliance-First Architecture
Every recovery action passes through **8 regulatory checks** before execution. The system is designed to be fully compliant with RBI, TRAI, and Consumer Protection Act 2019 regulations.

---

## 📈 Background Services

RecoverAI starts **2 autonomous background daemons** on boot:

| Service | Interval | Purpose |
|---|---|---|
| **Wabery WhatsApp Polling Listener** | Every 3 seconds | Polls for new incoming WhatsApp messages, processes with Gemini AI, dispatches real-time replies |
| **Promise-to-Pay Reminder Scheduler** | Every 30 seconds | Checks for due promise dates, crafts personalized reminders, dispatches via preferred channel |

Both services are started automatically via **FastAPI lifespan** hooks — no separate process management needed.

---

## 💰 Total Cost: ₹0

All services used on **free tier**:

| Service | Free Tier |
|---|---|
| Supabase | 500 MB database, 2 GB storage, Realtime included |
| Pinecone | 100K vectors, unlimited reads |
| Razorpay | Unlimited test mode transactions |
| Twilio | $15 free trial credit (SMS + Voice) |
| Wabery | Free sandbox WhatsApp |
| Resend | 3,000 emails/month |
| Google AI | Free Gemini API (rate-limited) |
| Fast2SMS | Free tier SMS credits |
| MSG91 | Free trial SMS credits |

---

## 🏆 Why This Should Win

| Criterion | RecoverAI Delivery |
|---|---|
| **Innovation** | 7 autonomous AI agents with self-evolving RAG, inter-agent debates, Thompson Sampling, and conversational recovery |
| **Completeness** | End-to-end: detection → diagnosis → strategy → compliance → execution → learning → two-way chat |
| **Real Integration** | Live Razorpay payment links, real WhatsApp/SMS/Email/Voice to your phone |
| **Compliance** | 8-check guardrail gate with RBI/TRAI citations and Gemini-powered legal debates |
| **Scalability** | Serverless architecture (Supabase + Pinecone + FastAPI async) |
| **Intelligence** | Every agent uses Gemini LLM + domain-specific RAG knowledge bases |
| **UX** | Professional React dashboard with D3.js visualizations, Supabase Realtime, and Framer Motion |
| **Cost** | ₹0 total — all free tiers |

---

## 📜 API Reference

### Dashboard
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/metrics` | Top-level recovery metrics |
| `GET` | `/api/dashboard/agent-feed` | Live agent action stream |
| `GET` | `/api/dashboard/funnel` | Recovery funnel (Sankey) data |
| `GET` | `/api/dashboard/patterns` | Detected failure patterns |
| `GET` | `/api/dashboard/patterns/detailed` | Multi-dimensional analytics |
| `GET` | `/api/dashboard/ab-tests` | A/B test experiment results |
| `GET` | `/api/dashboard/language-stats` | Performance by language |

### Simulation & Live Demo
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/simulation/scenarios` | List all 5 demo scenarios |
| `POST` | `/api/simulation/trigger/{scenario}` | Trigger a live scenario |
| `POST` | `/api/simulation/create-checkout-order/{scenario}` | Create Razorpay Checkout order |
| `POST` | `/api/simulation/report-gateway-failure` | Report Razorpay payment failure |
| `POST` | `/api/simulation/report-gateway-success` | Report payment success |

### Webhooks
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/webhooks/razorpay` | Razorpay payment events |
| `POST` | `/api/webhooks/twilio/whatsapp` | Twilio WhatsApp incoming |
| `POST/GET` | `/api/webhooks/wabery` | Wabery WhatsApp incoming |

### System
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | System info |
| `GET` | `/api/health` | Health check with background service status |
| `GET` | `/api/mcp/servers` | List MCP servers and 12 tools |

---

## 👤 Built By

**Gagan Singhal** — Full-stack AI Engineer

Built for **Razorpay Buildathon 2025** | Track 03: AI Revenue Recovery

---

<p align="center">
  <em>RecoverAI — Because every failed payment is recoverable revenue.</em>
</p>
