import io
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

from .database import get_db
from .models import (
    BankTransaction, DisputeCase, EvidenceItem, InvestigationRun,
    DraftPacket, ApprovalRecord, BankSubmittedDispute, IndependentVerification,
    TestScenarioResult
)
from .schemas import (
    DisputeCreateRequest, ApprovalRequest, SubmissionRequest,
    InvestigationResultSchema, DashboardStatsSchema
)
from .orchestrator import orchestrate_investigation
from .verifier import independently_verify_submission
from .packet_agent import calculate_packet_hash

router = APIRouter(prefix="/api", tags=["EvidentAI Core API"])

# -------------------------------------------------------------
# 1. Dashboard Metrics
# -------------------------------------------------------------
@router.get("/dashboard/stats", response_model=DashboardStatsSchema)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_txns = db.query(BankTransaction).count()
    open_disputes = db.query(DisputeCase).filter(
        DisputeCase.status.in_(["DRAFT", "READY_FOR_DRAFT", "UNDER_REVIEW"])
    ).count()
    draft_packets = db.query(DraftPacket).count()
    resolved_refunded = db.query(DisputeCase).filter(
        DisputeCase.status.in_(["ALREADY_REFUNDED", "SUBMITTED"])
    ).count()
    requiring_evidence = db.query(DisputeCase).filter(
        DisputeCase.status.in_(["NEEDS_MORE_EVIDENCE", "OUTSIDE_DISPUTE_WINDOW", "BLOCKED"])
    ).count()

    # Status distribution
    cases = db.query(DisputeCase).all()
    distribution: Dict[str, int] = {}
    for c in cases:
        distribution[c.status] = distribution.get(c.status, 0) + 1

    # Recent activity
    runs = db.query(InvestigationRun).order_by(InvestigationRun.created_at.desc()).limit(5).all()
    recent = []
    for r in runs:
        recent.append({
            "id": r.id,
            "dispute_id": r.dispute_id,
            "status": r.decision_status,
            "summary": r.decision_summary,
            "action": r.recommended_action,
            "timestamp": r.created_at.isoformat() if r.created_at else None
        })

    return {
        "total_transactions": total_txns,
        "open_disputes": open_disputes,
        "draft_packets": draft_packets,
        "resolved_or_refunded": resolved_refunded,
        "requiring_evidence": requiring_evidence,
        "status_distribution": distribution,
        "recent_activity": recent
    }

# -------------------------------------------------------------
# 2. Disputes Lifecycle
# -------------------------------------------------------------
@router.post("/disputes")
def create_dispute(payload: DisputeCreateRequest, db: Session = Depends(get_db)):
    """Create a new dispute case after verifying the transaction exists."""
    txn = db.query(BankTransaction).filter(BankTransaction.id == payload.transaction_id).first()
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{payload.transaction_id}' does not exist in bank records."
        )

    dispute_id = f"DISP-{uuid.uuid4().hex[:8].upper()}"
    new_case = DisputeCase(
        id=dispute_id,
        transaction_id=txn.id,
        order_id=txn.order_id,
        user_stated_reason=payload.user_stated_reason,
        user_explanation=payload.user_explanation,
        amount=txn.amount,
        currency=txn.currency,
        status="DRAFT"
    )
    db.add(new_case)
    db.commit()

    # Immediately trigger orchestrator to investigate
    result = orchestrate_investigation(db, new_case.id)
    return {
        "dispute_id": new_case.id,
        "investigation": result
    }

