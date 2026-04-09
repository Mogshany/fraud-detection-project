import React, { useEffect, useState } from 'react';
import { EncryptionStatus } from './EncryptionStatus';
import { Credits } from './Credits';
import '../styles/dashboard.css';

interface Transaction {
  id: string;
  amount: number;
  location: string;
  timestamp: string;
  masked_id: string;
}

interface Stat {
  total_transactions: number;
  frauds_detected: number;
  fraud_rate: number;
  avg_processing_time_ms: number;
  system_uptime: number;
}

type TabType = 'overview' | 'security' | 'team' | 'transactions';

export const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [stats, setStats] = useState<Stat | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsRes = await fetch('http://localhost:8000/stats');
        const statsData = await statsRes.json();
        setStats(statsData);

        const txRes = await fetch('http://localhost:8000/transactions?limit=10');
        const txData = await txRes.json();
        setTransactions(txData);
      } catch (err) {
        setError('Failed to load dashboard data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="dashboard"><p>Loading...</p></div>;
  }

  if (error) {
    return <div className="dashboard"><p className="error">{error}</p></div>;
  }

  return (
    <div className="dashboard">
      {/* Tabs Navigation */}
      <div className="tabs-navigation">
        <button
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button
          className={`tab-button ${activeTab === 'security' ? 'active' : ''}`}
          onClick={() => setActiveTab('security')}
        >
          🔐 Security
        </button>
        <button
          className={`tab-button ${activeTab === 'transactions' ? 'active' : ''}`}
          onClick={() => setActiveTab('transactions')}
        >
          📋 Transactions
        </button>
        <button
          className={`tab-button ${activeTab === 'team' ? 'active' : ''}`}
          onClick={() => setActiveTab('team')}
        >
          👥 Team
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="tab-pane">
            <h1>📊 Fraud Detection Dashboard</h1>

            <div className="stats-grid">
              <div className="stat-card">
                <h3>Total Transactions</h3>
                <p className="stat-value">{stats?.total_transactions || 0}</p>
              </div>
              <div className="stat-card fraud">
                <h3>Frauds Detected</h3>
                <p className="stat-value">{stats?.frauds_detected || 0}</p>
              </div>
              <div className="stat-card">
                <h3>Fraud Rate</h3>
                <p className="stat-value">{((stats?.fraud_rate || 0) * 100).toFixed(2)}%</p>
              </div>
              <div className="stat-card">
                <h3>Avg Processing Time</h3>
                <p className="stat-value">{stats?.avg_processing_time_ms || 0}ms</p>
              </div>
              <div className="stat-card">
                <h3>System Uptime</h3>
                <p className="stat-value">{stats?.system_uptime || 0}%</p>
              </div>
            </div>

            <div className="quick-stats">
              <div className="quick-stat">
                <span className="label">Detection Accuracy</span>
                <span className="value">94.5%</span>
              </div>
              <div className="quick-stat">
                <span className="label">Avg Response Time</span>
                <span className="value">48ms</span>
              </div>
              <div className="quick-stat">
                <span className="label">Active Alerts</span>
                <span className="value">{stats?.frauds_detected || 0}</span>
              </div>
              <div className="quick-stat">
                <span className="label">System Status</span>
                <span className="value healthy">Healthy</span>
              </div>
            </div>
          </div>
        )}

        {/* Security Tab */}
        {activeTab === 'security' && (
          <div className="tab-pane">
            <EncryptionStatus />
          </div>
        )}

        {/* Transactions Tab */}
        {activeTab === 'transactions' && (
          <div className="tab-pane">
            <h1>📋 Recent Transactions</h1>
            <div className="transactions-section">
              <div className="transactions-table">
                <table>
                  <thead>
                    <tr>
                      <th>Transaction ID</th>
                      <th>Amount</th>
                      <th>Location</th>
                      <th>Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx) => (
                      <tr key={tx.id}>
                        <td>{tx.id}</td>
                        <td>KES {tx.amount.toLocaleString()}</td>
                        <td>{tx.location}</td>
                        <td>{new Date(tx.timestamp).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Team Tab */}
        {activeTab === 'team' && (
          <div className="tab-pane">
            <Credits />
          </div>
        )}
      </div>
    </div>
  );
};