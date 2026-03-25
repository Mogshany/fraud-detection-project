FinFlag: Distributed AI Fraud Detection 🇰🇪
A Microservices-based Architecture for Detecting SIM Swap & BIN Enumeration Attacks in the Kenyan Fintech Ecosystem.

📌 Project Overview
As Kenya’s mobile-money ecosystem grows, so does the sophistication of cyber-fraud. Sentinel-AI is a next-generation fraud detection system designed to bridge the gap between telecommunications telemetry and financial banking security.

Unlike traditional "black-box" systems, Sentinel-AI uses a Distributed Microservices Architecture to identify fraud precursors (like SIM Swaps) before financial damage occurs, while remaining fully compliant with the Kenya Data Protection Act (2019).

🏗️ The 4-Module Architecture
The system is divided into four specialized modules, each developed by a core team member:

1. Endpoint Telemetry Module (Member 1)
Role: Early warning system.

Function: Extracts hardware signatures and monitors IMSI/SIM lifecycle anomalies.

Impact: Identifies SIM Swap precursors at the device level before a transaction is even initiated.

2. Distributed Infrastructure & Rate-Limiting (Member 3)
Role: Volumetric protection.

Function: Implements a Token-Bucket algorithm via Redis to mitigate high-velocity BIN enumeration attacks.

Impact: Prevents API collapse during botnet-driven "brute force" card testing.

3. Cryptographic Gateway Service (Member 2)
Role: Privacy & Compliance.

Function: Utilizes Format-Preserving Encryption (FPE) to mask PII (Personally Identifiable Information).

Impact: Ensures the AI processes data without seeing raw phone numbers or bank accounts, satisfying PCI-DSS and local data laws.

4. Transformer-Based XAI Engine (Yvonne Kwaya)
Role: The Intelligence Core.

Function: Uses Sequence-based Transformers to analyze transaction patterns and SHAP (Explainable AI) for justifications.

Impact: Provides sub-200ms fraud decisions with human-readable explanations (e.g., "Blocked due to sudden IMSI change").

🚀 Technical Stack
Language: Python 3.10+

AI/ML: PyTorch, SHAP, Scikit-learn

Backend: FastAPI (Asynchronous API)

Data/Cache: Redis (Distributed Lock & Rate Limiting)

Security: FF1 (Format Preserving Encryption)

Dataset: PaySim (Synthetic Mobile Money Simulator)

📊 The Unified Data Schema
All modules communicate via a unified JSON packet. This ensures seamless data flow from the hardware sensor to the AI engine.

JSON
{
  "transaction_id": "JKUAT-2026-X",
  "telemetry": { "imsi_status": "CHANGED", "hardware_risk": 0.88 },
  "infrastructure": { "rate_limit": "PASSED", "queue_ms": 12 },
  "crypto": { "masked_id": "0722***593", "protocol": "FPE-FF1" },
  "ai_decision": { "result": "BLOCK", "probability": 0.94, "reason": "SIM Swap Detected" }
}

🛠️ Installation & Setup
Clone the repository:
git clone https://github.com/Mogshany/fraud-detection-project.git
cd fraud-detection-project

Install Dependencies:
pip install -r requirements.txt

Start Redis (for Member 3's module):
docker run -p 6379:6379 -d redis

Run the API:
uvicorn main:app --reload

🎓 Academic Context
Institution: Jomo Kenyatta University of Agriculture and Technology (JKUAT)

Course: BSc. Computer Technology (Year 4)

Unit: BCT 2406: Project

Supervisor: Dr. Damaris Waema

🤝 The Team
Josphat Mwaura (Endpoint & Hardware Telemetry)

Sharon Nyaboke (Applied Cryptography & Privacy)

Bramwel Shaw (Distributed Systems & Performance)

Yvonne Kwaya (AI & Explainability Specialist)