@router.get("/disputes/{dispute_id}")
def get_dispute_details(dispute_id: str, db: Session = Depends(get_db)):
    dispute = db.query(DisputeCase).filter(DisputeCase.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute case not found.")

    evidence = db.query(EvidenceItem).filter(EvidenceItem.dispute_id == dispute_id).all()
    latest_run = db.query(InvestigationRun).filter(InvestigationRun.dispute_id == dispute_id).order_by(InvestigationRun.created_at.desc()).first()
    packet = db.query(DraftPacket).filter(DraftPacket.dispute_id == dispute_id).first()
    approvals = db.query(ApprovalRecord).filter(ApprovalRecord.dispute_id == dispute_id).order_by(ApprovalRecord.timestamp.desc()).all()
    verifications = db.query(IndependentVerification).filter(IndependentVerification.dispute_id == dispute_id).order_by(IndependentVerification.verified_at.desc()).all()

    return {
        "dispute": {
            "id": dispute.id,
            "transaction_id": dispute.transaction_id,
            "order_id": dispute.order_id,
            "user_stated_reason": dispute.user_stated_reason,
            "user_explanation": dispute.user_explanation,
            "amount": dispute.amount,
            "currency": dispute.currency,
            "status": dispute.status,
            "eligibility_decision": dispute.eligibility_decision,
            "provisional_credit_flag": dispute.provisional_credit_flag,
            "is_refunded_flag": dispute.is_refunded_flag,
            "created_at": dispute.created_at.isoformat() if dispute.created_at else None
        },
        "evidence_items": [
            {
                "id": e.id,
                "source_system": e.source_system,
                "source_record_id": e.source_record_id,
                "source_endpoint": e.source_endpoint,
                "retrieval_timestamp": e.retrieval_timestamp.isoformat() if e.retrieval_timestamp else None,
                "item_type": e.item_type,
                "extracted_facts": e.extracted_facts,
                "relevance_explanation": e.relevance_explanation,
                "verification_status": e.verification_status,
                "is_user_allegation": e.is_user_allegation
            } for e in evidence
        ],
        "latest_investigation": {
            "plan_steps": latest_run.plan_steps,
            "tool_executions": latest_run.tool_executions,
            "decision_status": latest_run.decision_status,
            "decision_summary": latest_run.decision_summary,
            "missing_requirements": latest_run.missing_requirements,
            "recommended_action": latest_run.recommended_action,
            "confidence_score": latest_run.confidence_score
        } if latest_run else None,
        "draft_packet": {
            "id": packet.id,
            "packet_version": packet.packet_version,
            "content_hash": packet.content_hash,
            "is_approved": packet.is_approved,
            "approval_timestamp": packet.approval_timestamp.isoformat() if packet.approval_timestamp else None,
            "approver_id": packet.approver_id,
            "packet_data": packet.packet_data
        } if packet else None,
        "approvals": [
            {
                "id": a.id,
                "action": a.action,
                "approver_name": a.approver_name,
                "comments": a.comments,
                "timestamp": a.timestamp.isoformat() if a.timestamp else None
            } for a in approvals
        ],
        "verifications": [
            {
                "id": v.id,
                "bank_dispute_id": v.bank_dispute_id,
                "verification_status": v.verification_status,
                "details": v.details,
                "explanation": v.explanation,
                "verified_at": v.verified_at.isoformat() if v.verified_at else None
            } for v in verifications
        ]
    }

@router.post("/disputes/{dispute_id}/re-investigate")
def re_investigate(dispute_id: str, db: Session = Depends(get_db)):
    """Re-run the orchestrator agent and recalculate findings."""
    return orchestrate_investigation(db, dispute_id)

# -------------------------------------------------------------
# 3. Human Approval Workflow
# -------------------------------------------------------------
@router.post("/disputes/{dispute_id}/approve")
def approve_or_reject_draft(dispute_id: str, payload: ApprovalRequest, db: Session = Depends(get_db)):
    """
    Enforce Human Approval.
    Requires explicit action (APPROVED, REJECTED, RETURNED_FOR_CORRECTION).
    Verifies that the packet has not mutated since approval.
    """
    packet = db.query(DraftPacket).filter(
        DraftPacket.id == payload.packet_id,
        DraftPacket.dispute_id == dispute_id
    ).first()

    if not packet:
        raise HTTPException(status_code=404, detail="Draft packet not found.")

    if packet.packet_version != payload.packet_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Packet version mismatch. Another revision has been generated. Please review the updated draft."
        )

    # Check hash integrity
    computed_hash = calculate_packet_hash(packet.packet_data)
    if computed_hash != packet.content_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cryptographic hash integrity violation. Packet content was altered."
        )

    # Record approval decision
    record = ApprovalRecord(
        id=f"APPR-{uuid.uuid4().hex[:8].upper()}",
        dispute_id=dispute_id,
        packet_id=packet.id,
        packet_version=packet.packet_version,
        action=payload.action,
        approver_name=payload.approver_name,
        comments=payload.comments
    )
    db.add(record)

    dispute = db.query(DisputeCase).filter(DisputeCase.id == dispute_id).first()

    if payload.action == "APPROVED":
        packet.is_approved = True
        packet.approval_timestamp = datetime.now(timezone.utc)
        packet.approver_id = payload.approver_name
        if dispute:
            dispute.status = "APPROVED"
    elif payload.action == "REJECTED":
        packet.is_approved = False
        if dispute:
            dispute.status = "REJECTED"
    elif payload.action == "RETURNED_FOR_CORRECTION":
        packet.is_approved = False
        if dispute:
            dispute.status = "NEEDS_MORE_EVIDENCE"

    db.commit()
    return {
        "status": "SUCCESS",
        "action": payload.action,
        "packet_id": packet.id,
        "is_approved": packet.is_approved
    }

