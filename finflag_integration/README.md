# FinFlag: Integrated Fraud Detection System 🚨

**Unified Dashboard & Testing Framework for 4-Member Team + Meta-Classifier**

```
FINFLAG ARCHITECTURE (Updated Role Distribution)
════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│              FINFLAG DASHBOARD (Flask Web UI)                    │
│  ├─ Single Transaction Analysis                                 │
│  ├─ Predefined Test Cases (6 scenarios)                         │
│  ├─ Real-time Results Tracking                                  │
│  ├─ Model Performance Metrics                                   │
│  └─ System Status & Component Health                            │
└──────────────────────────┬────────────────────────────────────┘
                           │
                           ▼
     ┌─────────────────────────────────────┐
     │   FINFLAG API (FastAPI/Flask)       │
     │  - Request routing & orchestration   │
     │  - Pipeline composition              │
     └────┬────────────┬────────────┬──────┘
          │            │            │
    ┌─────▼────┐  ┌────▼────┐  ┌──▼──────┐
    │ MEMBER 1 │  │ MEMBER 2│  │MEMBER 3 │
    │ Josphat  │  │Bramwel  │  │ Sharon  │
    │TELEMETRY │  │INFRA    │  │GATEWAY+ │
    │          │  │&RATELIM │  │ENCODER  │
    ├──────────┤  ├─────────┤  ├─────────┤
    │ sensor/  │  │infra/   │  │gateway/ │
    │telemetry │  │rate_    │  │fpe.py   │
    │.py       │  │limit.py │  │hashing  │
    │          │  │         │  │.py      │
    │✓IMSI     │  │✓Redis   │  │✓FPE     │
    │✓HW risk  │  │✓Token   │  │✓HMAC    │
    │✓Device   │  │✓Bucket  │  │✓Encoder │
    │  sig     │  │✓Queuing │  │  LLM    │
    └────┬─────┘  └────┬────┘  └────┬────┘
         │             │            │
         └─────────────┼────────────┘
                       │
         ┌─────────────▼──────────────┐
         │  MASKED DATA PACKET        │
         │  (Privacy-Preserved)       │
         └─────────────┬──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │   MEMBER 4: YVONNE (ML)     │
        ├──────────────────────────────┤
        │ ml_model/                    │
        │ ├─ xgboost_model.py          │
        │ ├─ autoencoder_model.py      │
        │ └─ xai_shap.py               │
        │                              │
        │ ✓ XGBoost (structured ML)    │
        │ ✓ Autoencoder (anomaly)      │
        │ ✓ SHAP (explainability)      │
        └────────────┬─────────────────┘
                     │
        ┌────────────▼──────────────┐
        │    MODEL OUTPUTS:          │
        │  ├─ xgboost_score: 0.85    │
        │  ├─ autoenc_score: 0.72    │
        │  ├─ shap_values: {...}     │
        │  └─ flags: [...]           │
        └────────────┬───────────────┘
                     │
    ┌────────────────▼─────────────────┐
    │  META-CLASSIFIER (Sharon)         │
    │  ensemble/meta_classifier.py      │
    ├───────────────────────────────────┤
    │ ✓ Weighted Ensemble Fusion        │
    │   - XGBoost: 45%                  │
    │   - Autoencoder: 30%              │
    │   - Encoder LLM: 25%              │
    │                                   │
    │ ✓ Grey Zone Detection             │
    │ ✓ Escalation Strategy             │
    │ ✓ Final Risk Assessment           │
    │ ✓ XAI Integration                 │
    └────────────┬──────────────────────┘
                 │
    ┌────────────▼──────────────┐
    │  FINAL VERDICT            │
    │  ┌──────────────────────┐ │
    │  │ Status: BLOCK/PASS   │ │
    │  │ Probability: 0.94    │ │
    │  │ Risk Level: CRITICAL │ │
    │  │ Reason: SIM_SWAP +   │ │
    │  │         WHALE_TX     │ │
    │  └──────────────────────┘ │
    └──────────────────────────┘
```

## 📋 Updated Role Distribution

### **MEMBER 1: Josphat (Endpoint Telemetry)**
**File:** `sensor/telemetry.py`
- Extract device hardware signatures
- Monitor IMSI/SIM lifecycle events
- Detect early fraud precursors

### **MEMBER 2: Bramwel (Infrastructure & Rate-Limiting)**
**File:** `infrastructure/rate_limit.py`
- Token Bucket algorithm via Redis
- Mitigate BIN enumeration attacks
- Request queuing & throttling

### **MEMBER 3: Sharon (Cryptographic Gateway + Encoder LLM)**
**File:** `gateway/fpe.py`, `gateway/hashing.py`, `gateway/encoder_llm.py`
- Format-Preserving Encryption (FPE) for PII masking
- HMAC identity linking
- **NEW:** Encoder LLM (DistilBERT) for transaction sentence understanding

