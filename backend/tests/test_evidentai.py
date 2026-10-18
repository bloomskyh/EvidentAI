import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base
from app.seed import seed_database
from app.models import DisputeCase, DraftPacket, BankSubmittedDispute

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_evidentai.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_database(db)
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

# -------------------------------------------------------------
# TC1: Disputed Charge (Product Not Received)
# Expected result: draft packet
# -------------------------------------------------------------
def test_tc1_disputed_charge_draft_packet():
    response = client.post("/api/disputes", json={
        "transaction_id": "TXN-IND-1001",
        "user_stated_reason": "PRODUCT_NOT_RECEIVED",
        "user_explanation": "Noise cancelling headphones were never delivered.",
        "merchant_contacted": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["investigation"]["status"] == "READY_FOR_DRAFT"
    assert data["investigation"]["draft_packet_id"] is not None
    assert "ELIGIBILITY_VERIFIED" in data["investigation"]["decision_summary"] or "All eligibility criteria met" in data["investigation"]["decision_summary"]

# -------------------------------------------------------------
# TC2: Already Refunded
# Expected result: flagged resolved
# -------------------------------------------------------------
def test_tc2_already_refunded():
    response = client.post("/api/disputes", json={
        "transaction_id": "TXN-IND-1002",
        "user_stated_reason": "PRODUCT_NOT_RECEIVED",
        "user_explanation": "Did not receive item.",
        "merchant_contacted": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["investigation"]["status"] == "ALREADY_REFUNDED"
    assert "already issued a full verified refund" in data["investigation"]["decision_summary"]
    # Check that case is flagged resolved
    assert "Case is flagged resolved" in data["investigation"]["decision_summary"]

# -------------------------------------------------------------
# TC3: Fraud Claim Without Evidence
# Expected result: not added
# -------------------------------------------------------------
def test_tc3_fraud_claim_without_evidence():
    response = client.post("/api/disputes", json={
        "transaction_id": "TXN-IND-1003",
        "user_stated_reason": "SUSPECTED_FRAUD",
        "user_explanation": "Card details were compromised.",
        "merchant_contacted": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["investigation"]["status"] == "NEEDS_MORE_EVIDENCE"
    assert any("Police Complaint" in item for item in data["investigation"]["missing_requirements"])
    assert "objective evidence is missing" in data["investigation"]["decision_summary"]

# -------------------------------------------------------------
# TC4: Provisional Credit
# Expected result: not called final
# -------------------------------------------------------------
def test_tc4_provisional_credit_not_final():
    response = client.post("/api/disputes", json={
        "transaction_id": "TXN-IND-1004",
        "user_stated_reason": "PRODUCT_NOT_RECEIVED",
        "user_explanation": "Lost monitor, got provisional credit from bank.",
        "merchant_contacted": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["investigation"]["status"] == "UNDER_REVIEW"
    assert "NOT a final refund" in data["investigation"]["decision_summary"]
    assert "temporary interim credit" in data["investigation"]["decision_summary"]

# -------------------------------------------------------------
# Edge Case: Expired Dispute Window
# -------------------------------------------------------------
def test_dispute_window_expired():
    response = client.post("/api/disputes", json={
        "transaction_id": "TXN-IND-1005",
        "user_stated_reason": "PRODUCT_NOT_RECEIVED",
        "user_explanation": "Purchased 95 days ago.",
        "merchant_contacted": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["investigation"]["status"] == "OUTSIDE_DISPUTE_WINDOW"

# -------------------------------------------------------------
# Edge Case: Non-existent transaction ID
# -------------------------------------------------------------
def test_nonexistent_transaction():
    response = client.post("/api/disputes", json={
        "transaction_id": "TXN-FAKE-9999",
        "user_stated_reason": "PRODUCT_NOT_RECEIVED",
        "user_explanation": "Fake transaction.",
        "merchant_contacted": True
    })
    assert response.status_code == 404

# -------------------------------------------------------------
# Human Approval Enforcement & Idempotent Submission
# -------------------------------------------------------------
def test_human_approval_enforced_and_verification():
    # 1. Create a draft dispute
    res_disp = client.post("/api/disputes", json={
        "transaction_id": "TXN-IND-1001",
        "user_stated_reason": "PRODUCT_NOT_RECEIVED",
        "user_explanation": "Rahul Sharma - headphones missing.",
        "merchant_contacted": True
    })
    dispute_id = res_disp.json()["dispute_id"]
    packet_id = res_disp.json()["investigation"]["draft_packet_id"]

    # 2. Attempt submission without approval -> Must be 403 FORBIDDEN
    idempotency_key = str(uuid.uuid4())
    sub_fail = client.post(f"/api/disputes/{dispute_id}/submit-to-bank", json={
        "packet_id": packet_id,
        "idempotency_key": idempotency_key
    })
    assert sub_fail.status_code == 403
    assert "has not received explicit human cardholder approval" in sub_fail.json()["detail"]

    # 3. Explicit Human Approval
    appr_res = client.post(f"/api/disputes/{dispute_id}/approve", json={
        "packet_id": packet_id,
        "packet_version": 1,
        "action": "APPROVED",
        "approver_name": "Rahul Sharma (Cardholder)",
        "comments": "Reviewed all facts and verified accuracy."
    })
    assert appr_res.status_code == 200
    assert appr_res.json()["is_approved"] is True

    # 4. Now Submit -> Success
    sub_succ = client.post(f"/api/disputes/{dispute_id}/submit-to-bank", json={
        "packet_id": packet_id,
        "idempotency_key": idempotency_key
    })
    assert sub_succ.status_code == 200
    bank_sub_id = sub_succ.json()["bank_submission_id"]
    assert sub_succ.json()["verification"]["status"] == "PASS"

    # 5. Duplicate Submission attempt with same idempotency key -> Must be 409 CONFLICT
    sub_dup = client.post(f"/api/disputes/{dispute_id}/submit-to-bank", json={
        "packet_id": packet_id,
        "idempotency_key": idempotency_key
    })
    assert sub_dup.status_code == 409
    assert "DUPLICATE SUBMISSION BLOCKED" in sub_dup.json()["detail"]

# -------------------------------------------------------------
# Test Scenarios Runner API
# -------------------------------------------------------------
def test_scenario_runner_endpoint():
    res = client.post("/api/scenarios/run-all")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 4
    for sc in scenarios:
        assert sc["status"] == "PASS"
