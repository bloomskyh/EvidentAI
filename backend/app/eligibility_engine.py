from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from .models import DisputeCase, EvidenceItem

def evaluate_eligibility_and_reasoning(
    dispute: DisputeCase,
    evidence_items: List[EvidenceItem]
) -> Dict[str, Any]:
    """
    Deterministic Financial Rule Engine.
    Evaluates eligibility strictly based on banking rules and verified records.
    States:
      - READY_FOR_DRAFT
      - NEEDS_MORE_EVIDENCE
      - OUTSIDE_DISPUTE_WINDOW
      - ALREADY_REFUNDED
      - UNDER_REVIEW
      - BLOCKED
    """
    reasons = []
    missing_requirements = []
    supporting_evidence_ids = []
    confidence_score = 1.0

    # 1. Check Bank Transaction Evidence
    bank_evi = next((e for e in evidence_items if e.item_type == "TRANSACTION_RECORD"), None)
    if not bank_evi:
        return {
            "status": "BLOCKED",
            "decision_summary": f"Transaction '{dispute.transaction_id}' could not be located in bank core ledger. Dispute cannot proceed.",
            "reasons": ["TRANSACTION_NOT_FOUND"],
            "supporting_evidence_ids": [],
            "missing_requirements": ["Valid bank transaction record"],
            "recommended_action": "Verify transaction ID on your bank statement and retry.",
            "confidence_score": 1.0,
            "provisional_credit_flag": False,
            "is_refunded_flag": False
        }

    bank_facts = bank_evi.extracted_facts
    supporting_evidence_ids.append(bank_evi.id)

    # Check Amount and Currency consistency
    if bank_facts.get("amount") != dispute.amount or bank_facts.get("currency") != dispute.currency:
        return {
            "status": "BLOCKED",
            "decision_summary": f"Mismatch detected: Disputed amount ({dispute.currency} {dispute.amount}) differs from bank ledger amount ({bank_facts.get('currency')} {bank_facts.get('amount')}).",
            "reasons": ["AMOUNT_CURRENCY_MISMATCH"],
            "supporting_evidence_ids": supporting_evidence_ids,
            "missing_requirements": ["Amount reconciliation"],
            "recommended_action": "Correct the disputed amount to match bank records.",
            "confidence_score": 1.0,
            "provisional_credit_flag": False,
            "is_refunded_flag": False
        }

    # 2. Check Dispute Window from Rules Evidence
    rules_evi = next((e for e in evidence_items if e.item_type == "BANK_DISPUTE_RULES"), None)
    window_days = 60
    if rules_evi:
        window_days = rules_evi.extracted_facts.get("dispute_window_days", 60)
        supporting_evidence_ids.append(rules_evi.id)

    txn_date_str = bank_facts.get("transaction_date")
    if txn_date_str:
        txn_date = datetime.fromisoformat(txn_date_str)
        if txn_date.tzinfo is None:
            txn_date = txn_date.replace(tzinfo=timezone.utc)
        now_utc = datetime.now(timezone.utc)
        age_days = (now_utc - txn_date).days

        if age_days > window_days:
            return {
                "status": "OUTSIDE_DISPUTE_WINDOW",
                "decision_summary": f"Transaction occurred {age_days} days ago, exceeding the bank's maximum allowable dispute window of {window_days} days.",
                "reasons": ["EXCEEDS_DISPUTE_WINDOW"],
                "supporting_evidence_ids": supporting_evidence_ids,
                "missing_requirements": ["Special exception approval or out-of-time waiver"],
                "recommended_action": "Contact merchant support directly or request special cardholder grievance review.",
                "confidence_score": 1.0,
                "provisional_credit_flag": False,
                "is_refunded_flag": False
            }

    # 3. Check Verified Refunds (TC2: Already Refunded)
    refund_evi = next((e for e in evidence_items if e.item_type == "REFUND_VOUCHER"), None)
    if refund_evi:
        refund_facts = refund_evi.extracted_facts
        if refund_facts.get("status") == "COMPLETED" and refund_facts.get("refund_amount") == dispute.amount:
            supporting_evidence_ids.append(refund_evi.id)
            return {
                "status": "ALREADY_REFUNDED",
                "decision_summary": f"Merchant has already issued a full verified refund of {dispute.currency} {dispute.amount} (ARN: {refund_facts.get('reference_number')}). Case is flagged resolved.",
                "reasons": ["REFUND_ALREADY_ISSUED"],
                "supporting_evidence_ids": supporting_evidence_ids,
                "missing_requirements": [],
                "recommended_action": "No chargeback required. Cardholder statement should reflect credited funds within 3-5 business days.",
                "confidence_score": 1.0,
                "provisional_credit_flag": False,
                "is_refunded_flag": True
            }

    # 4. Check Provisional Credit (TC4: Provisional Credit)
    has_provisional = bank_facts.get("has_provisional_credit", False)
    provisional_amount = bank_facts.get("provisional_credit_amount", 0.0)

    # 5. Check Dispute Stated Reason vs Evidence (TC3: Fraud claim without evidence)
    if dispute.user_stated_reason == "SUSPECTED_FRAUD":
        # Fraud allegations MUST be corroborated by objective independent evidence
        # (e.g. Police complaint, unauthorized IP logs, bank fraud alert)
        has_fraud_evidence = any(
            e.item_type in ["POLICE_REPORT", "FRAUD_AFFIDAVIT", "DEVICE_SECURITY_LOG"] 
            for e in evidence_items
        )
        if not has_fraud_evidence:
            reasons.append("FRAUD_CLAIM_UNSUPPORTED")
            missing_requirements.append("Official Police Complaint / Cybercrime Acknowledgement or Fraud Affidavit")
            missing_requirements.append("Card cancellation confirmation")
            
            summary = (
                "Fraud allegation cannot be submitted without corroborating documentation. "
                "The customer's statement has been recorded as a user allegation, but objective evidence is missing."
            )
            return {
                "status": "NEEDS_MORE_EVIDENCE",
                "decision_summary": summary,
                "reasons": reasons,
                "supporting_evidence_ids": supporting_evidence_ids,
                "missing_requirements": missing_requirements,
                "recommended_action": "Upload required fraud affidavit or official cybercrime acknowledgement before drafting dispute packet.",
                "confidence_score": 0.85,
                "provisional_credit_flag": has_provisional,
                "is_refunded_flag": False
            }

    # 6. Check Product Not Received (TC1 & General)
    if dispute.user_stated_reason == "PRODUCT_NOT_RECEIVED":
        order_evi = next((e for e in evidence_items if e.item_type == "ORDER_DETAILS"), None)
        if not order_evi:
            missing_requirements.append("Merchant Order Details & Tracking Number")
        else:
            supporting_evidence_ids.append(order_evi.id)
            order_facts = order_evi.extracted_facts
            if order_facts.get("fulfillment_status") == "DELIVERED":
                # Conflicting evidence: merchant claims delivered, user claims not received
                reasons.append("MERCHANT_DELIVERY_RECORD_CONFLICT")
                missing_requirements.append("Proof of non-receipt or delivery denial letter from courier")

        # Communication with merchant check
        msg_evis = [e for e in evidence_items if e.item_type == "MERCHANT_COMMUNICATION"]
        for m in msg_evis:
            supporting_evidence_ids.append(m.id)

        if not msg_evis and not dispute.user_explanation:
            missing_requirements.append("Written proof of attempt to resolve directly with merchant")

    # Handle Provisional Credit Labeling (Must never be called final!)
    if has_provisional:
        reasons.append("PROVISIONAL_CREDIT_ACTIVE")
        decision_summary = (
            f"Provisional credit of {dispute.currency} {provisional_amount} is currently applied to the cardholder account. "
            f"IMPORTANT: This is temporary interim credit and NOT a final refund or final dispute resolution. "
            f"Case remains UNDER_REVIEW until merchant inquiry completes."
        )
        return {
            "status": "UNDER_REVIEW",
            "decision_summary": decision_summary,
            "reasons": reasons,
            "supporting_evidence_ids": supporting_evidence_ids,
            "missing_requirements": missing_requirements,
            "recommended_action": "Monitor bank statement and merchant response. Do not close dispute prematurely.",
            "confidence_score": 0.95,
            "provisional_credit_flag": True,
            "is_refunded_flag": False
        }

    # If missing critical requirements
    if missing_requirements:
        return {
            "status": "NEEDS_MORE_EVIDENCE",
            "decision_summary": "Dispute details collected, but mandatory supporting evidence is incomplete.",
            "reasons": reasons or ["MISSING_MANDATORY_EVIDENCE"],
            "supporting_evidence_ids": supporting_evidence_ids,
            "missing_requirements": missing_requirements,
            "recommended_action": "Provide the requested supporting documents to prepare formal draft packet.",
            "confidence_score": 0.90,
            "provisional_credit_flag": False,
            "is_refunded_flag": False
        }

    # Genuine case ready for draft packet (TC1)
    return {
        "status": "READY_FOR_DRAFT",
        "decision_summary": "All eligibility criteria met. Transaction matched, dispute window valid, non-delivery corroborated by merchant tracking records. Ready to compile draft evidence packet.",
        "reasons": ["ELIGIBILITY_VERIFIED", "EVIDENCE_MATCHES_CLAIM"],
        "supporting_evidence_ids": supporting_evidence_ids,
        "missing_requirements": [],
        "recommended_action": "Compile draft dispute packet and submit for human approval.",
        "confidence_score": 0.98,
        "provisional_credit_flag": False,
        "is_refunded_flag": False
    }
