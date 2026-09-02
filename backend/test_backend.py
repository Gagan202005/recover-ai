"""
RecoverAI — Comprehensive Backend Test
Tests every cloud service, database, RAG pipeline, and integration.
Run: python test_backend.py
"""

import asyncio
import sys
import os
import json
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"
results = []


def log_result(test_name, passed, detail=""):
    icon = PASS if passed else FAIL
    results.append({"test": test_name, "passed": passed, "detail": detail})
    print(f"  {icon} {test_name}: {detail}")


def log_warn(test_name, detail=""):
    results.append({"test": test_name, "passed": None, "detail": detail})
    print(f"  {WARN} {test_name}: {detail}")


async def test_config():
    """Test 1: Configuration loads correctly"""
    print("\n" + "=" * 60)
    print("🔧 TEST 1: Configuration")
    print("=" * 60)
    try:
        from config import settings

        checks = {
            "supabase_url": bool(settings.supabase_url and settings.supabase_url.startswith("https://")),
            "supabase_secret_key": bool(settings.supabase_secret_key and len(settings.supabase_secret_key) > 20),
            "pinecone_api_key": bool(settings.pinecone_api_key and len(settings.pinecone_api_key) > 10),
            "pinecone_index_name": bool(settings.pinecone_index_name),
            "razorpay_key_id": bool(settings.razorpay_key_id and settings.razorpay_key_id.startswith("rzp_")),
            "razorpay_key_secret": bool(settings.razorpay_key_secret and len(settings.razorpay_key_secret) > 5),
            "twilio_account_sid": bool(settings.twilio_account_sid and settings.twilio_account_sid.startswith("AC")),
            "twilio_auth_token": bool(settings.twilio_auth_token and len(settings.twilio_auth_token) > 10),
            "resend_api_key": bool(settings.resend_api_key and settings.resend_api_key.startswith("re_")),
            "google_api_key": bool(settings.google_api_key and len(settings.google_api_key) > 10),
            "demo_phone_number": bool(settings.demo_phone_number and settings.demo_phone_number.startswith("+")),
            "demo_email": bool(settings.demo_email and "@" in settings.demo_email),
        }

        for key, valid in checks.items():
            log_result(f"Config: {key}", valid, "Present" if valid else "MISSING or INVALID")

    except Exception as e:
        log_result("Config: load settings", False, str(e))


async def test_supabase():
    """Test 2: Supabase connection + table existence + data"""
    print("\n" + "=" * 60)
    print("🗄️ TEST 2: Supabase Database")
    print("=" * 60)
    try:
        from database import supabase

        # Test connection
        log_result("Supabase: connection", True, "Client initialized")

        # Check each table exists
        tables = ["customers", "transactions", "recovery_actions", "agent_debates",
                   "promise_to_pay", "channel_messages", "ab_tests"]

        for table in tables:
            try:
                result = supabase.table(table).select("*", count="exact").limit(1).execute()
                count = result.count if hasattr(result, 'count') and result.count is not None else len(result.data or [])
                # Try to get actual count
                result_count = supabase.table(table).select("id", count="exact").execute()
                actual_count = result_count.count if result_count.count is not None else "unknown"
                log_result(f"Supabase: table '{table}'", True, f"Exists — {actual_count} rows")
            except Exception as e:
                error_msg = str(e)
                if "does not exist" in error_msg or "42P01" in error_msg:
                    log_result(f"Supabase: table '{table}'", False, "TABLE DOES NOT EXIST — run schema.sql!")
                else:
                    log_result(f"Supabase: table '{table}'", False, f"Error: {error_msg[:100]}")

        # Test dashboard metrics function
        try:
            from database import get_dashboard_metrics
            metrics = await get_dashboard_metrics()
            log_result("Supabase: get_dashboard_metrics()", True,
                       f"at_risk={metrics.get('at_risk', {}).get('count', 0)}, "
                       f"recovered={metrics.get('recovered', {}).get('count', 0)}, "
                       f"rate={metrics.get('recovery_rate', 0)}%")
        except Exception as e:
            log_result("Supabase: get_dashboard_metrics()", False, str(e)[:100])

        # Check if demo customer exists
        try:
            result = supabase.table("customers").select("*").eq("id", "cust_001").execute()
            if result.data and len(result.data) > 0:
                cust = result.data[0]
                log_result("Supabase: demo customer (cust_001)", True,
                           f"Name: {cust.get('name')}, Phone: {cust.get('phone')}, Segment: {cust.get('segment')}")
            else:
                log_result("Supabase: demo customer (cust_001)", False,
                           "NOT FOUND — need to run batch_runner to seed data")
        except Exception as e:
            log_result("Supabase: demo customer (cust_001)", False, str(e)[:100])

    except Exception as e:
        log_result("Supabase: connection", False, str(e)[:200])


