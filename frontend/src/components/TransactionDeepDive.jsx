import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getTransaction, getAuditTrail, getDebates } from '../utils/api';
import { agentIcons, agentColors, formatCurrencyFull, formatTime, statusColors } from '../utils/formatters';
import AgentDebateView from './AgentDebateView';

export default function TransactionDeepDive() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [txn, setTxn] = useState(null);
  const [trail, setTrail] = useState([]);
  const [debates, setDebates] = useState([]);

  useEffect(() => {
    Promise.all([getTransaction(id), getAuditTrail(id), getDebates(id)])
      .then(([t, a, d]) => { setTxn(t.data); setTrail(a.data); setDebates(d.data); })
      .catch(console.error);
  }, [id]);

  if (!txn) return <div className="deep-dive"><div className="loading-spinner"></div></div>;

  return (
    <div className="deep-dive">
      <div className="deep-dive-header">
        <button className="back-btn" onClick={() => navigate('/')}>← Back to War Room</button>
        <span style={{ color: statusColors[txn.recovery_status], fontWeight: 700, fontSize: 14, textTransform: 'uppercase' }}>
          {txn.recovery_status}
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
        <div className="card">
          <div className="card-title">Transaction Info</div>
          <p><strong>ID:</strong> {txn.id}</p>
          <p><strong>Amount:</strong> {formatCurrencyFull(txn.amount)}</p>
          <p><strong>Product:</strong> {txn.product_name}</p>
          <p><strong>Failure:</strong> {txn.failure_reason}</p>
          <p><strong>Error Code:</strong> {txn.error_code}</p>
          <p><strong>Bank:</strong> {txn.bank}</p>
          <p><strong>Method:</strong> {txn.method}</p>
        </div>
        <div className="card">
          <div className="card-title">Customer</div>
          <p><strong>Name:</strong> {txn.customers?.name || 'N/A'}</p>
          <p><strong>Segment:</strong> {txn.customers?.segment || 'N/A'}</p>
          <p><strong>Language:</strong> {txn.customers?.preferred_language || 'N/A'}</p>
          <p><strong>Channel:</strong> {txn.customers?.preferred_channel || 'N/A'}</p>
          <p><strong>DND:</strong> {txn.customers?.on_dnd ? '🔴 Yes' : '🟢 No'}</p>
          <p><strong>Opted Out:</strong> {txn.customers?.opted_out ? '🔴 Yes' : '🟢 No'}</p>
        </div>
      </div>

      {debates.length > 0 && <AgentDebateView debates={debates} />}

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">📋 Agent Audit Trail ({trail.length} actions)</div>
        <div className="audit-timeline">
          {trail.map((item, i) => (
            <div key={item.id || i} className="audit-item">
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <div className="audit-agent" style={{ color: agentColors[item.agent] || 'var(--accent)' }}>
                  {agentIcons[item.agent] || '🤖'} {item.agent?.toUpperCase()}
                </div>
                <div className="audit-time">{formatTime(item.created_at)} | {item.duration_ms}ms</div>
              </div>
              <div className="audit-action">Action: {item.action}</div>
              {item.details && (
                <div className="audit-details">
                  <pre style={{ whiteSpace: 'pre-wrap', fontSize: 10 }}>{JSON.stringify(item.details, null, 2)}</pre>
                </div>
              )}
              {item.rag_citations && item.rag_citations.length > 0 && (
                <div className="audit-rag">
                  📚 RAG Citations: {item.rag_citations.map((c, j) => (
                    <div key={j} style={{ marginTop: 4 }}>
                      <strong>{c.source}</strong>: {c.content?.slice(0, 120)}... (score: {c.score})
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