# -------------------------------------------------------------
# 4. Safe Submission & Independent Verification
# -------------------------------------------------------------
@router.post("/disputes/{dispute_id}/submit-to-bank")
def submit_dispute_to_bank(dispute_id: str, payload: SubmissionRequest, db: Session = Depends(get_db)):
    """
    Submit approved dispute packet to the Mock Bank.
    Backend ENFORCES:
    1. Human Approval must exist for this exact packet and hash.
    2. Idempotency Key prevents duplicate network submissions.
    3. Triggers Independent Verification immediately post-submission.
    """
    dispute = db.query(DisputeCase).filter(DisputeCase.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute case not found.")

    packet = db.query(DraftPacket).filter(
        DraftPacket.id == payload.packet_id,
        DraftPacket.dispute_id == dispute_id
    ).first()

    if not packet:
        raise HTTPException(status_code=404, detail="Draft packet not found.")

    # MANDATORY CHECK: Human Approval
    if not packet.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="SUBMISSION FORBIDDEN: This dispute packet has not received explicit human cardholder approval."
        )

    # MANDATORY CHECK: Verify hash hasn't mutated
    if calculate_packet_hash(packet.packet_data) != packet.content_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Packet contents mutated since approval. Re-approval is mandatory."
        )

    # MANDATORY CHECK: Idempotency Key
    existing_submission = db.query(BankSubmittedDispute).filter(
        BankSubmittedDispute.idempotency_key == payload.idempotency_key
    ).first()
    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"DUPLICATE SUBMISSION BLOCKED: Idempotency key '{payload.idempotency_key}' was already processed. Dispute ID: {existing_submission.id}."
        )

    evidence_ids = [e["evidence_id"] for e in packet.packet_data.get("evidence_items", [])]

    # Create Bank Record
    bank_sub_id = f"BANK-DISP-{uuid.uuid4().hex[:8].upper()}"
    bank_entry = BankSubmittedDispute(
        id=bank_sub_id,
        transaction_id=dispute.transaction_id,
        dispute_case_id=dispute.id,
        packet_id=packet.id,
        idempotency_key=payload.idempotency_key,
        amount=dispute.amount,
        currency=dispute.currency,
        dispute_reason=dispute.user_stated_reason,
        evidence_ids=evidence_ids,
        status="SUBMITTED_TO_NETWORK"
    )
    db.add(bank_entry)
    dispute.status = "SUBMITTED"
    db.commit()

    # Step 8: Trigger Independent Verification
    verification_res = independently_verify_submission(db, dispute.id, bank_sub_id)

    return {
        "status": "SUBMITTED",
        "bank_submission_id": bank_sub_id,
        "verification": verification_res
    }

# -------------------------------------------------------------
# 5. Evidence Export: JSON & PDF
# -------------------------------------------------------------
@router.get("/disputes/{dispute_id}/export/json")
def export_dispute_json(dispute_id: str, db: Session = Depends(get_db)):
    packet = db.query(DraftPacket).filter(DraftPacket.dispute_id == dispute_id).first()
    if not packet:
        raise HTTPException(status_code=404, detail="Evidence packet not found.")

    json_str = json.dumps(packet.packet_data, indent=2)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=evidentai_packet_{dispute_id}.json"}
    )