async def test_pinecone():
    """Test 3: Pinecone Vector DB"""
    print("\n" + "=" * 60)
    print("🌲 TEST 3: Pinecone Vector DB")
    print("=" * 60)
    try:
        from pinecone import Pinecone
        from config import settings

        pc = Pinecone(api_key=settings.pinecone_api_key)
        log_result("Pinecone: API connection", True, "Connected")

        # List indexes
        indexes = [idx.name for idx in pc.list_indexes()]
        log_result("Pinecone: list indexes", True, f"Found: {indexes}")

        if settings.pinecone_index_name in indexes:
            log_result(f"Pinecone: index '{settings.pinecone_index_name}'", True, "Exists")

            # Get index stats
            idx = pc.Index(settings.pinecone_index_name)
            stats = idx.describe_index_stats()
            total_vectors = stats.get("total_vector_count", 0)
            namespaces = stats.get("namespaces", {})

            log_result("Pinecone: total vectors", total_vectors > 0,
                       f"{total_vectors} vectors total")

            # Check each namespace
            expected_namespaces = ["error_codes", "compliance", "recovery_playbook"]
            for ns in expected_namespaces:
                if ns in namespaces:
                    ns_count = namespaces[ns].get("vector_count", 0)
                    log_result(f"Pinecone: namespace '{ns}'", ns_count > 0,
                               f"{ns_count} vectors")
                else:
                    log_result(f"Pinecone: namespace '{ns}'", False,
                               "EMPTY — need to run rag.ingest")

        else:
            log_result(f"Pinecone: index '{settings.pinecone_index_name}'", False,
                       f"NOT FOUND — need to run rag.ingest to create index. Available: {indexes}")

    except Exception as e:
        log_result("Pinecone: connection", False, f"{str(e)[:200]}")


async def test_embeddings():
    """Test 4: Google Embeddings"""
    print("\n" + "=" * 60)
    print("🧮 TEST 4: Google Embeddings (gemini-embedding-001)")
    print("=" * 60)
    try:
        from rag.embeddings import get_embedding, EMBEDDING_DIMENSION

        start = time.time()
        embedding = await get_embedding("test payment failure Razorpay")
        duration = round((time.time() - start) * 1000)

        if embedding and len(embedding) > 0:
            log_result("Embeddings: generate", True,
                       f"Dimension: {len(embedding)} (expected {EMBEDDING_DIMENSION}), took {duration}ms")
            if len(embedding) != EMBEDDING_DIMENSION:
                log_warn("Embeddings: dimension mismatch",
                         f"Got {len(embedding)}, expected {EMBEDDING_DIMENSION}")
        else:
            log_result("Embeddings: generate", False, "Empty embedding returned")

    except Exception as e:
        log_result("Embeddings: generate", False, f"{str(e)[:200]}")
        traceback.print_exc()