### **MEMBER 4: Yvonne (ML Models & XAI)**
**File:** `ml_model/xgboost_model.py`, `ml_model/autoencoder_model.py`, `ml_model/xai_shap.py`
- XGBoost for structured numerical features
- Autoencoder for anomaly detection
- SHAP for explainable AI

### **META-CLASSIFIER: Sharon (You - Final Verdict)**
**File:** `ensemble/meta_classifier.py`
- **Weighted Fusion:** XGBoost (45%) + Autoencoder (30%) + Encoder LLM (25%)
- Grey zone escalation strategy
- Final risk assessment
- XAI integration & reason generation

---

## 🔄 Data Flow Pipeline

```
RAW TRANSACTION
      ↓
[MEMBER 1] Telemetry Extraction
  Input: {raw_phone, location, amount, ...}
  Output: {imsi_status, hardware_risk, typing_speed, ...}
      ↓
[MEMBER 2] Rate Limit Check
  Input: {user_id, timestamp}
  Output: {rate_limit_status, tokens_remaining}
  Decision: REJECT or CONTINUE
      ↓
[MEMBER 3 - SHARON] Encryption & Masking
  Input: Raw telemetry + rate limit
  Output: {masked_phone, masked_id, behavioral_hash, encoder_sentence}
      ↓
[MEMBER 4 - YVONNE] Model Inference (3 models in parallel)
  ├─ XGBoost:      structured features → fraud_prob (0-1)
  ├─ Autoencoder:  transaction pattern → anomaly_score (0-1)
  └─ LLM Encoder:  transaction sentence → nlp_score (0-1)
  Output: {xgb_score, ae_score, llm_score, shap_values}
      ↓
[META-CLASSIFIER - SHARON] Ensemble Fusion
  Inputs: All 3 model outputs
  Formula: final_score = 0.45*xgb + 0.30*ae + 0.25*llm
  Output: {status, probability, risk_level, explanation}
      ↓
✅ FINAL DECISION: BLOCK/PASS
```

---

## 📊 Files to Create/Modify

| Component | File Path | Purpose |
|-----------|-----------|---------|
| **API Server** | `api/finflag_api.py` | Orchestrates all pipeline stages |
| **Sharon - Crypto** | `gateway/fpe.py` | FPE encryption (DONE) |
| **Sharon - Crypto** | `gateway/hashing.py` | HMAC hashing (DONE) |
| **Sharon - Encoder LLM** | `gateway/encoder_llm.py` | NEW - DistilBERT text understanding |
| **Yvonne - XGBoost** | `ml_model/xgboost_model.py` | NEW - Structured ML scoring |
| **Yvonne - Autoencoder** | `ml_model/autoencoder_model.py` | NEW - Anomaly detection |
| **Yvonne - XAI** | `ml_model/xai_shap.py` | NEW - Explainability |
| **Sharon - Meta Classifier** | `ensemble/meta_classifier.py` | NEW - Final verdict engine |
| **Frontend Dashboard** | `frontend/app.py` | Flask server for web UI |
| **Frontend Dashboard** | `frontend/templates/dashboard.html` | Web interface |
| **Frontend Dashboard** | `frontend/static/dashboard.js` | Frontend logic |
| **Frontend Dashboard** | `frontend/static/dashboard.css` | Styling |

---

## ✅ What Each Component Tests

| Test Scenario | Member 1 | Member 2 | Member 3 (Sharon) | Member 4 (Yvonne) | Meta-Class | Dashboard |
|---|---|---|---|---|---|---|
| Normal transaction | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| SIM swap + whale | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rate limit exceed | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| PII masking | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| XGBoost scoring | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Autoencoder anomaly | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Encoder LLM | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| Ensemble fusion | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| XAI explanation | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| End-to-end flow | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🚀 Quick Start (5 Steps)

1. **Create directories:**
   ```bash
   mkdir -p finflag_integration/{api,gateway,ml_model,ensemble,frontend/{templates,static}}
   ```

2. **Install dependencies:**
   ```bash
   pip install flask flask-cors redis transformers torch scikit-learn xgboost shap pandas numpy
   ```

3. **Start Redis:**
   ```bash
   docker run -p 6379:6379 -d redis
   ```

4. **Run API server:**
   ```bash
   python finflag_integration/api/finflag_api.py
   ```

5. **Open dashboard:**
   ```
   http://localhost:5000
   ```

---

**Next Steps:**
1. See `ARCHITECTURE.md` for detailed data flow
2. See individual module READMEs for member implementation details
3. See `META_CLASSIFIER.md` for ensemble fusion logic
4. See `DASHBOARD.md` for UI testing instructions
