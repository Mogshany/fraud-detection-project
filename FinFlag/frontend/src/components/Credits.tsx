import React from 'react';
import '../styles/credits.css';

export const Credits: React.FC = () => {
  return (
    <div className="credits-section">
      <h2>👥 Development Team & Contributions</h2>
      
      <div className="team-grid">
        <div className="team-member edge-computing">
          <div className="member-icon">📡</div>
          <h3>Edge Computing & Signal Processing</h3>
          <p className="member-name">Josphat</p>
          <ul className="contributions">
            <li>IoT Sensor Data Collection</li>
            <li>Real-time Signal Processing</li>
            <li>Edge Node Deployment</li>
            <li>IMSI Detection & Validation</li>
            <li>Hardware Risk Assessment</li>
            <li>Low-latency Data Acquisition</li>
          </ul>
        </div>

        <div className="team-member cryptography">
          <div className="member-icon">🔐</div>
          <h3>Applied Cryptography</h3>
          <p className="member-name">Sharon</p>
          <ul className="contributions">
            <li>AES-256-GCM Encryption</li>
            <li>HMAC-SHA256 Integrity Verification</li>
            <li>Secure Key Derivation (PBKDF2)</li>
            <li>Data Anonymization & Masking</li>
            <li>Privacy-Preserving Hashing</li>
            <li>End-to-End Encryption Pipeline</li>
          </ul>
        </div>

        <div className="team-member distributed-systems">
          <div className="member-icon">⚙️</div>
          <h3>Distributed Systems & MLOps</h3>
          <p className="member-name">Bramwel</p>
          <ul className="contributions">
            <li>Fraud Detection ML Models</li>
            <li>Model Training & Deployment</li>
            <li>Distributed Data Processing</li>
            <li>Real-time Prediction Pipeline</li>
            <li>System Scalability & Load Balancing</li>
            <li>Infrastructure Orchestration</li>
          </ul>
        </div>

        <div className="team-member nlp">
          <div className="member-icon">💬</div>
          <h3>Natural Language Processing</h3>
          <p className="member-name">Yvonne</p>
          <ul className="contributions">
            <li>Transaction Context Analysis</li>
            <li>Behavioral Pattern Recognition</li>
            <li>Anomaly Description Generation</li>
            <li>Alert Message Composition</li>
            <li>User Intent Understanding</li>
            <li>Text-based Risk Scoring</li>
          </ul>
        </div>
      </div>

      {/* System Architecture */}
      <SystemArchitecture />

      {/* Technology Stack */}
      <TechStack />
    </div>
  );
};