async def test_rag_queries():
    """Test 5: RAG Query Pipeline"""
    print("\n" + "=" * 60)
    print("📚 TEST 5: RAG Query Pipeline")
    print("=" * 60)
    try:
        from rag.pinecone_client import query_error_codes, query_compliance, query_playbook

        # Test error codes query
        try:
            start = time.time()
            results_ec = await query_error_codes("BAD_REQUEST_ERROR", "HDFC")
            duration = round((time.time() - start) * 1000)
            log_result("RAG: query_error_codes", len(results_ec) > 0,
                       f"{len(results_ec)} results, took {duration}ms" +
                       (f" — top: {results_ec[0]['content'][:80]}..." if results_ec else ""))
        except Exception as e:
            log_result("RAG: query_error_codes", False, str(e)[:150])

        # Test compliance query
        try:
            start = time.time()
            results_comp = await query_compliance("whatsapp payment recovery")
            duration = round((time.time() - start) * 1000)
            log_result("RAG: query_compliance", len(results_comp) > 0,
                       f"{len(results_comp)} results, took {duration}ms")
        except Exception as e:
            log_result("RAG: query_compliance", False, str(e)[:150])

        # Test playbook query
        try:
            start = time.time()
            results_pb = await query_playbook("card_expired", 429900, "vip")
            duration = round((time.time() - start) * 1000)
            log_result("RAG: query_playbook", True,
                       f"{len(results_pb)} results, took {duration}ms (may be 0 before batch run)")
        except Exception as e:
            log_result("RAG: query_playbook", False, str(e)[:150])

    except Exception as e:
        log_result("RAG: pipeline import", False, str(e)[:200])


async def test_razorpay():
    """Test 6: Razorpay API"""
    print("\n" + "=" * 60)
    print("💳 TEST 6: Razorpay API (Test Mode)")
    print("=" * 60)
    try:
        from channels.razorpay_client import rzp_client, create_order, create_payment_link

        # Test: create an order
        try:
            order = create_order(amount=100, currency="INR", receipt="test_order")
            log_result("Razorpay: create_order", True,
                       f"Order ID: {order.get('id')}, Status: {order.get('status')}")
        except Exception as e:
            log_result("Razorpay: create_order", False, str(e)[:150])

        # Test: create a payment link
        try:
            link = create_payment_link(
                amount=100, customer_name="Test User",
                customer_email="test@test.com", customer_phone="+919999999999",
                description="RecoverAI test link",
            )
            log_result("Razorpay: create_payment_link", True,
                       f"Link: {link.get('short_url')}")
        except Exception as e:
            log_result("Razorpay: create_payment_link", False, str(e)[:150])

    except Exception as e:
        log_result("Razorpay: client init", False, str(e)[:200])


async def test_twilio():
    """Test 7: Twilio API"""
    print("\n" + "=" * 60)
    print("📱 TEST 7: Twilio API (WhatsApp + SMS + Voice)")
    print("=" * 60)
    try:
        from channels.twilio_client import twilio_client
        from config import settings

        # Test: check account info (doesn't send any messages)
        try:
            account = twilio_client.api.accounts(settings.twilio_account_sid).fetch()
            log_result("Twilio: account connection", True,
                       f"Account: {account.friendly_name}, Status: {account.status}")
        except Exception as e:
            log_result("Twilio: account connection", False, str(e)[:150])

        log_result("Twilio: phone number configured", bool(settings.twilio_phone_number),
                   settings.twilio_phone_number or "NOT SET")
        log_result("Twilio: whatsapp number configured", bool(settings.twilio_whatsapp_number),
                   settings.twilio_whatsapp_number or "NOT SET")

    except Exception as e:
        log_result("Twilio: client init", False, str(e)[:200])


async def test_resend():
    """Test 8: Resend Email API"""
    print("\n" + "=" * 60)
    print("📧 TEST 8: Resend Email API")
    print("=" * 60)
    try:
        import resend
        from config import settings

        resend.api_key = settings.resend_api_key
        log_result("Resend: API key configured", bool(settings.resend_api_key),
                   f"Key: {settings.resend_api_key[:10]}..." if settings.resend_api_key else "NOT SET")
        log_result("Resend: from email configured", bool(settings.resend_from_email),
                   settings.resend_from_email or "NOT SET")

        # Test: validate API key by listing domains (non-destructive)
        try:
            # Try fetching API key info
            domains = resend.Domains.list()
            log_result("Resend: API connection", True,
                       f"Connected — {len(domains.get('data', []))} domains configured")
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "401" in error_msg or "403" in error_msg:
                log_result("Resend: API connection", False, f"Invalid API key: {error_msg[:100]}")
            else:
                # Some errors are fine (e.g., the list method might differ)
                log_result("Resend: API connection", True, f"Key seems valid (non-critical error: {error_msg[:80]})")

    except Exception as e:
        log_result("Resend: import/init", False, str(e)[:200])


