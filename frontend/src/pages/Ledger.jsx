import React from 'react';
import LedgerTable from '../components/LedgerTable';

export default function Ledger() {
  return (
    <div className="ledger-page">
      <div className="hero-section" style={{ marginBottom: '2rem' }}>
        <div className="hero-content">
          <div className="eyebrow">
            <span className="eyebrow-dot">•</span> PEER-TO-PEER NETWORK
          </div>
          <h1 className="hero-title">
            Energy <span className="accent">Ledger.</span>
          </h1>
          <p className="hero-description">
            Transparent record of energy generation and peer-to-peer transfers originating from this node.
          </p>
        </div>
      </div>

      <div className="ledger-wallet-card">
        <div>
          <div className="identity-label">NODE WALLET</div>
          <div className="identity-value" style={{ fontSize: '1.1rem', marginTop: '0.2rem' }}>
            Not Connected
          </div>
        </div>
        <button className="btn-metamask" onClick={() => {}}>
          Connect MetaMask
        </button>
      </div>

      <div className="status-strip">
        <div className="strip-item">
          <span className="strip-label">TOTAL RECORDED</span>
          <span className="strip-value prominent">8.48 kWh</span>
        </div>
        <div className="strip-divider" />
        <div className="strip-item">
          <span className="strip-label">TRANSACTIONS</span>
          <span className="strip-value">4 Records</span>
        </div>
        <div className="strip-divider" />
        <div className="strip-item">
          <span className="strip-label">NODE</span>
          <span className="strip-value">B01</span>
        </div>
        <div className="strip-divider" />
        <div className="strip-item">
          <span className="strip-label">NETWORK</span>
          <span className="strip-value">Demonstration</span>
        </div>
      </div>

      <div className="table-panel">
        <div style={{ marginBottom: '1rem' }}>
          <span className="panel-eyebrow">RECORDED ACTIVITY</span>
        </div>
        <LedgerTable />
      </div>

      <div className="independence-strip">
        <span className="notice-check">❖</span>
        <div>
          <div className="notice-title">Blockchain-ready ledger</div>
          <div className="notice-text">
            Current records are demonstration data. The ledger interface is structured for future MetaMask wallet connection and on-chain transaction verification.
          </div>
        </div>
      </div>
    </div>
  );
}
