export default function AgentDebateView({ debates }) {
  if (!debates || debates.length === 0) return null;

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="card-title">⚔️ Agent Debates ({debates.length})</div>
      {debates.map((d, i) => (
        <div key={d.id || i} className="debate-card">
          <div className="debate-header">
            <div className="debate-vs">
              🎯 {d.proposer?.toUpperCase()} &nbsp;vs&nbsp; ⚖️ {d.reviewer?.toUpperCase()}
            </div>
          </div>
          <div className="debate-objection">
            <strong>❌ Objection:</strong> {d.objection}
          </div>
          <div className="debate-resolution">
            <strong>✅ Resolution:</strong> {JSON.stringify(d.resolution)}
          </div>
          {d.compliance_citation && (
            <div className="debate-citation">📜 {d.compliance_citation}</div>
          )}
        </div>
      ))}
    </div>
  );
}