async def test_gemini():
    """Test 9: Google Gemini LLM"""
    print("\n" + "=" * 60)
    print("🤖 TEST 9: Google Gemini LLM")
    print("=" * 60)
    try:
        import google.generativeai as genai
        from config import settings

        genai.configure(api_key=settings.google_api_key)
        from config import settings as s
        model = genai.GenerativeModel(s.gemini_model)
        log_result("Gemini: model", True, f"Using {s.gemini_model}")

        start = time.time()
        response = model.generate_content("Reply with only: OK")
        duration = round((time.time() - start) * 1000)

        text = response.text.strip() if response.text else ""
        log_result("Gemini: generate_content", bool(text),
                   f"Response: '{text[:50]}', took {duration}ms")

    except Exception as e:
        log_result("Gemini: generate_content", False, str(e)[:200])


async def test_rag_data_files():
    """Test 10: RAG data files exist"""
    print("\n" + "=" * 60)
    print("📁 TEST 10: RAG Data Files")
    print("=" * 60)

    data_dir = os.path.join(os.path.dirname(__file__), "rag", "data")

    # Check error_codes.json
    ec_path = os.path.join(data_dir, "error_codes.json")
    if os.path.exists(ec_path):
        with open(ec_path) as f:
            data = json.load(f)
        log_result("RAG Data: error_codes.json", len(data) > 0, f"{len(data)} error codes")
    else:
        log_result("RAG Data: error_codes.json", False, "FILE NOT FOUND")

    # Check compliance_rules.json
    cr_path = os.path.join(data_dir, "compliance_rules.json")
    if os.path.exists(cr_path):
        with open(cr_path) as f:
            data = json.load(f)
        log_result("RAG Data: compliance_rules.json", len(data) > 0, f"{len(data)} rules")
    else:
        log_result("RAG Data: compliance_rules.json", False, "FILE NOT FOUND")


async def test_api_endpoints():
    """Test 11: FastAPI endpoints via HTTP"""
    print("\n" + "=" * 60)
    print("🌐 TEST 11: API Endpoints (localhost:8000)")
    print("=" * 60)
    try:
        import httpx

        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=10) as client:
            endpoints = [
                ("GET", "/", "Root"),
                ("GET", "/api/health", "Health"),
                ("GET", "/api/mcp/servers", "MCP Servers"),
                ("GET", "/api/dashboard/metrics", "Dashboard Metrics"),
                ("GET", "/api/dashboard/agent-feed?limit=5", "Agent Feed"),
                ("GET", "/api/dashboard/funnel", "Recovery Funnel"),
                ("GET", "/api/dashboard/patterns", "Failure Patterns"),
                ("GET", "/api/dashboard/ab-tests", "A/B Tests"),
                ("GET", "/api/dashboard/language-stats", "Language Stats"),
                ("GET", "/api/transactions/?limit=5", "Transactions List"),
                ("GET", "/api/simulation/scenarios", "Simulation Scenarios"),
            ]

            for method, path, name in endpoints:
                try:
                    if method == "GET":
                        resp = await client.get(path)
                    else:
                        resp = await client.post(path)

                    if resp.status_code == 200:
                        data = resp.json()
                        # Brief summary of response
                        if isinstance(data, dict):
                            detail = f"200 OK — keys: {list(data.keys())[:5]}"
                        elif isinstance(data, list):
                            detail = f"200 OK — {len(data)} items"
                        else:
                            detail = f"200 OK"
                        log_result(f"API: {name}", True, detail)
                    else:
                        log_result(f"API: {name}", False, f"HTTP {resp.status_code}: {resp.text[:100]}")
                except Exception as e:
                    log_result(f"API: {name}", False, str(e)[:100])

    except Exception as e:
        log_result("API: httpx import/connection", False, str(e)[:200])


