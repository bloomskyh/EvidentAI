from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

def generate_uuid():
    return str(uuid.uuid4())

class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(String(64), primary_key=True) # e.g. TXN-1001
    account_number = Column(String(32), nullable=False)
    card_last4 = Column(String(4), nullable=False)
    order_id = Column(String(64), nullable=True) # Cross-system link
    merchant_name = Column(String(128), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    transaction_date = Column(DateTime, nullable=False)
    posted_date = Column(DateTime, nullable=True)
    status = Column(String(32), default="SETTLED") # SETTLED, PENDING, REVERSED
    refund_status = Column(String(32), default="NONE") # NONE, PARTIAL, FULL
    description = Column(String(255), nullable=True)
    has_provisional_credit = Column(Boolean, default=False)
    provisional_credit_amount = Column(Float, default=0.0)
    provisional_credit_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

class BankDisputeRule(Base):
    __tablename__ = "bank_dispute_rules"

    id = Column(String(64), primary_key=True) # e.g. RULE-INR-01
    currency = Column(String(8), default="INR")
    dispute_window_days = Column(Integer, default=60) # Configurable window
    require_merchant_contact = Column(Boolean, default=True)
    requires_written_explanation = Column(Boolean, default=True)
    allowed_reasons = Column(JSON, nullable=False) # list of reason strings
    created_at = Column(DateTime, default=get_utc_now)

class StoreOrder(Base):
    __tablename__ = "store_orders"

    id = Column(String(64), primary_key=True) # e.g. ORD-9001
    customer_email = Column(String(128), nullable=False)
    customer_name = Column(String(128), nullable=False)
    order_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    fulfillment_status = Column(String(32), default="DELIVERED") # DELIVERED, UNFULFILLED, CANCELLED, TRANSIT
    delivery_date = Column(DateTime, nullable=True)
    tracking_number = Column(String(64), nullable=True)
    items_summary = Column(Text, nullable=True)
    linked_transaction_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

class StorePayment(Base):
    __tablename__ = "store_payments"

    id = Column(String(64), primary_key=True) # e.g. PAY-8001
    order_id = Column(String(64), ForeignKey("store_orders.id"), nullable=False)
    transaction_id = Column(String(64), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    payment_method = Column(String(32), default="CREDIT_CARD")
    payment_status = Column(String(32), default="CAPTURED") # CAPTURED, FAILED, REFUNDED
    created_at = Column(DateTime, default=get_utc_now)

class StoreRefund(Base):
    __tablename__ = "store_refunds"

    id = Column(String(64), primary_key=True) # e.g. REF-3001
    order_id = Column(String(64), ForeignKey("store_orders.id"), nullable=False)
    transaction_id = Column(String(64), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    refund_date = Column(DateTime, nullable=False)
    reason = Column(String(255), nullable=True)
    status = Column(String(32), default="COMPLETED") # COMPLETED, PENDING
    reference_number = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

class StoreMessage(Base):
    __tablename__ = "store_messages"

    id = Column(String(64), primary_key=True) # e.g. MSG-5001
    order_id = Column(String(64), ForeignKey("store_orders.id"), nullable=False)
    sender = Column(String(64), nullable=False) # CUSTOMER, MERCHANT, SUPPORT
    timestamp = Column(DateTime, nullable=False)
    subject = Column(String(255), nullable=True)
    message_body = Column(Text, nullable=False)
    channel = Column(String(32), default="EMAIL") # EMAIL, CHAT, TICKET
    created_at = Column(DateTime, default=get_utc_now)

class DisputeCase(Base):
    __tablename__ = "dispute_cases"

    id = Column(String(64), primary_key=True) # e.g. DISP-UUID
    transaction_id = Column(String(64), nullable=False)
    order_id = Column(String(64), nullable=True)
    user_stated_reason = Column(String(64), nullable=False) # PRODUCT_NOT_RECEIVED, DUPLICATE_CHARGE, INCORRECT_AMOUNT, SUSPECTED_FRAUD
    user_explanation = Column(Text, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    
    # Workflow status: DRAFT, READY_FOR_DRAFT, NEEDS_MORE_EVIDENCE, OUTSIDE_DISPUTE_WINDOW, ALREADY_REFUNDED, UNDER_REVIEW, BLOCKED, APPROVED, SUBMITTED, REJECTED
    status = Column(String(64), default="DRAFT")
    eligibility_decision = Column(JSON, nullable=True)
    provisional_credit_flag = Column(Boolean, default=False)
    is_refunded_flag = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String(64), primary_key=True) # e.g. EVI-UUID
    dispute_id = Column(String(64), ForeignKey("dispute_cases.id"), nullable=False)
    source_system = Column(String(32), nullable=False) # BANK_CORE, STORE_COMMERCE, USER_UPLOAD, STORE_MESSAGES
    source_record_id = Column(String(64), nullable=False)
    source_endpoint = Column(String(128), nullable=False)
    retrieval_timestamp = Column(DateTime, default=get_utc_now)
    item_type = Column(String(64), nullable=False) # TRANSACTION_RECORD, ORDER_DETAILS, REFUND_VOUCHER, MERCHANT_MESSAGE, PROVISIONAL_CREDIT_RECEIPT
    extracted_facts = Column(JSON, nullable=False)
    relevance_explanation = Column(Text, nullable=False)
    verification_status = Column(String(32), default="VERIFIED") # VERIFIED, UNVERIFIED, CONFLICT, UNRELIABLE
    is_user_allegation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now)

class InvestigationRun(Base):
    __tablename__ = "investigation_runs"

    id = Column(String(64), primary_key=True) # e.g. RUN-UUID
    dispute_id = Column(String(64), ForeignKey("dispute_cases.id"), nullable=False)
    plan_steps = Column(JSON, nullable=False)
    tool_executions = Column(JSON, nullable=False) # list of tool calls with timestamps, parameters & outputs
    decision_status = Column(String(64), nullable=False)
    decision_summary = Column(Text, nullable=False)
    missing_requirements = Column(JSON, nullable=True)
    recommended_action = Column(String(128), nullable=False)
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=get_utc_now)

class DraftPacket(Base):
    __tablename__ = "draft_packets"

    id = Column(String(64), primary_key=True) # e.g. PKT-UUID
    dispute_id = Column(String(64), ForeignKey("dispute_cases.id"), nullable=False)
    packet_version = Column(Integer, default=1)
    content_hash = Column(String(64), nullable=False) # SHA256 snapshot for immutable verification
    packet_data = Column(JSON, nullable=False)
    is_approved = Column(Boolean, default=False)
    approval_timestamp = Column(DateTime, nullable=True)
    approver_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id = Column(String(64), primary_key=True)
    dispute_id = Column(String(64), ForeignKey("dispute_cases.id"), nullable=False)
    packet_id = Column(String(64), ForeignKey("draft_packets.id"), nullable=False)
    packet_version = Column(Integer, nullable=False)
    action = Column(String(32), nullable=False) # APPROVED, REJECTED, RETURNED_FOR_CORRECTION
    approver_name = Column(String(64), nullable=False)
    comments = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=get_utc_now)

