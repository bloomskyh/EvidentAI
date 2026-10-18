# EvidentAI — Chargeback Evidence Assistant

> **Every Claim. Backed by Evidence.**  
> *Official Problem Statement: Chargeback Evidence Assistant — FinTech & Financial AI*  
> *Agentic AI Hackathon 2026 by Ziro.Digital*

EvidentAI is an agentic AI assistant that automates dispute evidence collection, enforces deterministic financial checks, prepares immutable evidence packets for mandatory human approval, and independently verifies submission state against simulated banking networks.

---

## 🌟 Key Features

1. **Agentic Orchestrator & Tool Trace:** Coordinates evidence gathering across Mock Bank and Mock Store APIs, generating a transparent audit log of tool calls.
2. **Zero-Hallucination Deterministic Financial Rules:** Non-negotiable checks (dispute window age, amount reconciliation, refund identification) are evaluated in deterministic code.
3. **Mandatory Backend-Enforced Human Approval:** Submissions require explicit human cardholder consent; unapproved packets return `403 Forbidden`.
4. **Cryptographic Integrity & SHA-256 Hashing:** Every evidence packet is hashed; any post-approval edit invalidates prior approval.
5. **Idempotent Bank Network Submissions:** Duplicate requests sharing an idempotency key return `409 Conflict`.
6. **Independent Verification Component:** Queries the banking network independently post-submission to verify ledger state.
7. **Document Generation:** Exports official dispute packets in both structured JSON and formatted PDF.
8. **Automated Test Scenarios Suite:** Dedicated UI and Pytest suite testing TC1 through TC4 and edge cases.

---

## 📂 Repository Structure

```
EvidentAI/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application & lifecycle
│   │   ├── models.py               # SQLAlchemy persistent schema
│   │   ├── database.py             # DB connection & session factory
│   │   ├── seed.py                 # Synthetic banking & merchant data
│   │   ├── bank_api.py             # Mock Bank API service
│   │   ├── store_api.py            # Mock Store API service
│   │   ├── core_api.py             # EvidentAI Core dispute endpoints
│   │   ├── orchestrator.py         # Orchestrator Agent
│   │   ├── evidence_retriever.py   # Evidence retrieval tools
│   │   ├── eligibility_engine.py   # Deterministic Financial Rules
│   │   ├── packet_agent.py         # Evidence packet compiler & hasher
│   │   ├── verifier.py             # Independent verification engine
│   │   └── schemas.py              # Pydantic request/response models
│   └── tests/
│       └── test_evidentai.py       # Pytest suite for TC1-TC4 & edge cases
├── frontend/
│   ├── src/
│   │   ├── components/Navbar.tsx
│   │   ├── pages/DashboardPage.tsx
│   │   ├── pages/TransactionsPage.tsx
│   │   ├── pages/NewDisputeWizard.tsx
│   │   ├── pages/InvestigationWorkspace.tsx
│   │   ├── pages/EvidencePacketPage.tsx
│   │   ├── pages/ApprovalVerificationPage.tsx
│   │   ├── pages/TestScenariosPage.tsx
│   │   ├── App.tsx
│   │   └── types.ts
│   └── vite.config.ts
├── docs/
│   ├── architecture.md             # Architecture & data flow diagrams
│   └── test-scenarios.md           # TC1-TC4 scenario specifications
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart Guide (Local Windows Execution)

### Prerequisites
- **Python 3.11+** installed (`python --version`)
- **Node.js 18+ & npm** installed (`node --version`)

---

### Step 1: Backend Setup & Startup

Open a PowerShell terminal:

```powershell
# Navigate to backend
cd backend

# Install dependencies
python -m pip install fastapi uvicorn sqlalchemy reportlab pytest pytest-asyncio python-multipart

# Start FastAPI server on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend starts at `http://127.0.0.1:8000`.  
Interactive Swagger documentation is available at: `http://127.0.0.1:8000/docs`.

---

### Step 2: Frontend Setup & Startup

Open a second terminal:

```powershell
# Navigate to frontend
cd frontend

# Install dependencies (if not already installed)
npm.cmd install

# Start Vite development server
npm.cmd run dev
```

The frontend dashboard will be live at: `http://localhost:5173`.

---

## 🧪 Running Automated Tests

Run the complete Pytest suite to verify all official test scenarios, idempotency, approval restrictions, and edge cases:

```powershell
cd backend
$env:PYTHONPATH="."
python -m pytest tests -v
```

### Verified Scenarios:
- **TC1 — Disputed charge:** `draft packet` produced with verified merchant delay proof.
- **TC2 — Already refunded:** `flagged resolved` preventing duplicate chargeback.
- **TC3 — Fraud claim without evidence:** Unsupported fraud claims `not added` to formal packet.
- **TC4 — Provisional credit:** Provisional credit explicitly labeled as temporary; `not called final`.
- **Approval Enforcement:** Direct submission without prior approval returns `HTTP 403 Forbidden`.
- **Idempotent Submission:** Re-submitting with identical key returns `HTTP 409 Conflict`.
- **Independent Verification:** Direct post-submission bank network audit passes.

---

## 🔒 Security & Data Integrity Design
- **No Real Bank Accounts:** All records and services are mock endpoints with persistent synthetic data.
- **Idempotency Keys:** Protects against network duplicate retries.
- **Immutability:** SHA-256 hash checks prevent tampering between approval and submission.
- **Zero Secrets Leaked:** Environment variables stored in `.env.example`; no keys committed.