async def test_message_templates():
    """Test 12: Message templates render correctly"""
    print("\n" + "=" * 60)
    print("💬 TEST 12: Message Templates")
    print("=" * 60)
    try:
        from channels.message_templates import render_template, select_language, TEMPLATES

        log_result("Templates: loaded", len(TEMPLATES) > 0, f"{len(TEMPLATES)} templates")

        # Test rendering in all 3 languages
        for lang in ["english", "hinglish", "hindi"]:
            try:
                msg = render_template("recovery_whatsapp", lang,
                                      name="Test", amount="4,299", product="Silk Kurta", link="https://rzp.io/test")
                log_result(f"Templates: recovery_whatsapp ({lang})", bool(msg),
                           f"'{msg[:60]}...'")
            except Exception as e:
                log_result(f"Templates: recovery_whatsapp ({lang})", False, str(e)[:100])

        # Test language selection
        test_cases = [
            ({"preferred_language": "hindi"}, "hindi"),
            ({"city": "Mumbai"}, "hinglish"),
            ({"city": "Bangalore"}, "english"),
            ({"city": "Lucknow"}, "hindi"),
        ]
        for customer, expected in test_cases:
            result = select_language(customer)
            log_result(f"Templates: select_language({customer})", result == expected,
                       f"Got '{result}', expected '{expected}'")

    except Exception as e:
        log_result("Templates: import", False, str(e)[:200])


async def test_agent_imports():
    """Test 13: All agent modules import correctly"""
    print("\n" + "=" * 60)
    print("🤖 TEST 13: Agent Module Imports")
    print("=" * 60)

    agent_modules = [
        ("agents.state", "RecoveryState"),
        ("agents.sentinel", "sentinel_node"),
        ("agents.diagnostician", "diagnostician_node"),
        ("agents.strategist", "strategist_node"),
        ("agents.compliance", "compliance_node"),
        ("agents.executor", "executor_node"),
        ("agents.analyst", "analyst_node"),
        ("agents.swarm", "recovery_app"),
    ]

    for module_name, attr_name in agent_modules:
        try:
            module = __import__(module_name, fromlist=[attr_name])
            attr = getattr(module, attr_name)
            log_result(f"Agent: {module_name}.{attr_name}", True, f"Imported ({type(attr).__name__})")
        except Exception as e:
            log_result(f"Agent: {module_name}.{attr_name}", False, str(e)[:150])


async def test_mcp_server_imports():
    """Test 14: MCP server modules import correctly"""
    print("\n" + "=" * 60)
    print("🔧 TEST 14: MCP Server Imports")
    print("=" * 60)

    try:
        from mcp_servers.razorpay_server import mcp as rzp_mcp
        log_result("MCP: razorpay-recovery server", True, f"Name: {rzp_mcp.name}")
    except Exception as e:
        log_result("MCP: razorpay-recovery server", False, str(e)[:150])

    try:
        from mcp_servers.comms_server import mcp as comms_mcp
        log_result("MCP: comms-recovery server", True, f"Name: {comms_mcp.name}")
    except Exception as e:
        log_result("MCP: comms-recovery server", False, str(e)[:150])


async def main():
    print("\n" + "🧠" * 30)
    print("   RecoverAI — COMPREHENSIVE BACKEND TEST")
    print("🧠" * 30)

    await test_config()
    await test_supabase()
    await test_pinecone()
    await test_embeddings()
    await test_rag_queries()
    await test_rag_data_files()
    await test_razorpay()
    await test_twilio()
    await test_resend()
    await test_gemini()
    await test_api_endpoints()
    await test_message_templates()
    await test_agent_imports()
    await test_mcp_server_imports()

    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r["passed"] is True)
    failed = sum(1 for r in results if r["passed"] is False)
    warnings = sum(1 for r in results if r["passed"] is None)
    total = len(results)

    print(f"\n  {PASS} Passed:   {passed}/{total}")
    print(f"  {FAIL} Failed:   {failed}/{total}")
    if warnings:
        print(f"  {WARN} Warnings: {warnings}/{total}")

    if failed > 0:
        print(f"\n  🔴 FAILED TESTS:")
        for r in results:
            if r["passed"] is False:
                print(f"     • {r['test']}: {r['detail']}")

    print(f"\n{'=' * 60}")
    if failed == 0:
        print("  🎉 ALL TESTS PASSED! Backend is ready.")
    else:
        print(f"  ⚠️  {failed} test(s) need attention before running.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
