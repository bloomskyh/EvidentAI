from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .database import get_db
from .models import (
    BankTransaction, BankDisputeRule, BankSubmittedDispute
)
from .schemas import (
    BankTransactionSchema, BankDisputeRuleSchema
)

router = APIRouter(prefix="/api/mock-bank", tags=["Mock Bank Service"])

@router.get("/transactions", response_model=List[BankTransactionSchema])
def list_bank_transactions(db: Session = Depends(get_db)):
    """List all transactions recorded in the bank core ledger."""
    return db.query(BankTransaction).order_by(BankTransaction.transaction_date.desc()).all()

@router.get("/transactions/{transaction_id}", response_model=BankTransactionSchema)
def get_bank_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed transaction record from bank core."""
    txn = db.query(BankTransaction).filter(BankTransaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bank transaction '{transaction_id}' not found in core ledger."
        )
    return txn

@router.get("/dispute-rules", response_model=List[BankDisputeRuleSchema])
def get_dispute_rules(currency: Optional[str] = "INR", db: Session = Depends(get_db)):
    """Retrieve bank dispute rules and configurable window deadlines."""
    query = db.query(BankDisputeRule)
    if currency:
        query = query.filter(BankDisputeRule.currency == currency)
    rules = query.all()
    if not rules:
        # Fallback to default
        rules = db.query(BankDisputeRule).all()
    return rules

@router.get("/disputes/{dispute_id}")
def get_submitted_dispute(dispute_id: str, db: Session = Depends(get_db)):
    """Retrieve a dispute submitted to the bank network for independent verification."""
    disp = db.query(BankSubmittedDispute).filter(BankSubmittedDispute.id == dispute_id).first()
    if not disp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submitted dispute '{dispute_id}' does not exist in bank network records."
        )
    return {
        "id": disp.id,
        "transaction_id": disp.transaction_id,
        "dispute_case_id": disp.dispute_case_id,
        "packet_id": disp.packet_id,
        "amount": disp.amount,
        "currency": disp.currency,
        "dispute_reason": disp.dispute_reason,
        "evidence_ids": disp.evidence_ids,
        "status": disp.status,
        "idempotency_key": disp.idempotency_key,
        "received_timestamp": disp.received_timestamp.isoformat() if disp.received_timestamp else None
    }
