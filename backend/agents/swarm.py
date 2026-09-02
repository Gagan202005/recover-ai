"""
RecoverAI — LangGraph Swarm
Orchestrates the 6-agent pipeline as a StateGraph.
"""

from langgraph.graph import StateGraph, END
from agents.state import RecoveryState
from agents.sentinel import sentinel_node
from agents.diagnostician import diagnostician_node
from agents.strategist import strategist_node
from agents.compliance import compliance_node
from agents.executor import executor_node
from agents.analyst import analyst_node


def should_execute(state: RecoveryState) -> str:
    """After compliance, decide whether to execute or skip to analyst.
    Only 'blocked' skips execution. No human_review verdict exists —
    since we only send payment links (no auto-debit), all non-blocked
    transactions proceed to execution."""
    compliance = state.get("compliance_result", {})
    verdict = compliance.get("verdict", "approved")

    if verdict == "blocked":
        return "analyst"  # Skip executor, go to analyst to log exception
    else:
        return "executor"  # approved or modified → execute recovery action


def build_recovery_graph() -> StateGraph:
    """Build the LangGraph StateGraph for the 6-agent recovery swarm."""

    graph = StateGraph(RecoveryState)

    # Add all 6 agent nodes
    graph.add_node("sentinel", sentinel_node)
    graph.add_node("diagnostician", diagnostician_node)
    graph.add_node("strategist", strategist_node)
    graph.add_node("compliance", compliance_node)
    graph.add_node("executor", executor_node)
    graph.add_node("analyst", analyst_node)

    # Linear flow: Sentinel → Diagnostician → Strategist → Compliance
    graph.add_edge("sentinel", "diagnostician")
    graph.add_edge("diagnostician", "strategist")
    graph.add_edge("strategist", "compliance")

    # Conditional: Compliance → Executor (if approved) or → Analyst (if blocked/held)
    graph.add_conditional_edges("compliance", should_execute, {"executor": "executor", "analyst": "analyst"})

    # Executor → Analyst
    graph.add_edge("executor", "analyst")

    # Analyst → END
    graph.add_edge("analyst", END)

    # Entry point
    graph.set_entry_point("sentinel")

    return graph


# Compile the graph
recovery_graph = build_recovery_graph()
recovery_app = recovery_graph.compile()


async def process_transaction(transaction: dict, customer: dict, is_live: bool = False) -> dict:
    """Process a single transaction through the 6-agent swarm."""

    initial_state: RecoveryState = {
        "transaction_id": transaction["id"],
        "razorpay_order_id": transaction.get("razorpay_order_id", ""),
        "amount": transaction["amount"],
        "currency": transaction.get("currency", "INR"),
        "customer_id": transaction["customer_id"],
        "customer_name": customer.get("name", "Customer"),
        "customer_phone": customer.get("phone", ""),
        "customer_email": customer.get("email", ""),
        "product_name": transaction.get("product_name", "Order"),
        "failure_reason": transaction.get("failure_reason", "unknown"),
        "error_code": transaction.get("error_code", "UNKNOWN"),
        "error_description": transaction.get("error_description", ""),
        "error_source": transaction.get("error_source", "unknown"),
        "bank": transaction.get("bank", "unknown"),
        "method": transaction.get("method", "card"),
        "is_live_demo": is_live,
        "sentinel_output": {},
        "diagnosis": {},
        "strategy": {},
        "compliance_result": {},
        "execution_result": {},
        "analysis": {},
        "debates": [],
        "audit_trail": [],
        "status": "processing",
        "attempt_count": transaction.get("attempt_count", 0) or 0,
        "customer_context": customer or {},
    }

    # Run the graph
    result = await recovery_app.ainvoke(initial_state)
    return result