const SystemArchitecture: React.FC = () => {
  return (
    <div className="architecture-section">
      <h3>🏗️ System Architecture & Data Flow</h3>
      
      <div className="architecture-flow">
        {/* Stage 1: Edge Computing */}
        <div className="architecture-stage edge">
          <div className="stage-header">
            <h4>Stage 1: Data Collection</h4>
            <p className="member-tag">Josphat's Work</p>
          </div>
          <div className="stage-content">
            <p>🌍 Mobile Network</p>
            <p>↓</p>
            <p>📡 IoT Sensors</p>
            <p>↓</p>
            <p>📊 Signal Processing</p>
            <div className="data-points">
              <span className="data-item">IMSI Status</span>
              <span className="data-item">Device Risk</span>
              <span className="data-item">Hardware ID</span>
              <span className="data-item">Location Data</span>
              <span className="data-item">Timestamp</span>
            </div>
          </div>
        </div>

        {/* Arrow */}
        <div className="architecture-arrow">→</div>

        {/* Stage 2: Cryptography */}
        <div className="architecture-stage crypto">
          <div className="stage-header">
            <h4>Stage 2: Data Protection</h4>
            <p className="member-tag">Sharon's Work</p>
          </div>
          <div className="stage-content">
            <p>🔑 Key Generation</p>
            <p>↓</p>
            <p>🔐 AES-256 Encryption</p>
            <p>↓</p>
            <p>✅ HMAC Verification</p>
            <div className="data-points">
              <span className="data-item">Encrypted Payload</span>
              <span className="data-item">Masked ID</span>
              <span className="data-item">Hash Signature</span>
              <span className="data-item">Integrity Check</span>
            </div>
          </div>
        </div>

        {/* Arrow */}
        <div className="architecture-arrow">→</div>

        {/* Stage 3: ML & NLP */}
        <div className="architecture-stage ml">
          <div className="stage-header">
            <h4>Stage 3: Analysis & Prediction</h4>
            <p className="member-tag">Bramwel & Yvonne</p>
          </div>
          <div className="stage-content">
            <p>🤖 ML Model</p>
            <p>↓</p>
            <p>💬 NLP Analysis</p>
            <p>↓</p>
            <p>🎯 Risk Scoring</p>
            <div className="data-points">
              <span className="data-item">Fraud Probability</span>
              <span className="data-item">Risk Level</span>
              <span className="data-item">Explanation Text</span>
              <span className="data-item">Action Required</span>
            </div>
          </div>
        </div>

        {/* Arrow */}
        <div className="architecture-arrow">→</div>

        {/* Stage 4: Output */}
        <div className="architecture-stage output">
          <div className="stage-header">
            <h4>Stage 4: Action & Alert</h4>
            <p className="member-tag">All Teams</p>
          </div>
          <div className="stage-content">
            <p>✅ PASS / 🚫 BLOCK</p>
            <p>↓</p>
            <p>🔔 Alert System</p>
            <p>↓</p>
            <p>📊 Dashboard Update</p>
            <div className="data-points">
              <span className="data-item">Decision</span>
              <span className="data-item">Notification</span>
              <span className="data-item">Audit Log</span>
            </div>
          </div>
        </div>
      </div>

      {/* Interactions */}
      <div className="interactions-grid">
        <div className="interaction-card">
          <h4>🔄 Josphat ↔ Sharon</h4>
          <p>Raw sensor data flows from edge computing to cryptography layer for immediate encryption and protection before transmission.</p>
        </div>

        <div className="interaction-card">
          <h4>🔄 Sharon ↔ Bramwel</h4>
          <p>Encrypted, anonymized data is securely decrypted in the MLOps pipeline. Cryptographic hashes verify data integrity before model inference.</p>
        </div>

        <div className="interaction-card">
          <h4>🔄 Bramwel ↔ Yvonne</h4>
          <p>ML model outputs (fraud probability, feature importance) are fed to NLP system to generate human-readable explanations and risk narratives.</p>
        </div>

        <div className="interaction-card">
          <h4>🔄 Yvonne ↔ Sharon</h4>
          <p>NLP-generated alerts and explanations are encrypted before being sent to users, ensuring sensitive fraud analysis remains private.</p>
        </div>

        <div className="interaction-card">
          <h4>🔄 All ↔ All</h4>
          <p>Each layer validates the previous layer's output. Edge sensors validate IMSI, crypto ensures integrity, ML verifies encrypted data, NLP ensures clarity.</p>
        </div>

        <div className="interaction-card">
          <h4>🔄 Real-time Feedback Loop</h4>
          <p>System decisions are logged, encrypted, and fed back to ML models for continuous improvement and adaptation to new fraud patterns.</p>
        </div>
      </div>
    </div>
  );
};

const TechStack: React.FC = () => {
  return (
    <div className="tech-stack">
      <h3>🛠️ Integrated Technology Stack</h3>
      
      <div className="tech-layers">
        <div className="tech-layer edge-tech">
          <h4>📡 Edge Layer (Josphat)</h4>
          <div className="tech-badges">
            <span className="badge">IoT Sensors</span>
            <span className="badge">Signal Processing</span>
            <span className="badge">IMSI Detection</span>
            <span className="badge">Real-time Acquisition</span>
          </div>
        </div>

        <div className="tech-layer crypto-tech">
          <h4>🔐 Security Layer (Sharon)</h4>
          <div className="tech-badges">
            <span className="badge crypto">AES-256-GCM</span>
            <span className="badge crypto">HMAC-SHA256</span>
            <span className="badge crypto">PBKDF2</span>
            <span className="badge crypto">Hardware Security</span>
          </div>
        </div>

        <div className="tech-layer ml-tech">
          <h4>🤖 ML/Ops Layer (Bramwel)</h4>
          <div className="tech-badges">
            <span className="badge ml">TensorFlow</span>
            <span className="badge ml">XGBoost</span>
            <span className="badge ml">Kubernetes</span>
            <span className="badge ml">Apache Spark</span>
          </div>
        </div>

        <div className="tech-layer nlp-tech">
          <h4>💬 NLP Layer (Yvonne)</h4>
          <div className="tech-badges">
            <span className="badge nlp">Transformer Models</span>
            <span className="badge nlp">BERT</span>
            <span className="badge nlp">Text Generation</span>
            <span className="badge nlp">Sentiment Analysis</span>
          </div>
        </div>

        <div className="tech-layer platform-tech">
          <h4>🌐 Platform Layer</h4>
          <div className="tech-badges">
            <span className="badge platform">FastAPI</span>
            <span className="badge platform">React</span>
            <span className="badge platform">PostgreSQL</span>
            <span className="badge platform">Redis</span>
            <span className="badge platform">Docker</span>
          </div>
        </div>
      </div>
    </div>
  );
};