@router.get("/disputes/{dispute_id}/export/pdf")
def export_dispute_pdf(dispute_id: str, db: Session = Depends(get_db)):
    packet = db.query(DraftPacket).filter(DraftPacket.dispute_id == dispute_id).first()
    if not packet:
        raise HTTPException(status_code=404, detail="Evidence packet not found.")

    data = packet.packet_data
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    p.setFillColor(colors.HexColor("#0F172A"))
    p.rect(0, height - 70, width, 70, fill=1, stroke=0)
    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 18)
    p.drawString(40, height - 42, "EvidentAI — Official Dispute Evidence Packet")
    p.setFont("Helvetica", 10)
    p.drawString(40, height - 58, "Every Claim. Backed by Evidence.")

    # Body Info
    p.setFillColor(colors.HexColor("#1E293B"))
    p.setFont("Helvetica-Bold", 12)
    y = height - 100

    p.drawString(40, y, f"Dispute ID: {data.get('dispute_id')}")
    y -= 18
    p.drawString(40, y, f"Transaction Ref: {data.get('transaction_id')} | Amount: {data.get('currency')} {data.get('amount')}")
    y -= 18
    p.drawString(40, y, f"Stated Reason: {data.get('reason')}")
    y -= 25

    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Cardholder Declaration:")
    y -= 15
    p.setFont("Helvetica", 10)
    p.drawString(40, y, str(data.get("customer_allegation", ""))[:95])
    y -= 25

    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Verified Evidence Records:")
    y -= 15
    p.setFont("Helvetica", 9)
    for idx, evi in enumerate(data.get("evidence_items", [])[:6], start=1):
        line = f"[{idx}] {evi.get('source_system')} ({evi.get('source_record_id')}): {evi.get('relevance')}"
        p.drawString(40, y, line[:100])
        y -= 15

    y -= 15
    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Eligibility Status:")
    y -= 15
    p.setFont("Helvetica", 9)
    assessment = data.get("eligibility_assessment", {})
    p.drawString(40, y, f"Status: {assessment.get('status')} | Confidence: {assessment.get('confidence_score')}")
    y -= 15
    p.drawString(40, y, f"Summary: {assessment.get('decision_summary', '')[:100]}")
    y -= 30

    p.setStrokeColor(colors.HexColor("#94A3B8"))
    p.line(40, y, width - 40, y)
    y -= 20
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(40, y, f"Cryptographic SHA-256 Hash: {packet.content_hash}")
    y -= 12
    p.drawString(40, y, "Generated by EvidentAI Agentic Assistant. Powered by Ziro.Digital Hackathon 2026.")

    p.showPage()
    p.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=evidentai_packet_{dispute_id}.pdf"}
    )

