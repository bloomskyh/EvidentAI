export interface BankTransaction {
  id: str;
  account_number: string;
  card_last4: string;
  order_id?: string;
  merchant_name: string;
  amount: number;
  currency: string;
  transaction_date: string;
  posted_date?: string;
  status: string;
  refund_status: string;
  description?: string;
  has_provisional_credit: boolean;
  provisional_credit_amount: number;
}

type str = string;

export interface StoreOrder {
  id: string;
  customer_email: string;
  customer_name: string;
  order_date: string;
  amount: number;
  currency: string;
  fulfillment_status: string;
  delivery_date?: string;
  tracking_number?: string;
  items_summary?: string;
  linked_transaction_id?: string;
}

export interface EvidenceItem {
  id: string;
  source_system: string;
  source_record_id: string;
  source_endpoint: string;
  retrieval_timestamp: string;
  item_type: string;
  extracted_facts: Record<string, any>;
  relevance_explanation: string;
  verification_status: string;
  is_user_allegation: boolean;
}

export interface DisputeDetails {
  dispute: {
    id: string;
    transaction_id: string;
    order_id?: string;
    user_stated_reason: string;
    user_explanation: string;
    amount: number;
    currency: string;
    status: string;
    eligibility_decision?: any;
    provisional_credit_flag: boolean;
    is_refunded_flag: boolean;
    created_at?: string;
  };
  evidence_items: EvidenceItem[];
  latest_investigation?: {
    plan_steps: string[];
    tool_executions: Array<{
      tool_name: string;
      system: string;
      endpoint: string;
      status: string;
      timestamp: string;
      evidence_id?: string;
      count?: number;
      detail?: string;
    }>;
    decision_status: string;
    decision_summary: string;
    missing_requirements: string[];
    recommended_action: string;
    confidence_score: number;
  };
  draft_packet?: {
    id: string;
    packet_version: number;
    content_hash: string;
    is_approved: boolean;
    approval_timestamp?: string;
    approver_id?: string;
    packet_data: any;
  };
  approvals: Array<{
    id: string;
    action: string;
    approver_name: string;
    comments?: string;
    timestamp?: string;
  }>;
  verifications: Array<{
    id: string;
    bank_dispute_id?: string;
    verification_status: string;
    details: any;
    explanation: string;
    verified_at?: string;
  }>;
}

export interface DashboardStats {
  total_transactions: number;
  open_disputes: number;
  draft_packets: number;
  resolved_or_refunded: number;
  requiring_evidence: number;
  status_distribution: Record<string, number>;
  recent_activity: Array<{
    id: string;
    dispute_id: string;
    status: string;
    summary: string;
    action: string;
    timestamp?: string;
  }>;
}

export interface ScenarioResult {
  id: string;
  name: string;
  input_data: any;
  expected_result: string;
  actual_result: string;
  status: 'PASS' | 'FAIL';
  decision_explanation: string;
  evidence_references: string[];
  verification_output: any;
}
