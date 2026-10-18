from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

# Bank / Store Schemas
class BankTransactionSchema(BaseModel):
    id: str
    account_number: str
    card_last4: str
    order_id: Optional[str] = None
    merchant_name: str
    amount: float
    currency: str
    transaction_date: datetime
    posted_date: Optional[datetime] = None
    status: str
    refund_status: str
    description: Optional[str] = None
    has_provisional_credit: bool
    provisional_credit_amount: float
    provisional_credit_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class BankDisputeRuleSchema(BaseModel):
    id: str
    currency: str
    dispute_window_days: int
    require_merchant_contact: bool
    requires_written_explanation: bool
    allowed_reasons: List[str]

    class Config:
        from_attributes = True

class StoreOrderSchema(BaseModel):
    id: str
    customer_email: str
    customer_name: str
    order_date: datetime
    amount: float
    currency: str
    fulfillment_status: str
    delivery_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    items_summary: Optional[str] = None
    linked_transaction_id: Optional[str] = None

    class Config:
        from_attributes = True

class StoreRefundSchema(BaseModel):
    id: str
    order_id: str
    transaction_id: str
    amount: float
    currency: str
    refund_date: datetime
    reason: Optional[str] = None
    status: str
    reference_number: Optional[str] = None

    class Config:
        from_attributes = True

class StoreMessageSchema(BaseModel):
    id: str
    order_id: str
    sender: str
    timestamp: datetime
    subject: Optional[str] = None
    message_body: str
    channel: str

    class Config:
        from_attributes = True

# Dispute Creation Request
class DisputeCreateRequest(BaseModel):
    transaction_id: str
    user_stated_reason: str
    user_explanation: str
    merchant_contacted: bool = True
    supporting_notes: Optional[str] = None

# Evidence Item Schema
class EvidenceItemSchema(BaseModel):
    id: str
    dispute_id: str
    source_system: str
    source_record_id: str
    source_endpoint: str
    retrieval_timestamp: datetime
    item_type: str
    extracted_facts: Dict[str, Any]
    relevance_explanation: str
    verification_status: str
    is_user_allegation: bool

    class Config:
        from_attributes = True

# Investigation Result Schema
class InvestigationResultSchema(BaseModel):
    dispute_id: str
    decision_status: str
    decision_summary: str
    missing_requirements: List[str]
    recommended_action: str
    confidence_score: float
    plan_steps: List[str]
    tool_executions: List[Dict[str, Any]]
    evidence_items: List[EvidenceItemSchema]

# Approval Request Schema
class ApprovalRequest(BaseModel):
    packet_id: str
    packet_version: int
    action: str = Field(..., description="APPROVED, REJECTED, or RETURNED_FOR_CORRECTION")
    approver_name: str = "Compliance Officer / Cardholder"
    comments: Optional[str] = None

# Submission Request Schema
class SubmissionRequest(BaseModel):
    packet_id: str
    idempotency_key: str

# Verification Result Schema
class VerificationResultSchema(BaseModel):
    id: str
    dispute_id: str
    bank_dispute_id: Optional[str]
    verified_at: datetime
    verification_status: str
    details: Dict[str, Any]
    explanation: str

    class Config:
        from_attributes = True

# Dashboard Stats Schema
class DashboardStatsSchema(BaseModel):
    total_transactions: int
    open_disputes: int
    draft_packets: int
    resolved_or_refunded: int
    requiring_evidence: int
    status_distribution: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
