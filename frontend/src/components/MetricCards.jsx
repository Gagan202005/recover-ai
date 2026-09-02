import { formatCurrencyFull, formatCurrency } from '../utils/formatters';
import { FiTrendingUp, FiAlertTriangle, FiCheckCircle, FiActivity, FiShield } from 'react-icons/fi';

export default function MetricCards({ metrics }) {
  if (!metrics) {
    return (
      <div className="simple-metrics-grid">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="simple-metric-card loading">
            <div className="loading-spinner"></div>
          </div>
        ))}
      </div>
    );
  }

  const recoveryRate = metrics.recovery_rate || 0;
  const recoveredAmount = metrics.recovered?.amount || 0;
  const recoveredCount = metrics.recovered?.count || 0;
  const atRiskAmount = metrics.at_risk?.amount || 0;
  const atRiskCount = metrics.at_risk?.count || 0;
  const processingAmount = metrics.processing?.amount || 0;
  const processingCount = metrics.processing?.count || 0;
  const exceptionsAmount = metrics.exceptions?.amount || 0;
  const exceptionsCount = metrics.exceptions?.count || 0;

  return (
    <div className="simple-metrics-grid">
      {/* 1. RECOVERED CAPITAL */}
      <div className="simple-metric-card recovered-border">
        <div className="simple-metric-top">
          <span className="simple-metric-label">💰 Net Recovered</span>
          <span className="simple-metric-pill green-pill">
            <FiCheckCircle size={10} /> {recoveryRate}% Yield
          </span>
        </div>
        <div className="simple-metric-value text-green">{formatCurrencyFull(recoveredAmount)}</div>
        <div className="simple-metric-sub">
          <strong>{recoveredCount}</strong> orders recovered autonomously
        </div>
      </div>

      {/* 2. AT-RISK EXPOSURE */}
      <div className="simple-metric-card at-risk-border">
        <div className="simple-metric-top">
          <span className="simple-metric-label">💀 Revenue At Risk</span>
          <span className="simple-metric-pill red-pill">
            <FiAlertTriangle size={10} /> Total Failed
          </span>
        </div>
        <div className="simple-metric-value text-red">{formatCurrencyFull(atRiskAmount)}</div>
        <div className="simple-metric-sub">
          <strong>{atRiskCount}</strong> failed checkout transactions
        </div>
      </div>

      {/* 3. IN-PIPELINE NEGOTIATION */}
      <div className="simple-metric-card processing-border">
        <div className="simple-metric-top">
          <span className="simple-metric-label">🔄 In Swarm Pipeline</span>
          <span className="simple-metric-pill yellow-pill">
            <FiActivity size={10} /> Active
          </span>
        </div>
        <div className="simple-metric-value text-yellow">{formatCurrencyFull(processingAmount)}</div>
        <div className="simple-metric-sub">
          <strong>{processingCount}</strong> in WhatsApp / SMS recovery
        </div>
      </div>

      {/* 4. COMPLIANCE BLOCKS */}
      <div className="simple-metric-card exceptions-border">
        <div className="simple-metric-top">
          <span className="simple-metric-label">🛡️ Guardrail Protected</span>
          <span className="simple-metric-pill purple-pill">
            <FiShield size={10} /> Compliance
          </span>
        </div>
        <div className="simple-metric-value text-purple">{formatCurrencyFull(exceptionsAmount)}</div>
        <div className="simple-metric-sub">
          <strong>{exceptionsCount}</strong> opted-out / dispute blocked
        </div>
      </div>
    </div>
  );
}
