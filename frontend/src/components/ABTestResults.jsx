import { useState, useEffect } from 'react';
import { getABTests } from '../utils/api';

export default function ABTestResults() {
  const [tests, setTests] = useState([]);

  useEffect(() => {
    getABTests().then(res => setTests(res.data)).catch(() => {});
  }, []);

  if (tests.length === 0) return null;

  return (
    <div className="card">
      <div className="card-title">🧪 A/B Test Results</div>
      {tests.map((t, i) => {
        const rateA = t.variant_a_trials > 0 ? Math.round((t.variant_a_successes / t.variant_a_trials) * 100) : 0;
        const rateB = t.variant_b_trials > 0 ? Math.round((t.variant_b_successes / t.variant_b_trials) * 100) : 0;
        const totalTrials = t.variant_a_trials + t.variant_b_trials;

        return (
          <div key={t.id || i} style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: 14, marginBottom: 10 }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>{t.experiment_name}</div>
            <div style={{ display: 'flex', gap: 12 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                  {t.variant_a?.toUpperCase()} {t.winner === t.variant_a ? '👑' : ''}
                </div>
                <div style={{ background: 'var(--bg-card)', borderRadius: 6, overflow: 'hidden', height: 8, marginBottom: 4 }}>
                  <div style={{ width: `${rateA}%`, height: '100%', background: 'var(--accent)', transition: 'width 1s ease' }} />
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{rateA}% ({t.variant_a_successes}/{t.variant_a_trials})</div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
                  {t.variant_b?.toUpperCase()} {t.winner === t.variant_b ? '👑' : ''}
                </div>
                <div style={{ background: 'var(--bg-card)', borderRadius: 6, overflow: 'hidden', height: 8, marginBottom: 4 }}>
                  <div style={{ width: `${rateB}%`, height: '100%', background: 'var(--green)', transition: 'width 1s ease' }} />
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{rateB}% ({t.variant_b_successes}/{t.variant_b_trials})</div>
              </div>
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 6 }}>
              {totalTrials} trials | {t.is_significant ? '✅ Significant' : '🔄 Collecting data...'}
            </div>
          </div>
        );
      })}
    </div>
  );
}
