# FinFlag: Distributed AI Fraud Detection 🇰🇪
FinFlag is an enterprise-grade, microservices-based fraud detection framework designed specifically for the Kenyan fintech ecosystem. It provides real-time protection against SIM Swap Account Takeovers (ATOs) and High-Velocity BIN Attacks while ensuring full compliance with the Kenya Data Protection Act (2019).

🏛️ System Architecture
The project is divided into four specialized modules that form a unified security pipeline:
1. 📡 Sensor Module (/sensor)
-Lead: Josphat

-Focus: Endpoint Telemetry.

-Function: Captures device fingerprints and monitors IMSI/SIM lifecycle changes. It generates a "Hardware Risk Score" before the transaction leaves the phone.

2. 🔐 Gateway Module (/gateway)
-Lead: Sharon

-Focus: Applied Cryptography & Privacy.

-Function: Implements Format-Preserving Encryption (FPE) using the FF1 algorithm. It masks PII (Phone numbers, Account IDs) so the AI can process data without compromising user privacy.

3. 🚦 Infrastructure Module (/infrastructure)
-Lead: Bramwel

-Focus: Distributed Systems & Resilience.

-Function: Manages traffic using a Redis-backed Token-Bucket algorithm. It protects the system from API collapse during automated botnet attacks.

4. 🧠 Intelligence Module (/ml_model)
-Lead: Yvonne 

-Focus: AI & Explainability (XAI).

-Function: A Transformer-based sequence model that analyzes transaction history. It uses SHAP to provide human-readable justifications for every "Block/Allow" decision.

🚀 Technical Stack

*Backend - Python 3.10+, FastAPI
*Artificial Intelligence - PyTorch (Transformers), SHAP (XAI)*Data & Messaging - Redis, Pandas, NumPy
*Security - FF1 Cryptography, PCI-DSS Standards
*Environment - Docker, Git, Python-Dotenv

📜 Academic Credits
-Project Name: FinFlag

-Institution: Jomo Kenyatta University of Agriculture and Technology (JKUAT)

-Supervised by: Dr. Damaris Waema

-Course: BSc. Computer Technology (Year 4)