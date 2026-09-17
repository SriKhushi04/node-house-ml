import React from 'react';

const demoTransactions = [
  {
    txId: 'TX-000184',
    type: 'Generation',
    energy: '3.57 kWh',
    counterparty: 'B01 Solar Array',
    status: 'Verified',
  },
  {
    txId: 'TX-000183',
    type: 'P2P Transfer',
    energy: '1.20 kWh',
    counterparty: 'Building 03',
    status: 'Verified',
  },
  {
    txId: 'TX-000182',
    type: 'Generation',
    energy: '2.91 kWh',
    counterparty: 'B01 Solar Array',
    status: 'Verified',
  },
  {
    txId: 'TX-000181',
    type: 'P2P Transfer',
    energy: '0.80 kWh',
    counterparty: 'Central Battery',
    status: 'Verified',
  },
];

export default function LedgerTable({ transactions = demoTransactions }) {
  return (
    <div className="table-container">
      <table className="ledger-table">
        <thead>
          <tr>
            <th>Transaction</th>
            <th>Type</th>
            <th>Energy</th>
            <th>Counterparty</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((tx) => (
            <tr key={tx.txId}>
              <td className="tx-id">{tx.txId}</td>
              <td>
                <span
                  className={`tx-type ${
                    tx.type === 'Generation' ? 'type-generation' : 'type-p2p'
                  }`}
                >
                  {tx.type}
                </span>
              </td>
              <td>{tx.energy}</td>
              <td>{tx.counterparty}</td>
              <td>
                <span className="status-badge-verified">✓ {tx.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

