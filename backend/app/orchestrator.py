import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from .models import DisputeCase, EvidenceItem, InvestigationRun, DraftPacket
from .evidence_retriever import (
    retrieve_bank_transaction_evidence,
    retrieve_bank_rules_evidence,
    retrieve_store_order_evidence,
    retrieve_store_refund_evidence,
    retrieve_store_messages_evidence
)
from .eligibility_engine import evaluate_eligibility_and_reasoning
from .packet_agent import assemble_draft_packet

def orchestrate_investigation(db: Session, dispute_id: str) -> Dict[str, Any]:
    """
    Orchestrator Agent.
    Responsibilities:
    - Coordinates retrieval tools across Bank Core and Store Commerce.
    - Records tool execution log.
    - Runs deterministic eligibility checks.
    - Manages draft packet generation.
    - Safely stops if missing evidence, refund detected, or outside window.
    """
    dispute = db.query(DisputeCase).filter(DisputeCase.id == dispute_id).first()
    if not dispute:
        raise ValueError(f"Dispute {dispute_id} does not exist.")

    plan_steps = [
        "1. Plan investigation workflow based on dispute reason",
        "2. Retrieve Bank core ledger records for transaction validation",
        "3. Retrieve Bank dispute regulations and filing deadline window",
        "4. Retrieve Merchant store order and fulfillment confirmation",
        "5. Search Merchant records for pre-existing refunds or cancellations",
        "6. Retrieve Merchant-Customer communication logs",
        "7. Execute deterministic financial eligibility rules",
        "8. Assemble structured draft evidence packet if eligible"
    ]

    execution_log: List[Dict[str, Any]] = []

    # Clean previous evidence for a fresh investigation run
    db.query(EvidenceItem).filter(EvidenceItem.dispute_id == dispute.id).delete()
    db.commit()

    # Step 2: Bank Transaction
    bank_evi = retrieve_bank_transaction_evidence(db, dispute, execution_log)

    # Step 3: Bank Rules
    rules_evi = retrieve_bank_rules_evidence(db, dispute, dispute.currency, execution_log)

    # Step 4: Store Order
    order_evi = retrieve_store_order_evidence(db, dispute, execution_log)

    # Step 5: Store Refund
    refund_evi = retrieve_store_refund_evidence(db, dispute, execution_log)

    # Step 6: Store Messages
    msg_evis = retrieve_store_messages_evidence(db, dispute, dispute.order_id, execution_log)
    db.commit()

    # Fetch all newly saved evidence items
    all_evidence = db.query(EvidenceItem).filter(EvidenceItem.dispute_id == dispute.id).all()

    # Step 7: Deterministic Eligibility & Reasoning
    eligibility_result = evaluate_eligibility_and_reasoning(dispute, all_evidence)

    # Update Dispute Case Status
    new_status = eligibility_result["status"]
    dispute.status = new_status
    dispute.eligibility_decision = eligibility_result
    dispute.provisional_credit_flag = eligibility_result.get("provisional_credit_flag", False)
    dispute.is_refunded_flag = eligibility_result.get("is_refunded_flag", False)
    db.commit()

    # Step 8: Assemble Draft Packet if eligible or draftable
    draft_packet_id = None
    if new_status in ["READY_FOR_DRAFT", "UNDER_REVIEW", "NEEDS_MORE_EVIDENCE"]:
        pkt = assemble_draft_packet(db, dispute, all_evidence, eligibility_result)
        draft_packet_id = pkt.id

    # Record Investigation Run
    run_record = InvestigationRun(
        id=f"RUN-{uuid.uuid4().hex[:8].upper()}",
        dispute_id=dispute.id,
        plan_steps=plan_steps,
        tool_executions=execution_log,
        decision_status=new_status,
        decision_summary=eligibility_result["decision_summary"],
        missing_requirements=eligibility_result.get("missing_requirements", []),
        recommended_action=eligibility_result["recommended_action"],
        confidence_score=eligibility_result.get("confidence_score", 1.0)
    )
    db.add(run_record)
    db.commit()

    return {
        "dispute_id": dispute.id,
        "run_id": run_record.id,
        "status": new_status,
        "decision_summary": eligibility_result["decision_summary"],
        "plan_steps": plan_steps,
        "tool_executions": execution_log,
        "missing_requirements": eligibility_result.get("missing_requirements", []),
        "recommended_action": eligibility_result["recommended_action"],
        "confidence_score": eligibility_result.get("confidence_score", 1.0),
        "draft_packet_id": draft_packet_id,
        "evidence_items_count": len(all_evidence)
    }
