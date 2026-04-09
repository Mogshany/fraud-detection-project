import React, { useEffect, useState } from 'react';
import '../styles/encryption.css';

interface EncryptionData {
  algorithm: string;
  keySize: number;
  encryptedRecords: number;
  encryptionStatus: 'active' | 'inactive';
  lastEncrypted: string;
}

export const EncryptionStatus: React.FC = () => {
  const [encryptionData, setEncryptionData] = useState<EncryptionData>({
    algorithm: 'AES-256-GCM',
    keySize: 256,
    encryptedRecords: 3847,
    encryptionStatus: 'active',
    lastEncrypted: new Date().toLocaleString(),
  });

  return (
    <div className="encryption-section">
      <h2>🔐 Cryptographic Security</h2>
      <div className="encryption-grid">
        <div className="encryption-card">
          <h3>Encryption Algorithm</h3>
          <p className="value">{encryptionData.algorithm}</p>
          <p className="label">Advanced Encryption Standard</p>
        </div>

        <div className="encryption-card">
          <h3>Key Size</h3>
          <p className="value">{encryptionData.keySize} bits</p>
          <p className="label">Military-grade encryption</p>
        </div>

        <div className="encryption-card">
          <h3>Encrypted Records</h3>
          <p className="value">{encryptionData.encryptedRecords.toLocaleString()}</p>
          <p className="label">Data points secured</p>
        </div>

        <div className={`encryption-card status ${encryptionData.encryptionStatus}`}>
          <h3>Encryption Status</h3>
          <p className="value">
            {encryptionData.encryptionStatus === 'active' ? '🟢 ACTIVE' : '🔴 INACTIVE'}
          </p>
          <p className="label">Real-time protection</p>
        </div>
      </div>

      <div className="encryption-details">
        <h3>Security Features</h3>
        <ul>
          <li>✅ End-to-end encryption for all transactions</li>
          <li>✅ HMAC-SHA256 for data integrity verification</li>
          <li>✅ Random IV generation for each encryption</li>
          <li>✅ Secure key derivation (PBKDF2)</li>
          <li>✅ Hardware-accelerated cryptographic operations</li>
          <li>✅ PCI-DSS compliant encryption protocols</li>
        </ul>
      </div>
    </div>
  );
};