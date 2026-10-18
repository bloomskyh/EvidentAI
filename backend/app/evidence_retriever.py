from datetime import datetime, timezone
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from .models import (
    BankTransaction, BankDisputeRule, StoreOrder, StorePayment,
    StoreRefund, StoreMessage, EvidenceItem, DisputeCase
)

def retrieve_bank_transaction_evidence(db: Session, dispute: DisputeCase, execution_log: List[Dict[str, Any]]) -> Optional[EvidenceItem]:
    exec_entry = {
        "tool_name": "retrieve_bank_transaction",
        "system": "MOCK_BANK",
        "endpoint": f"/api/mock-bank/transactions/{dispute.transaction_id}",
        "status": "CALLED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    txn = db.query(BankTransaction).filter(BankTransaction.id == dispute.transaction_id).first()
    if not txn:
        exec_entry["status"] = "NOT_FOUND"
        exec_entry["detail"] = f"Transaction {dispute.transaction_id} not present in bank core."
        execution_log.append(exec_entry)
        return None

    facts = {
        "transaction_id": txn.id,
        "amount": txn.amount,
        "currency": txn.currency,
        "card_last4": txn.card_last4,
        "account_number": txn.account_number,
        "merchant_name": txn.merchant_name,
        "transaction_date": txn.transaction_date.isoformat(),
        "status": txn.status,
        "refund_status": txn.refund_status,
        "has_provisional_credit": txn.has_provisional_credit,
        "provisional_credit_amount": txn.provisional_credit_amount
    }

    evi = EvidenceItem(
        id=f"EVI-BNK-{uuid.uuid4().hex[:8].upper()}",
        dispute_id=dispute.id,
        source_system="BANK_CORE",
        source_record_id=txn.id,
        source_endpoint=f"/api/mock-bank/transactions/{txn.id}",
        retrieval_timestamp=datetime.now(timezone.utc),
        item_type="TRANSACTION_RECORD",
        extracted_facts=facts,
        relevance_explanation="Official banking ledger entry confirming authorization, settled amount, and card details.",
        verification_status="VERIFIED",
        is_user_allegation=False
    )
    db.add(evi)
    exec_entry["status"] = "SUCCESS"
    exec_entry["evidence_id"] = evi.id
    execution_log.append(exec_entry)
    return evi

def retrieve_bank_rules_evidence(db: Session, dispute: DisputeCase, currency: str, execution_log: List[Dict[str, Any]]) -> Optional[EvidenceItem]:
    exec_entry = {
        "tool_name": "retrieve_bank_dispute_rules",
        "system": "MOCK_BANK",
        "endpoint": f"/api/mock-bank/dispute-rules?currency={currency}",
        "status": "CALLED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    rule = db.query(BankDisputeRule).filter(BankDisputeRule.currency == currency).first()
    if not rule:
        rule = db.query(BankDisputeRule).first()

    if not rule:
        exec_entry["status"] = "NOT_FOUND"
        execution_log.append(exec_entry)
        return None

    facts = {
        "rule_id": rule.id,
        "currency": rule.currency,
        "dispute_window_days": rule.dispute_window_days,
        "require_merchant_contact": rule.require_merchant_contact,
        "allowed_reasons": rule.allowed_reasons
    }

    evi = EvidenceItem(
        id=f"EVI-RUL-{uuid.uuid4().hex[:8].upper()}",
        dispute_id=dispute.id,
        source_system="BANK_CORE",
        source_record_id=rule.id,
        source_endpoint="/api/mock-bank/dispute-rules",
        retrieval_timestamp=datetime.now(timezone.utc),
        item_type="BANK_DISPUTE_RULES",
        extracted_facts=facts,
        relevance_explanation=f"Network policy requires disputes to be filed within {rule.dispute_window_days} days of settlement.",
        verification_status="VERIFIED",
        is_user_allegation=False
    )
    db.add(evi)
    exec_entry["status"] = "SUCCESS"
    exec_entry["evidence_id"] = evi.id
    execution_log.append(exec_entry)
    return evi

def retrieve_store_order_evidence(db: Session, dispute: DisputeCase, execution_log: List[Dict[str, Any]]) -> Optional[EvidenceItem]:
    exec_entry = {
        "tool_name": "retrieve_store_order",
        "system": "MOCK_STORE",
        "endpoint": f"/api/mock-store/orders/by-transaction/{dispute.transaction_id}",
        "status": "CALLED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    order = db.query(StoreOrder).filter(StoreOrder.linked_transaction_id == dispute.transaction_id).first()
    if not order and dispute.order_id:
        order = db.query(StoreOrder).filter(StoreOrder.id == dispute.order_id).first()

    if not order:
        exec_entry["status"] = "NOT_FOUND"
        exec_entry["detail"] = f"No store order found matching transaction {dispute.transaction_id}."
        execution_log.append(exec_entry)
        return None

    facts = {
        "order_id": order.id,
        "customer_email": order.customer_email,
        "customer_name": order.customer_name,
        "order_date": order.order_date.isoformat(),
        "amount": order.amount,
        "currency": order.currency,
        "fulfillment_status": order.fulfillment_status,
        "delivery_date": order.delivery_date.isoformat() if order.delivery_date else None,
        "tracking_number": order.tracking_number,
        "items_summary": order.items_summary
    }

    evi = EvidenceItem(
        id=f"EVI-ORD-{uuid.uuid4().hex[:8].upper()}",
        dispute_id=dispute.id,
        source_system="STORE_COMMERCE",
        source_record_id=order.id,
        source_endpoint=f"/api/mock-store/orders/{order.id}",
        retrieval_timestamp=datetime.now(timezone.utc),
        item_type="ORDER_DETAILS",
        extracted_facts=facts,
        relevance_explanation="Merchant store checkout order documenting purchased items and recorded fulfillment status.",
        verification_status="VERIFIED",
        is_user_allegation=False
    )
    db.add(evi)
    exec_entry["status"] = "SUCCESS"
    exec_entry["evidence_id"] = evi.id
    execution_log.append(exec_entry)
    return evi

def retrieve_store_refund_evidence(db: Session, dispute: DisputeCase, execution_log: List[Dict[str, Any]]) -> Optional[EvidenceItem]:
    exec_entry = {
        "tool_name": "retrieve_store_refund",
        "system": "MOCK_STORE",
        "endpoint": f"/api/mock-store/refunds?transaction_id={dispute.transaction_id}",
        "status": "CALLED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    refund = db.query(StoreRefund).filter(StoreRefund.transaction_id == dispute.transaction_id).first()
    if not refund:
        exec_entry["status"] = "NO_REFUND_RECORDED"
        execution_log.append(exec_entry)
        return None

    facts = {
        "refund_id": refund.id,
        "order_id": refund.order_id,
        "transaction_id": refund.transaction_id,
        "refund_amount": refund.amount,
        "currency": refund.currency,
        "refund_date": refund.refund_date.isoformat(),
        "reason": refund.reason,
        "status": refund.status,
        "reference_number": refund.reference_number
    }

    evi = EvidenceItem(
        id=f"EVI-REF-{uuid.uuid4().hex[:8].upper()}",
        dispute_id=dispute.id,
        source_system="STORE_COMMERCE",
        source_record_id=refund.id,
        source_endpoint=f"/api/mock-store/refunds?transaction_id={dispute.transaction_id}",
        retrieval_timestamp=datetime.now(timezone.utc),
        item_type="REFUND_VOUCHER",
        extracted_facts=facts,
        relevance_explanation="Verified merchant refund credit record reversing charges back to the cardholder.",
        verification_status="VERIFIED",
        is_user_allegation=False
    )
    db.add(evi)
    exec_entry["status"] = "SUCCESS"
    exec_entry["evidence_id"] = evi.id
    execution_log.append(exec_entry)
    return evi

def retrieve_store_messages_evidence(db: Session, dispute: DisputeCase, order_id: Optional[str], execution_log: List[Dict[str, Any]]) -> List[EvidenceItem]:
    if not order_id:
        return []

    exec_entry = {
        "tool_name": "retrieve_merchant_messages",
        "system": "MOCK_STORE",
        "endpoint": f"/api/mock-store/messages?order_id={order_id}",
        "status": "CALLED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    messages = db.query(StoreMessage).filter(StoreMessage.order_id == order_id).all()
    created_items = []
    for msg in messages:
        facts = {
            "message_id": msg.id,
            "order_id": msg.order_id,
            "sender": msg.sender,
            "timestamp": msg.timestamp.isoformat(),
            "subject": msg.subject,
            "body": msg.message_body,
            "channel": msg.channel
        }
        evi = EvidenceItem(
            id=f"EVI-MSG-{uuid.uuid4().hex[:8].upper()}",
            dispute_id=dispute.id,
            source_system="STORE_MESSAGES",
            source_record_id=msg.id,
            source_endpoint=f"/api/mock-store/messages?order_id={order_id}",
            retrieval_timestamp=datetime.now(timezone.utc),
            item_type="MERCHANT_COMMUNICATION",
            extracted_facts=facts,
            relevance_explanation=f"Direct communication from {msg.sender} showing merchant engagement and shipment updates.",
            verification_status="VERIFIED",
            is_user_allegation=False
        )
        db.add(evi)
        created_items.append(evi)

    exec_entry["status"] = "SUCCESS"
    exec_entry["count"] = len(created_items)
    execution_log.append(exec_entry)
    return created_items
