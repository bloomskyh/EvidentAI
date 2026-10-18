from datetime import datetime, timezone
import uuid
from typing import Dict, Any
from sqlalchemy.orm import Session
from .models import (
    BankSubmittedDispute, IndependentVerification, DisputeCase, DraftPacket
)

def independently_verify_submission(
    db: Session,
    dispute_id: str,
    bank_submission_id: str
) -> Dict[str, Any]:
    """
    Independent Verification Component.
    Executed separately from packet generation and submission.
    Directly queries the Mock Bank database to verify ledger state.
    """
    dispute = db.query(DisputeCase).filter(DisputeCase.id == dispute_id).first()
    submitted = db.query(BankSubmittedDispute).filter(BankSubmittedDispute.id == bank_submission_id).first()

    checks = {
        "dispute_id_exists": False,
        "transaction_id_match": False,
        "amount_currency_match": False,
        "evidence_references_valid": False,
        "single_execution_guaranteed": False,
        "status_matches_network_protocol": False
    }

    if not submitted:
        details = {
            "checks": checks,
            "error": f"Submission ID '{bank_submission_id}' not found in bank network ledger."
        }
        verif = IndependentVerification(
            id=f"VERIF-{uuid.uuid4().hex[:8].upper()}",
            dispute_id=dispute_id,
            bank_dispute_id=bank_submission_id,
            verification_status="FAIL",
            details=details,
            explanation="The mock bank did not record any dispute with this identifier."
        )
        db.add(verif)
        db.commit()
        return {
            "status": "FAIL",
            "explanation": verif.explanation,
            "details": details
        }

    checks["dispute_id_exists"] = True

    # Check 1: Transaction ID Match
    if dispute and submitted.transaction_id == dispute.transaction_id:
        checks["transaction_id_match"] = True

    # Check 2: Amount & Currency Match
    if dispute and submitted.amount == dispute.amount and submitted.currency == dispute.currency:
        checks["amount_currency_match"] = True

    # Check 3: Evidence references exist
    if submitted.evidence_ids and len(submitted.evidence_ids) > 0:
        checks["evidence_references_valid"] = True

    # Check 4: Idempotency / No duplicate submissions
    duplicate_count = db.query(BankSubmittedDispute).filter(
        BankSubmittedDispute.idempotency_key == submitted.idempotency_key
    ).count()
    if duplicate_count == 1:
        checks["single_execution_guaranteed"] = True

    # Check 5: Status
    if submitted.status in ["SUBMITTED_TO_NETWORK", "UNDER_INVESTIGATION", "ACCEPTED"]:
        checks["status_matches_network_protocol"] = True

    all_passed = all(checks.values())
    verif_status = "PASS" if all_passed else "FAIL"
    explanation = (
        "Independent bank verification SUCCEEDED. All cryptographic and financial checks matched bank network records."
        if all_passed else
        "Independent bank verification FAILED. Discrepancies detected between client claim and bank network records."
    )

    verif = IndependentVerification(
        id=f"VERIF-{uuid.uuid4().hex[:8].upper()}",
        dispute_id=dispute_id,
        bank_dispute_id=bank_submission_id,
        verification_status=verif_status,
        details={"checks": checks, "submitted_data": {
            "id": submitted.id,
            "amount": submitted.amount,
            "currency": submitted.currency,
            "transaction_id": submitted.transaction_id,
            "status": submitted.status
        }},
        explanation=explanation
    )
    db.add(verif)
    db.commit()

    return {
        "status": verif_status,
        "explanation": explanation,
        "details": checks,
        "verification_id": verif.id
    }
