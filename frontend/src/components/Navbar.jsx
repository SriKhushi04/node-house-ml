import React from 'react';

export default function Navbar({ activeTab, setActiveTab }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <div className="brand-icon"></div>
        <span className="brand-title">GridShare</span>
        <span className="brand-sub">NODE</span>
      </div>

      <div className="nav-links">
        <button
          className={`nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
        <button
          className={`nav-btn ${activeTab === 'ledger' ? 'active' : ''}`}
          onClick={() => setActiveTab('ledger')}
        >
          Energy Ledger
        </button>
      </div>

      <div className="navbar-actions">
        <div className="node-status">
          <span className="status-dot"></span>
          <span>B01 Online</span>
        </div>
        <button className="connect-wallet-btn">
          Connect Wallet
        </button>
      </div>
    </nav>
  );
}
