import { useState, useEffect } from 'react';
import { getTransactions } from '../utils/api';
import { formatCurrencyFull } from '../utils/formatters';

export default function ExceptionReport() {
  const [exceptions, setExceptions] = useState([]);

  useEffect(() => {
    getTransactions({ recovery_status: 'exception' })
      .then(res => setExceptions(res.data))
      .catch(() => {});
  }, []);

  if (exceptions.length === 0) return null;

  return (
    <div className="card">
      <div className="card-title">❌ Exception Report ({exceptions.length})</div>
      <div style={{ maxHeight: 300, overflowY: 'auto' }}>
        {exceptions.slice(0, 20).map(e => (
          <div key={e.id} style={{
            background: 'var(--bg-secondary)', borderRadius: 8, padding: 12, marginBottom: 8,
            borderLeft: '3px solid var(--red)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontSize: 12, fontWeight: 600 }}>{e.id}</span>
              <span style={{ fontSize: 12, color: 'var(--red)', fontWeight: 600 }}>{formatCurrencyFull(e.amount)}</span>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {e.customers?.name || 'Unknown'} | {e.failure_reason || 'N/A'} | {e.bank || 'N/A'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
