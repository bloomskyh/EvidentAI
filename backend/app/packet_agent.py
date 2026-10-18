import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from .models import DisputeCase, EvidenceItem, DraftPacket

def calculate_packet_hash(packet_dict: Dict[str, Any]) -> str:
    """Compute deterministic SHA256 snapshot for immutable verification."""
    serialized = json.dumps(packet_dict, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def assemble_draft_packet(
    db: Session,
    dispute: DisputeCase,
    evidence_items: List[EvidenceItem],
    eligibility_result: Dict[str, Any]
) -> DraftPacket:
    """
    Evidence Packet Agent.
    Prepares a structured draft packet strictly from verified evidence.
    Distinguishes customer-provided claims from independently verified facts.
    """
    # 1. Filter evidence - only verified, relevant evidence included
    structured_evidence = []
    for item in evidence_items:
        if item.verification_status == "VERIFIED" and not item.is_user_allegation:
            structured_evidence.append({
                "evidence_id": item.id,
                "source_system": item.source_system,
                "source_record_id": item.source_record_id,
                "source_endpoint": item.source_endpoint,
                "retrieved_at": item.retrieval_timestamp.isoformat() if item.retrieval_timestamp else None,
                "facts": item.extracted_facts,
                "relevance": item.relevance_explanation,
                "status": item.verification_status
            })

    # 2. Chronological Timeline
    timeline = []
    bank_evi = next((e for e in evidence_items if e.item_type == "TRANSACTION_RECORD"), None)
    if bank_evi:
        timeline.append({
            "timestamp": bank_evi.extracted_facts.get("transaction_date"),
            "event": "Transaction Authorized & Settled",
            "details": f"{dispute.currency} {dispute.amount} settled at {bank_evi.extracted_facts.get('merchant_name')}"
        })

    order_evi = next((e for e in evidence_items if e.item_type == "ORDER_DETAILS"), None)
    if order_evi:
        timeline.append({
            "timestamp": order_evi.extracted_facts.get("order_date"),
            "event": "Store Order Created",
            "details": f"Order {order_evi.source_record_id} recorded in merchant system ({order_evi.extracted_facts.get('fulfillment_status')})"
        })

    for item in evidence_items:
        if item.item_type == "MERCHANT_COMMUNICATION":
            timeline.append({
                "timestamp": item.extracted_facts.get("timestamp"),
                "event": f"Merchant Communication ({item.extracted_facts.get('sender')})",
                "details": item.extracted_facts.get("subject", "Notice")
            })

    # Sort timeline chronologically
    timeline.sort(key=lambda x: str(x.get("timestamp") or ""))

    # 3. Formatted Bank Dispute Form
    bank_dispute_form = {
        "form_version": "FINTECH_REV_2026_01",
        "cardholder_dispute_declaration": {
            "cardholder_claim": dispute.user_explanation,
            "dispute_category": dispute.user_stated_reason,
            "disputed_amount": dispute.amount,
            "currency": dispute.currency,
            "transaction_reference": dispute.transaction_id,
            "associated_order": dispute.order_id
        },
        "verified_evidence_summary": [e["relevance"] for e in structured_evidence],
        "eligibility_findings": {
            "status": eligibility_result.get("status"),
            "summary": eligibility_result.get("decision_summary"),
            "confidence": eligibility_result.get("confidence_score")
        },
        "missing_items": eligibility_result.get("missing_requirements", []),
        "provisional_credit_present": eligibility_result.get("provisional_credit_flag", False),
        "disclaimer": "This document contains verified financial claims compiled by EvidentAI. All allegations require explicit human cardholder signature/authorization before network transmission."
    }

    packet_payload = {
        "dispute_id": dispute.id,
        "transaction_id": dispute.transaction_id,
        "order_id": dispute.order_id,
        "amount": dispute.amount,
        "currency": dispute.currency,
        "reason": dispute.user_stated_reason,
        "customer_allegation": dispute.user_explanation,
        "timeline": timeline,
        "evidence_items": structured_evidence,
        "missing_requirements": eligibility_result.get("missing_requirements", []),
        "eligibility_assessment": eligibility_result,
        "bank_dispute_form": bank_dispute_form,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

    content_hash = calculate_packet_hash(packet_payload)

    # Check existing draft packet for this dispute
    existing_pkt = db.query(DraftPacket).filter(DraftPacket.dispute_id == dispute.id).first()
    if existing_pkt:
        existing_pkt.packet_version += 1
        existing_pkt.content_hash = content_hash
        existing_pkt.packet_data = packet_payload
        existing_pkt.is_approved = False # Invalidate previous approval on modification
        existing_pkt.approval_timestamp = None
        existing_pkt.approver_id = None
        db.commit()
        return existing_pkt

    new_pkt = DraftPacket(
        id=f"PKT-{uuid.uuid4().hex[:8].upper()}",
        dispute_id=dispute.id,
        packet_version=1,
        content_hash=content_hash,
        packet_data=packet_payload,
        is_approved=False
    )
    db.add(new_pkt)
    db.commit()
    return new_pkt