# -------------------------------------------------------------
# 6. Official Test Cases Runner
# -------------------------------------------------------------
@router.post("/scenarios/run-all")
def run_all_scenarios(db: Session = Depends(get_db)):
    """Run all 4 official hackathon scenarios and return verified results."""
    from .seed import seed_database
    seed_database(db)

    results = []

    # Scenario TC1: Disputed charge
    # Expected: draft packet
    d1 = DisputeCase(
        id=f"DISP-TC1-{uuid.uuid4().hex[:6]}",
        transaction_id="TXN-IND-1001",
        order_id="ORD-IND-9001",
        user_stated_reason="PRODUCT_NOT_RECEIVED",
        user_explanation="Package never arrived despite payment being settled 12 days ago.",
        amount=4999.00,
        currency="INR",
        status="DRAFT"
    )
    db.add(d1)
    db.commit()
    inv1 = orchestrate_investigation(db, d1.id)
    passed1 = inv1["status"] in ["READY_FOR_DRAFT"] and inv1["draft_packet_id"] is not None

    res1 = TestScenarioResult(
        id="TC1",
        name="TC1 — Disputed charge",
        input_data={"transaction_id": "TXN-IND-1001", "reason": "PRODUCT_NOT_RECEIVED"},
        expected_result="draft packet",
        actual_result=f"Status: {inv1['status']}, Packet ID: {inv1['draft_packet_id']}",
        status="PASS" if passed1 else "FAIL",
        decision_explanation=inv1["decision_summary"],
        evidence_references=[e["tool_name"] for e in inv1["tool_executions"]],
        verification_output=inv1
    )
    db.merge(res1)
    results.append(res1)

    # Scenario TC2: Already refunded
    # Expected: flagged resolved
    d2 = DisputeCase(
        id=f"DISP-TC2-{uuid.uuid4().hex[:6]}",
        transaction_id="TXN-IND-1002",
        order_id="ORD-IND-9002",
        user_stated_reason="PRODUCT_NOT_RECEIVED",
        user_explanation="Customer disputing charge without noticing prior merchant refund.",
        amount=2499.00,
        currency="INR",
        status="DRAFT"
    )
    db.add(d2)
    db.commit()
    inv2 = orchestrate_investigation(db, d2.id)
    passed2 = inv2["status"] == "ALREADY_REFUNDED"

    res2 = TestScenarioResult(
        id="TC2",
        name="TC2 — Already refunded",
        input_data={"transaction_id": "TXN-IND-1002", "reason": "PRODUCT_NOT_RECEIVED"},
        expected_result="flagged resolved",
        actual_result=f"Status: {inv2['status']}",
        status="PASS" if passed2 else "FAIL",
        decision_explanation=inv2["decision_summary"],
        evidence_references=[e["tool_name"] for e in inv2["tool_executions"]],
        verification_output=inv2
    )
    db.merge(res2)
    results.append(res2)

    # Scenario TC3: Fraud claim without evidence
    # Expected: not added
    d3 = DisputeCase(
        id=f"DISP-TC3-{uuid.uuid4().hex[:6]}",
        transaction_id="TXN-IND-1003",
        order_id="ORD-IND-9003",
        user_stated_reason="SUSPECTED_FRAUD",
        user_explanation="I did not make this purchase, somebody stole my details.",
        amount=8999.00,
        currency="INR",
        status="DRAFT"
    )
    db.add(d3)
    db.commit()
    inv3 = orchestrate_investigation(db, d3.id)
    passed3 = inv3["status"] == "NEEDS_MORE_EVIDENCE" and "Official Police Complaint / Cybercrime Acknowledgement or Fraud Affidavit" in inv3["missing_requirements"]

    res3 = TestScenarioResult(
        id="TC3",
        name="TC3 — Fraud claim without evidence",
        input_data={"transaction_id": "TXN-IND-1003", "reason": "SUSPECTED_FRAUD"},
        expected_result="not added",
        actual_result=f"Status: {inv3['status']} (Unsupported fraud allegations excluded)",
        status="PASS" if passed3 else "FAIL",
        decision_explanation=inv3["decision_summary"],
        evidence_references=[e["tool_name"] for e in inv3["tool_executions"]],
        verification_output=inv3
    )
    db.merge(res3)
    results.append(res3)

    # Scenario TC4: Provisional credit
    # Expected: not called final
    d4 = DisputeCase(
        id=f"DISP-TC4-{uuid.uuid4().hex[:6]}",
        transaction_id="TXN-IND-1004",
        order_id="ORD-IND-9004",
        user_stated_reason="PRODUCT_NOT_RECEIVED",
        user_explanation="Package lost in transit, bank provided temporary credit.",
        amount=15499.00,
        currency="INR",
        status="DRAFT"
    )
    db.add(d4)
    db.commit()
    inv4 = orchestrate_investigation(db, d4.id)
    passed4 = inv4["status"] == "UNDER_REVIEW" and "NOT a final refund" in inv4["decision_summary"]

    res4 = TestScenarioResult(
        id="TC4",
        name="TC4 — Provisional credit",
        input_data={"transaction_id": "TXN-IND-1004", "reason": "PRODUCT_NOT_RECEIVED"},
        expected_result="not called final",
        actual_result=f"Status: {inv4['status']} (Provisional credit labeled interim, never final)",
        status="PASS" if passed4 else "FAIL",
        decision_explanation=inv4["decision_summary"],
        evidence_references=[e["tool_name"] for e in inv4["tool_executions"]],
        verification_output=inv4
    )
    db.merge(res4)
    results.append(res4)

    db.commit()

    return [
        {
            "id": r.id,
            "name": r.name,
            "input_data": r.input_data,
            "expected_result": r.expected_result,
            "actual_result": r.actual_result,
            "status": r.status,
            "decision_explanation": r.decision_explanation,
            "evidence_references": r.evidence_references,
            "verification_output": r.verification_output
        } for r in results
    ]

@router.get("/scenarios/results")
def get_scenario_results(db: Session = Depends(get_db)):
    scenarios = db.query(TestScenarioResult).order_by(TestScenarioResult.id.asc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "input_data": r.input_data,
            "expected_result": r.expected_result,
            "actual_result": r.actual_result,
            "status": r.status,
            "decision_explanation": r.decision_explanation,
            "evidence_references": r.evidence_references,
            "verification_output": r.verification_output
        } for r in scenarios
    ]
