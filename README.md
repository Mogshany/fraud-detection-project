# Role 1 – Smart Edge Telemetry & Anomaly Detection Module
### FinTech Fraud Detection AI | Final Year CS/AI/FinTech Project

---

## What This Module Does

This is **Role 1** of the distributed fraud detection system. It acts as the **Smart Edge Intelligence Layer** — analysing device, SIM, location, and behavioural data *before* any data is sent to the cloud.

Instead of just collecting raw telemetry, it **analyses + scores + detects anomalies at the edge** and produces a structured JSON payload with a **fraud risk score** for Role 2 (Cryptographic Gateway) to consume.

---

## Computational Techniques Implemented

| # | Technique | Algorithm | Purpose |
|---|-----------|-----------|---------|
| 1 | **Device Fingerprint Hashing** | SHA-256 | Identifies device identity |
| 2 | **Fingerprint Similarity** | Hamming Distance | Detects device change severity |
| 3 | **Geo-location Risk Scoring** | Haversine Formula | Measures physical travel distance |
| 4 | **Impossible Travel Detection** | Speed calculation | Flags location jumps |
| 5 | **SIM Lifecycle Anomaly** | Rule-Based Inference | Detects SIM swap timing |
| 6 | **Statistical Anomaly Detection** | Z-Score Analysis | Finds outlier login times |
| 7 | **Transaction Velocity Analysis** | Sliding Window Average | Detects velocity spikes |
| 8 | **Edge Risk Scoring** | Weighted Formula | Aggregates all signals into one score |

---

## Project Structure

```
role1_edge_telemetry/
├── src/
│   ├── __init__.py
│   └── edge_telemetry.py      ← All algorithms (main source file)
├── tests/
│   └── test_edge_telemetry.py ← Unit tests for every technique
├── demo.py                    ← Demo runner with 4 real scenarios
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone (for teammates)
```bash
git clone https://github.com/YOUR_USERNAME/fintech-fraud-role1.git
cd fintech-fraud-role1
```

### 2. Run the Demo
```bash
python demo.py
```

You will see 4 scenarios tested:
- ✅ Normal login → **LOW risk**
- 🚨 SIM swap + new device → **HIGH risk**
- 🚨 Geo-location jump Nairobi → Lagos → **HIGH risk**
- ⚠️ Late-night anomalous login → **MEDIUM risk**

### 3. Run the Tests
```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Output Payload (sent to Role 2)

```json
{
  "metadata": {
    "module": "Role1-EdgeTelemetry",
    "version": "1.0.0",
    "timestamp_utc": "2025-01-15T14:30:00Z",
    "user_id": "USR-001"
  },
  "analyses": {
    "device_fingerprint": {
      "fingerprint": "sha256_hash_here",
      "is_new_device": false,
      "similarity_score": 1.0,
      "risk_flag": "NONE"
    },
    "geo_location": {
      "distance_km": 3.2,
      "speed_kmh": 45.0,
      "risk_flag": "NONE"
    },
    "sim_lifecycle": {
      "imsi_changed": false,
      "risk_flag": "NONE"
    },
    "statistical_time": {
      "z_score": 0.23,
      "risk_flag": "NONE"
    }
  },
  "risk_assessment": {
    "risk_score": 0.0,
    "risk_level": "LOW",
    "recommendation": "ALLOW – Forward encrypted payload to Role 2."
  },
  "forward_to_role2": true
}
```

---

## How the Risk Score is Calculated

```
Risk Score = (Device Score × 0.35)
           + (SIM Score    × 0.30)
           + (Location Score × 0.20)
           + (Time Score   × 0.15)
```

| Flag | Score |
|------|-------|
| NONE | 0.0 |
| SUSPICIOUS | 0.5 |
| HIGH | 1.0 |

| Risk Score | Level | Action |
|------------|-------|--------|
| 0.00 – 0.34 | LOW | ALLOW → Forward to Role 2 |
| 0.35 – 0.64 | MEDIUM | CHALLENGE → Require OTP |
| 0.65 – 1.00 | HIGH | BLOCK → Forward to Role 4 ML |

---

## How Teammates Can Use This

**Role 2 (Cryptographic Gateway):**
- Receive the JSON payload from `EdgeTelemetryModule.process()`
- Read `forward_to_role2` to decide whether to accept
- Apply FPE to the sensitive fields

**Role 3 (Distributed Systems):**
- The payload is a single JSON object — easy to publish to Redis/Kafka
- Use `risk_level` for priority queue routing

**Role 4 (AI Scientist):**
- The `analyses` dict gives you clean feature vectors
- `device.similarity_score`, `geo_location.distance_km`, `sim_lifecycle.imsi_changed`
- Ready to feed directly into your ML model as features

---

## Dependencies

**Zero external dependencies** for the core module. Uses Python standard library only:
- `hashlib` – SHA-256 fingerprinting
- `math` – Haversine formula
- `statistics` – Z-score calculation
- `json`, `time`, `datetime`, `collections` – utilities

Optional: `pytest` for running tests.

---

## Author

**Role 1 – Endpoint & Telemetry Engineer**
Smart Edge Intelligence Module | FinTech Fraud Detection AI
