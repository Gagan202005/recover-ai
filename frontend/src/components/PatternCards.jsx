import { Link } from 'react-router-dom';
import { FiAlertTriangle, FiActivity, FiArrowRight, FiZap } from 'react-icons/fi';

export default function PatternCards({ patterns }) {
  if (!patterns || patterns.length === 0) {
    return (
      <div className="card">
        <div className="card-title">🔍 Failure Patterns</div>
        <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '24px 0' }}>
          No anomaly patterns detected yet.
        </div>
      </div>
    );
  }

  const severityBadgeClass = {
    high: 'badge-high',
    medium: 'badge-medium',
    low: 'badge-low',
  };

  const typeIcon = {
    bank_outage: '🏦',
    failure_cluster: '⚡',
    method_issue: '💳',
    high_value_risk: '💰',
    low_recovery: '📉',
  };

  return (
    <div className="card pattern-preview-card">
      <div className="card-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 16 }}>🔍</span>
          <span style={{ fontWeight: 800 }}>Autonomous Failure Radar</span>
          <span className="live-count-pill">{patterns.length} Active</span>
        </div>
        <Link 
          to="/patterns" 
          className="preview-deep-link"
          style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: 'var(--accent)', textDecoration: 'none', fontWeight: 700 }}
        >
          <span>Full Analytics</span>
          <FiArrowRight />
        </Link>
      </div>

      <div className="patterns-preview-list">
        {patterns.slice(0, 5).map((p, i) => {
          const isHigh = p.severity === 'high';
          const icon = typeIcon[p.type] || '⚠️';

          return (
            <div key={i} className={`pattern-preview-item ${isHigh ? 'item-high-severity' : ''}`}>
              <div className="preview-item-top">
                <span className="preview-item-icon">{icon}</span>
                <div className="preview-item-desc">{p.description}</div>
              </div>

              <div className="preview-item-bottom">
                <span className={`mini-severity-chip ${severityBadgeClass[p.severity] || 'badge-low'}`}>
                  {p.severity?.toUpperCase()}
                </span>
                <span className="mini-type-tag">
                  {p.type?.replace(/_/g, ' ')}
                </span>
                {p.recovery_rate !== undefined && (
                  <span className="mini-rate-tag">
                    {p.recovery_rate}% recovery
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <Link 
        to="/patterns" 
        className="open-radar-btn"
      >
        <FiZap style={{ marginRight: 6 }} />
        <span>Open Multi-Dimensional Root Cause Radar →</span>
      </Link>
    </div>
  );
}
