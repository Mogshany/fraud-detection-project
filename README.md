# FinFlag 🛡️
### Privacy-Preserving AI Fraud Detection for the Kenyan Fintech Ecosystem

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-085041?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-3C3489?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Redis](https://img.shields.io/badge/Redis-7.2-red?style=flat-square&logo=redis&logoColor=white)](https://redis.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![JKUAT](https://img.shields.io/badge/Project-JKUAT%20Final%20Year-blue?style=flat-square)](https://jkuat.ac.ke)

---

## What is FinFlag?

FinFlag is a distributed, real-time fraud detection system built specifically for the **M-Pesa mobile money ecosystem** in Kenya. It uses a two-brain hybrid AI architecture to identify fraudulent transactions — including SIM-swap Account Takeover attacks — **without ever storing or exposing the real identity of any user**.

The core research contribution is a **Privacy-Preserving AI Pipeline**: personal data (phone numbers, National IDs) is cryptographically masked at the point of entry using Format-Preserving Encryption (FF1/NIST SP 800-38G), and the AI layer operates entirely on masked data. A fraudster is caught. A user's identity is never revealed.

---

## The Problem

Mobile money fraud in Kenya costs consumers hundreds of millions of shillings annually. The most damaging attack is **SIM-Swap Account Takeover (ATO)**:

1. A fraudster convinces a mobile carrier to reassign a victim's phone number to a new SIM
2. They immediately initiate a large M-Pesa transfer from an unfamiliar location
3. By the time the victim notices, the money is gone

Existing fraud systems either expose user PII to AI models (a privacy violation) or operate too slowly to block transactions in real time. FinFlag solves both problems.

---

## Architecture — The Relay Race

The system operates across four computing domains in sequence:

```
[Edge Sensor]  →  [The Shield]  →  [The Handshake]  →  [The Brain]
 Raw PII data      FPE + HMAC       Redis Queue         AI Verdict
 Member 1          Sharon           Member 3            Sharon + Yvonne
```

| Domain | Component | Owner | Technology |
|---|---|---|---|
| Capture | `data_bridge.py` | Member 1 | PaySim / M-Pesa sensor feed |
| Shield | `gateway/` | Sharon | FastAPI · FF1 FPE · HMAC-SHA256 |
| Handshake | Redis Stack | Member 3 | Redis 7.2 · Docker Compose |
| Brain | `ml_model/` | Sharon + Yvonne | DistilBERT · XGBoost · SHAP |

---

## Team & Roles

| Member | Role | Computing Area | Key Deliverable |
|---|---|---|---|
| **Sharon** | Repo Owner · Cryptographic Gateway · Encoder LLM | Applied Cryptography · NLP · Deep Learning | `gateway/fpe.py`, `gateway/hashing.py`, `gateway/main.py`, `ml_model/encoder_model.py`, `ml_model/tokenizer_service.py` |
| **Josphat** | Sensor & Edge Engineer | Edge Computing · Signal Processing | `data_bridge.py` — streams PaySim data, injects Kenyan metadata |
| **Bramwel** | Infrastructure & DevOps | Distributed Systems · MLOps | `docker-compose.yml`, Redis Stack config, model serving |
| **Yvonne** | Intelligence & NLP Engineer | Machine Learning · Explainability | XGBoost classifier, `ml_model/shap_explainer.py` |

---

## Two-Brain Hybrid AI

FinFlag uses two independent AI models whose scores are fused by an Ensemble Decision Engine:

```
Financial Sentence  →  Encoder LLM (DistilBERT)  →  LLM score
                                                            ↓
Feature Vector      →  Structured ML (XGBoost)   →  Struct score  →  BLOCK / PASS
                              ↓
                         SHAP explanation
```

**Brain A — Encoder LLM (Sharon):** Reads the full transaction as a natural-language sentence. Uses self-attention to detect fraud patterns that only appear when multiple signals combine — e.g. `SWAPPED + remote + whale + transfer` = Account Takeover.

**Brain B — Structured ML (Yvonne):** Reads a 16-feature numeric vector. Fast, explainable, and excellent at hard-rule violations — e.g. amount 10× the account average, 3am withdrawal.

**Ensemble:** Weighted average by default. Escalation strategy activates the LLM only for borderline cases (score 0.25–0.65), saving compute on clear-cut transactions.

---

## Privacy by Architecture

No raw PII enters the AI pipeline. Ever.

```
0722123456  ──[FF1 FPE]──►  0722891043   (same format, mathematically unreadable)
0722123456  ──[HMAC]────►  FF-4a7b2c9d… (stable token, non-reversible)
```

**Format-Preserving Encryption (FF1):** The encrypted phone number is still a valid 10-digit Kenyan number. It passes every downstream format check. Only the holder of the AES-256 key can reverse it — for court-ordered audits.

**Salted HMAC-SHA256:** The behavioral token links Transaction #5 and Transaction #42 to the same masked identity, enabling pattern detection. It cannot be reversed without the secret salt.

**Tweak binding:** The FPE tweak is bound to the `sensor_id`, meaning the same phone number produces a different ciphertext on different sensors. Cross-sensor correlation attacks are prevented.

---

## Data Dictionary

### Input — `RawTransactionPacket`
| Field | Type | Example |
|---|---|---|
| `sensor_id` | string | `"JKUAT-SN-001"` |
| `imsi_status` | enum | `ACTIVE` \| `SWAPPED` \| `CLONED` \| `UNKNOWN` |
| `hardware_risk` | float [0,1] | `0.72` |
| `typing_speed` | float (kpm) | `38.5` |
| `raw_phone` | string (10 digits) | `"0722123456"` |
| `amount` | float (KES) | `4500.0` |
| `transaction_type` | enum | `TRANSFER` \| `WITHDRAWAL` \| `PAYMENT` \| `DEPOSIT` |
| `location` | string | `"Juja"` |
| `national_id` | string (opt.) | `"12345678"` |
| `recipient_phone` | string (opt.) | `"0733999888"` |

### Output — `FraudVerdict`
| Field | Type | Example |
|---|---|---|
| `fraud_probability` | float [0,1] | `0.97` |
| `status` | enum | `BLOCK` \| `PASS` |
| `risk_level` | enum | `LOW` \| `MEDIUM` \| `HIGH` \| `CRITICAL` |
| `llm_score` | float | `0.97` |
| `struct_score` | float | `1.00` |
| `fusion_method` | string | `"escalated_to_llm"` |
| `behavioral_hash` | string | `"FF-4a7b2c9d..."` |

---

## Project Structure

```
finflag/
│
├── gateway/                        # Sharon — Cryptographic Gateway
│   ├── __init__.py
│   ├── fpe.py                      # FF1 Format-Preserving Encryption (NIST SP 800-38G)
│   ├── hashing.py                  # Salted HMAC-SHA256 behavioral tokens
│   └── main.py                     # FastAPI Shield — /ingest, /verify, /health
│
├── ml_model/                       # Sharon + Yvonne — Intelligence Layer
│   ├── __init__.py
│   ├── tokenizer_service.py        # Masked packet → sentence + feature vector
│   ├── encoder_model.py            # DistilBERT encoder + EnsembleDecisionEngine
│   ├── pipeline.py                 # End-to-end integration (demo + tests)
│   └── shap_explainer.py           # Yvonne — XGBoost + SHAP explainability
│
├── data_bridge/                    # Josphat — Edge Sensor Layer
│   └── data_bridge.py              # PaySim streamer + Kenya-nization
│
├── infra/                          # Bramwel — Infrastructure
│   ├── docker-compose.yml          # One-command system startup
│   └── redis.conf                  # Redis Stack configuration
│
├── tests/
│   └── test_crypto.py              # FPE + HMAC unit tests
│
├── requirements.txt                # All Python dependencies
├── setup_env.ps1                   # Windows setup script (generates .env)
├── setup_env.sh                    # Mac/Linux setup script
└── .gitignore                      # Excludes .env and secret keys
```

---

## Quick Start

### Prerequisites
- Python 3.10 or later
- Docker Desktop (for Redis)
- Git

### 1. Clone the repository

```bash
git clone [https://github.com/Mogshany/fraud-detection-project.git]
cd fraud-detection-project
```

### 2. Run the setup script

**Windows (PowerShell):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup_env.ps1
```

**Mac / Linux:**
```bash
bash setup_env.sh
```

The setup script will:
- Create a Python virtual environment (`.venv`)
- Install all dependencies from `requirements.txt`
- Generate a `.env` file with freshly generated AES-256 FPE key and HMAC salt

### 3. Start Redis (requires Docker)

```bash
docker run -d --name finflag-redis -p 6379:6379 redis/redis-stack:latest
```

### 4. Run the full pipeline demo

```bash
python -m ml_model.pipeline
```

You should see three test transactions processed end-to-end:
```
🟢 PASS  p=0.0000  risk=LOW      — Routine 150 KES payment in Juja
🔴 BLOCK p=1.0000  risk=CRITICAL — SIM-swap + 175,000 KES transfer
🟡 PASS  p=0.2300  risk=MEDIUM   — Grey zone 55,000 KES withdrawal
```

### 5. Start the Gateway API

```bash
uvicorn gateway.main:app --reload --port 8000
```

Interactive API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Run the tests

```bash
pytest tests/ -v
```

---

## API Endpoints

### `POST /ingest`
Submit a raw transaction for masking and fraud scoring.

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "JKUAT-SN-001",
    "imsi_status": "SWAPPED",
    "hardware_risk": 0.88,
    "raw_phone": "0722123456",
    "amount": 175000,
    "transaction_type": "TRANSFER",
    "location": "UNKNOWN",
    "recipient_phone": "0733999888"
  }'
```

**Response:**
```json
{
  "masked_sender_phone": "0722891043",
  "behavioral_hash": "FF-4a7b2c9d3e1f8a7b",
  "sensor_id": "JKUAT-SN-001",
  "imsi_status": "SWAPPED",
  "hardware_risk": 0.88,
  "amount": 175000.0,
  "transaction_type": "TRANSFER",
  "location": "UNKNOWN",
  "processing_time_ms": 2.341
}
```

### `POST /verify`
Audit endpoint — verify a real phone number matches a stored behavioral token.

```bash
curl -X POST http://localhost:8000/verify \
  -H "Content-Type: application/json" \
  -d '{"raw_phone": "0722123456", "token_to_check": "FF-4a7b2c9d..."}'
```

### `GET /health`
```json
{"status": "ok", "redis": "connected", "crypto": "ready"}
```

---

## Environment Variables

The `.env` file is generated automatically by the setup script. **Never commit it to Git.**

| Variable | Description | How to generate |
|---|---|---|
| `FINFLAG_FPE_KEY` | 64-char hex AES-256 key for FF1 encryption | `python -c "import os; print(os.urandom(32).hex())"` |
| `FINFLAG_HMAC_SALT` | Base64-encoded 32-byte HMAC salt | `python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` (default) |

---

## Running with Docker Compose (Member 3)

```bash
docker compose up
```

This starts three containers:
- `finflag-gateway` — FastAPI on port 8000
- `finflag-redis` — Redis Stack on port 6379
- `finflag-ml` — Pipeline worker (reads from Redis queue)

---

## Key Technical Concepts

### FF1 Format-Preserving Encryption
FF1 is a NIST-standardised (SP 800-38G) encryption algorithm that outputs ciphertext in the same format as its input. A 10-digit phone number encrypts to a 10-digit phone number. This is critical for FinFlag because M-Pesa infrastructure validates phone formats — regular encryption would break every downstream system.

The algorithm uses a 10-round Feistel network with AES-256 as the pseudorandom function. Each round mixes the left and right halves of the input using a keystream derived from the AES output, the round number, and a context-binding tweak.

### HMAC Behavioral Tokens
HMAC-SHA256 with a secret salt produces a stable, non-reversible token for each identity. The same phone number always produces the same token with the same salt — enabling the AI to cluster transactions by identity — but the token cannot be reversed to recover the phone number without the salt.

### DistilBERT Encoder LLM
DistilBERT is a lightweight transformer model with 6 encoder layers and 66M parameters. FinFlag fine-tunes it on synthetic M-Pesa transaction data formatted as natural-language sentences. The `[CLS]` token embedding from the final layer is fed into a two-layer classification head that outputs a fraud probability.

### SHAP Explainability
SHAP (SHapley Additive exPlanations) decomposes the XGBoost model's prediction for each transaction into per-feature contributions. This produces human-readable explanations like "blocked primarily because sim_swapped (+0.41) and is_whale (+0.31)" — essential for regulatory compliance in fintech.

---

## 4-Week Sprint Plan

| Week | Focus | Key Tasks |
|---|---|---|
| **Week 1** | Environment & Security | `setup_env.ps1`, FPE module, HMAC module, Gateway API |
| **Week 2** | Pipeline connection | Redis integration, `data_bridge.py`, Tokenizer, Docker Compose |
| **Week 3** | AI training | DistilBERT fine-tuning, XGBoost training, SHAP, Ensemble engine |
| **Week 4** | Integration & presentation | End-to-end tests, documentation, JKUAT presentation prep |

---

## Fraud Patterns Detected

| Pattern | Signals | Detection method |
|---|---|---|
| SIM-Swap ATO | `imsi_status=SWAPPED` + large amount + new recipient | Both LLM (context) + XGBoost (rules) |
| Bot-driven fraud | `typing_speed > 200 kpm` (superhuman) | XGBoost feature rule |
| Unusual location | `location_known=False` + high amount | XGBoost + LLM sentence context |
| Whale transaction | `amount >= 150,000 KES` | XGBoost hard rule |
| Cloned SIM | `imsi_status=CLONED` | Highest weight in both models |
| Round-number scripting | `amount % 500 == 0` | XGBoost secondary signal |

---

## Academic Context

This project is submitted in partial fulfilment of the requirements for the Bachelor of Science in Computer Science at **Jomo Kenyatta University of Agriculture and Technology (JKUAT)**, Kenya.

**Research contribution:** The system demonstrates that a Transformer-based fraud detection model can operate with full accuracy on Format-Preserving Encrypted data — proving that privacy and intelligence are not mutually exclusive in fintech AI systems.

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `cryptography` | 42.0+ | AES-ECB primitives for FF1 FPE |
| `fastapi` | 0.110+ | Gateway REST API |
| `uvicorn` | 0.29+ | ASGI server |
| `pydantic` | 2.0+ | Data Dictionary validation |
| `redis` | 5.0+ | Message queue client |
| `torch` | 2.2+ | DistilBERT training and inference |
| `transformers` | 4.40+ | Hugging Face DistilBERT |
| `xgboost` | 2.0+ | Structured ML classifier |
| `shap` | 0.44+ | Feature-level explainability |
| `scikit-learn` | 1.4+ | Meta-classifier utilities |
| `pytest` | 8.0+ | Unit and integration tests |

Install all: `pip install -r requirements.txt`

> **Note:** `torch` and `transformers` are commented out in `requirements.txt` by default (≈2 GB download). Uncomment them before Week 3 training.

---

## Security Notes

- The `.env` file containing cryptographic keys is excluded from Git via `.gitignore`. Never commit it.
- The `/verify` endpoint is for authorised audit use only. Add API key middleware before any production deployment.
- FPE keys should be rotated periodically. Rotating the key re-masks all historical data — plan accordingly.
- The HMAC salt should be stored in a secrets manager (HashiCorp Vault, AWS Secrets Manager) in production, never on disk alongside the hashed data.

---

## Licence

MIT Licence — see [LICENSE](LICENSE) for details.

---

## Acknowledgements

- PaySim synthetic dataset — Kaggle (Lopez-Rojas et al.)
- DistilBERT — Hugging Face / Sanh et al. (2019)
- FF1 algorithm — NIST Special Publication 800-38G
- SHAP — Lundberg & Lee (2017)
- Project supervisor and the JKUAT Computer Science department
