"""
RecoverAI — FastAPI Main App
Entry point: registers all routes, handles startup, CORS.
Starts background services (Wabery polling listener + Reminder scheduler) on boot.
"""

import sys
import os
import asyncio
from contextlib import asynccontextmanager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.dashboard import router as dashboard_router
from api.transactions import router as transactions_router
from api.simulation import router as simulation_router
from api.reports import router as reports_router
from api.webhooks import router as webhooks_router
from config import settings


# ── Background Services ──────────────────────────────────────────

_background_tasks = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: start background services on boot, clean up on shutdown."""
    print("\n🚀 RecoverAI Server Starting...")
    print("=" * 60)

    # 1. Start Wabery WhatsApp Polling Listener (two-way messaging)
    try:
        from channels.wabery_listener import start_polling_loop
        polling_task = asyncio.create_task(start_polling_loop())
        _background_tasks.append(polling_task)
        print("✅ Wabery WhatsApp Polling Listener → STARTED")
    except Exception as e:
        print(f"⚠️ Wabery Polling Listener failed to start: {e}")

    # 2. Start Reminder Scheduler Daemon (promise-to-pay follow-ups)
    try:
        from simulation.reminder_scheduler import start_reminder_daemon
        reminder_task = asyncio.create_task(start_reminder_daemon(interval_seconds=30))
        _background_tasks.append(reminder_task)
        print("✅ Reminder Scheduler Daemon (30s interval) → STARTED")
    except Exception as e:
        print(f"⚠️ Reminder Scheduler failed to start: {e}")

    print("=" * 60)
    print(f"🌐 API ready at http://{settings.api_host}:{settings.api_port}")
    print(f"📡 WhatsApp two-way: polling Wabery every 3s")
    print(f"⏰ Reminders: checking due promises every 30s")
    print("=" * 60 + "\n")

    yield  # Server is running

    # Shutdown: cancel background tasks
    print("\n🛑 RecoverAI Server Shutting Down...")
    for task in _background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    print("✅ Background services stopped.\n")


# ── FastAPI App ──────────────────────────────────────────────────

app = FastAPI(
    title="RecoverAI",
    description="AI Revenue Recovery — 6-Agent Swarm with MCP Tool-Calling",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
app.include_router(dashboard_router)
app.include_router(transactions_router)
app.include_router(simulation_router)
app.include_router(reports_router)
app.include_router(webhooks_router)


@app.get("/")
async def root():
    return {
        "name": "RecoverAI",
        "version": "1.0.0",
        "description": "AI Revenue Recovery Agent — Razorpay Buildathon",
        "agents": 6,
        "mcp_servers": 2,
        "mcp_tools": 12,
        "background_services": [
            "Wabery WhatsApp Polling Listener (two-way messaging)",
            "Promise-to-Pay Reminder Scheduler",
        ],
        "features": [
            "6-Agent LangGraph Swarm",
            "RAG with 4 Knowledge Bases",
            "MCP Tool-Calling (Razorpay + Comms)",
            "Real WhatsApp/SMS/Email/Voice",
            "Two-Way WhatsApp + Promise-to-Pay",
            "Multi-Language (Hindi/Hinglish/English)",
            "Agent Debates + Compliance Gate",
            "PDF Audit Report",
        ],
    }


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "env": settings.app_env,
        "background_services": {
            "wabery_polling": len(_background_tasks) >= 1,
            "reminder_scheduler": len(_background_tasks) >= 2,
        },
    }


@app.get("/api/mcp/servers")
async def list_mcp_servers():
    """List registered MCP servers and their tools."""
    return {
        "servers": [
            {
                "name": "razorpay-recovery",
                "description": "Razorpay payment operations via MCP",
                "tools": [
                    {"name": "tool_create_payment_link", "description": "Create a Razorpay payment link"},
                    {"name": "tool_create_order", "description": "Create a Razorpay order"},
                    {"name": "tool_fetch_payment_details", "description": "Fetch payment details"},
                    {"name": "tool_fetch_order_payments", "description": "Fetch order payments"},
                    {"name": "tool_create_subscription", "description": "Create a subscription"},
                    {"name": "tool_create_invoice", "description": "Create an invoice"},
                    {"name": "tool_list_failed_payments", "description": "List failed payments"},
                ],
            },
            {
                "name": "comms-recovery",
                "description": "Multi-channel communications via MCP",
                "tools": [
                    {"name": "tool_send_whatsapp", "description": "Send WhatsApp message"},
                    {"name": "tool_send_sms", "description": "Send SMS"},
                    {"name": "tool_send_email", "description": "Send email"},
                    {"name": "tool_make_voice_call", "description": "Make voice call"},
                    {"name": "tool_check_dnd_status", "description": "Check DND status"},
                ],
            },
        ],
        "total_tools": 12,
    }