class BankSubmittedDispute(Base):
    __tablename__ = "bank_submitted_disputes"

    id = Column(String(64), primary_key=True) # e.g. BANK-DISP-XXXX
    transaction_id = Column(String(64), nullable=False)
    dispute_case_id = Column(String(64), nullable=False)
    packet_id = Column(String(64), nullable=False)
    idempotency_key = Column(String(64), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False)
    dispute_reason = Column(String(64), nullable=False)
    evidence_ids = Column(JSON, nullable=False)
    status = Column(String(32), default="SUBMITTED_TO_NETWORK") # SUBMITTED_TO_NETWORK, UNDER_INVESTIGATION, ACCEPTED, REJECTED
    received_timestamp = Column(DateTime, default=get_utc_now)

class IndependentVerification(Base):
    __tablename__ = "independent_verifications"

    id = Column(String(64), primary_key=True)
    dispute_id = Column(String(64), ForeignKey("dispute_cases.id"), nullable=False)
    bank_dispute_id = Column(String(64), nullable=True)
    verified_at = Column(DateTime, default=get_utc_now)
    verification_status = Column(String(32), nullable=False) # PASS, FAIL, PENDING, NEEDS_REVIEW
    details = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=False)

class TestScenarioResult(Base):
    __tablename__ = "test_scenario_results"

    id = Column(String(64), primary_key=True) # e.g. TC1, TC2, TC3, TC4
    name = Column(String(128), nullable=False)
    input_data = Column(JSON, nullable=False)
    expected_result = Column(String(128), nullable=False)
    actual_result = Column(String(128), nullable=False)
    status = Column(String(16), nullable=False) # PASS / FAIL
    decision_explanation = Column(Text, nullable=False)
    evidence_references = Column(JSON, nullable=False)
    verification_output = Column(JSON, nullable=False)
    executed_at = Column(DateTime, default=get_utc_now)
