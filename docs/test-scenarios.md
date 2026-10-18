# EvidentAI — Official Test Scenarios Specification

This document details the four official hackathon test cases, their behavioral requirements, inputs, expected results, and verification mechanisms implemented in EvidentAI.

---

## TC1 — Disputed Charge

- **Scenario Name:** Genuine Disputed Charge (Product Not Received)
- **Input:**
  - Transaction ID: `TXN-IND-1001`
  - Store Order ID: `ORD-IND-9001`
  - Disputed Amount: `₹4999.00`
  - Dispute Reason: `PRODUCT_NOT_RECEIVED`
  - Context: Settlement occurred 12 days ago; store order is marked `UNFULFILLED`; merchant email acknowledges courier delay.
- **Expected Result:** `draft packet`
- **Observed Behavior:**
  - Orchestrator verifies bank ledger entry and matches store order amount and currency.
  - Checks bank dispute rule window (12 days < 60-day deadline).
  - Corroborates customer claim against merchant logistics email.
  - Generates immutable draft packet (`READY_FOR_DRAFT`).
  - Requires explicit human approval before bank network transmission.
- **Automated Test:** `test_tc1_disputed_charge_draft_packet` (Pytest Status: PASS)

---

## TC2 — Already Refunded

- **Scenario Name:** Duplicate Dispute Prevention on Refunded Item
- **Input:**
  - Transaction ID: `TXN-IND-1002`
  - Store Order ID: `ORD-IND-9002`
  - Disputed Amount: `₹2499.00`
  - Context: Store order records a completed refund of `₹2499.00` with ARN `REF-BANK-ARN-778899`.
- **Expected Result:** `flagged resolved`
- **Observed Behavior:**
  - Evidence Retrieval Agent retrieves refund voucher and bank settlement.
  - Eligibility engine matches refund amount with disputed amount.
  - Automatically flags dispute as `ALREADY_REFUNDED` and case resolved.
  - Prevents fraudulent or duplicate dispute submission.
  - Preserves refund voucher ARN in audit ledger.
- **Automated Test:** `test_tc2_already_refunded` (Pytest Status: PASS)

---

## TC3 — Fraud Claim Without Evidence

- **Scenario Name:** Unsupported Fraud Allegation
- **Input:**
  - Transaction ID: `TXN-IND-1003`
  - Store Order ID: `ORD-IND-9003`
  - Disputed Amount: `₹8999.00`
  - Dispute Reason: `SUSPECTED_FRAUD`
  - Context: User alleges unauthorized card takeover, but no police FIR or cybercrime affidavit is attached.
- **Expected Result:** `not added`
- **Observed Behavior:**
  - Deterministic financial rules identify lack of corroborating independent documentation.
  - Customer claim is preserved strictly as an unverified user allegation.
  - Case status set to `NEEDS_MORE_EVIDENCE` with explicit missing requirements.
  - System excludes unsupported claims from formal bank evidence packet.
  - Blocks automated submission.
- **Automated Test:** `test_tc3_fraud_claim_without_evidence` (Pytest Status: PASS)

---

## TC4 — Provisional Credit

- **Scenario Name:** Active Provisional Credit Handling
- **Input:**
  - Transaction ID: `TXN-IND-1004`
  - Store Order ID: `ORD-IND-9004`
  - Disputed Amount: `₹15499.00`
  - Context: Bank statement displays an active provisional credit of `₹15499.00` pending courier inquiry.
- **Expected Result:** `not called final`
- **Observed Behavior:**
  - Retrieval agent detects `has_provisional_credit: True`.
  - Eligibility engine explicitly notes provisional credit as interim, temporary funds.
  - Does NOT misrepresent the provisional credit as a completed refund or final resolution.
  - Dispute status set to `UNDER_REVIEW`.
- **Automated Test:** `test_tc4_provisional_credit_not_final` (Pytest Status: PASS)

---

## Additional Edge Cases Tested

| Test Name | Condition Tested | Expected Outcome | Pytest Status |
|---|---|---|---|
| `test_dispute_window_expired` | Transaction age > 60 days (`TXN-IND-1005`) | `OUTSIDE_DISPUTE_WINDOW` | PASS |
| `test_nonexistent_transaction` | Bogus transaction ID (`TXN-FAKE-9999`) | HTTP 404 Not Found | PASS |
| `test_human_approval_enforced` | Submission attempted without prior approval | HTTP 403 Forbidden | PASS |
| `test_duplicate_submission` | Same idempotency key re-submitted | HTTP 409 Conflict | PASS |
| `test_independent_verification` | Post-submission ledger check | Verification `PASS` | PASS |
