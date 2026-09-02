import { useState, useEffect } from 'react';
import { getLanguageStats } from '../utils/api';

const LANG_LABELS = { english: '🇬🇧 English', hinglish: '🇮🇳 Hinglish', hindi: '🇮🇳 Hindi' };
const LANG_COLORS = { english: 'var(--blue)', hinglish: 'var(--accent)', hindi: 'var(--green)' };

export default function LanguageStats() {
  const [stats, setStats] = useState({});

  useEffect(() => {
    getLanguageStats().then(res => setStats(res.data)).catch(() => {});
  }, []);

  const entries = Object.entries(stats);
  if (entries.length === 0) return null;

  const totalMsgs = entries.reduce((sum, [, v]) => sum + v.total, 0);

  return (
    <div className="card">
      <div className="card-title">🌐 Multi-Language Performance</div>
      {entries.map(([lang, data]) => {
        const pct = totalMsgs > 0 ? Math.round((data.total / totalMsgs) * 100) : 0;
        return (
          <div key={lang} style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
              <span>{LANG_LABELS[lang] || lang}</span>
              <span style={{ color: 'var(--text-muted)', fontFamily: "'JetBrains Mono', monospace" }}>
                {data.total} msgs ({pct}%)
              </span>
            </div>
            <div style={{ background: 'var(--bg-secondary)', borderRadius: 6, overflow: 'hidden', height: 6 }}>
              <div style={{ width: `${pct}%`, height: '100%', background: LANG_COLORS[lang] || 'var(--accent)', transition: 'width 1s ease' }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
