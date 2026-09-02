"""
RecoverAI — API: Reports
PDF audit report generation and download.
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse
from reports.pdf_generator import generate_pdf_report
from database import supabase

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/pdf")
async def download_pdf_report():
    """Generate and download an audit report (PDF or HTML fallback)."""
    # Get all data
    txns = supabase.table("transactions") \
        .select("*, customers(name, segment)") \
        .neq("status", "success") \
        .order("created_at", desc=True) \
        .execute()

    actions = supabase.table("recovery_actions") \
        .select("*") \
        .order("created_at", desc=False) \
        .execute()

    debates = supabase.table("agent_debates").select("*").execute()

    exceptions = supabase.table("transactions") \
        .select("*, customers(name)") \
        .eq("recovery_status", "exception") \
        .execute()

    report_data = {
        "transactions": txns.data or [],
        "actions": actions.data or [],
        "debates": debates.data or [],
        "exceptions": exceptions.data or [],
    }

    filepath = generate_pdf_report(report_data)

    if filepath.endswith(".pdf"):
        return FileResponse(filepath, filename="RecoverAI_Audit_Report.pdf", media_type="application/pdf")
    else:
        return FileResponse(filepath, filename="RecoverAI_Audit_Report.html", media_type="text/html")
