import { useNavigate } from 'react-router-dom';

export default function CoverPage() {
  const navigate = useNavigate();

  return (
    <div className="recover-cover-container">
      {/* ── Background Cyber-Mesh & Dynamic Lighting ── */}
      <div className="mesh-grid-overlay" />
      <div className="ambient-spotlight spot-blue" />
      <div className="ambient-spotlight spot-purple" />

      <div className="recover-content-card">
        {/* ── Top Buildathon Brand Tag ── */}
        <div className="brand-badge-wrapper">
          <div className="buildathon-brand-pill">
            <span className="pulse-indicator">
              <span className="pulse-dot" />
              <span className="pulse-ring" />
            </span>
            <span className="brand-text">RAZORPAY BUILDATHON 2026</span>
            <span className="badge-separator">/</span>
            <span className="track-text">TRACK 03: AI REVENUE RECOVERY</span>
          </div>
        </div>

        {/* ── Hero Title ── */}
        <h1 className="recover-hero-title">
          Recover <span className="neon-gradient-text">Lost Revenue.</span>
        </h1>

        {/* ── Official Track Slogan ── */}
        <div className="slogan-quote-wrap">
          <span className="quote-mark">“</span>
          <p className="recover-slogan">Find revenue that’s slipping away and win it back</p>
          <span className="quote-mark">”</span>
        </div>

        <p className="recover-hero-desc">
          An autonomous 6-agent LangGraph swarm that intercepts payment failures in real-time, diagnoses root causes with Pinecone RAG, debates compliance guardrails, and negotiates recovery over two-way WhatsApp.
        </p>

        {/* ── Unique 3-Stage Autonomous Recovery Pipeline ── */}
        <div className="recovery-stages-grid">
          {/* Stage 1: Detect */}
          <div className="stage-card stage-detect">
            <div className="stage-number">01</div>
            <div className="stage-header">
              <span className="stage-icon">⚡</span>
              <span className="stage-tag">REAL-TIME TRIAGE</span>
            </div>
            <h3 className="stage-title">Sentinel & Diagnostics</h3>
            <p className="stage-desc">
              Scores urgency formulas, queries 4-KB Pinecone error codes, and detects bank outage spikes across rolling 30-min windows.
            </p>
            <div className="stage-footer">
              <span className="stage-agent-pill">🔍 Sentinel</span>
              <span className="stage-agent-pill">🧠 Diagnostician</span>
            </div>
          </div>

          {/* Stage 2: Strategy & Guardrails */}
          <div className="stage-card stage-strategy">
            <div className="stage-number">02</div>
            <div className="stage-header">
              <span className="stage-icon">⚖️</span>
              <span className="stage-tag">LEGAL GUARDRAILS</span>
            </div>
            <h3 className="stage-title">Strategist & Compliance</h3>
            <p className="stage-desc">
              Thompson Sampling A/B testing + 8 regulatory checks (TRAI DND, 9AM-9PM, 3 retries) with Gemini legal debates.
            </p>
            <div className="stage-footer">
              <span className="stage-agent-pill">🎯 Strategist</span>
              <span className="stage-agent-pill">🛡️ Compliance</span>
            </div>
          </div>

          {/* Stage 3: Execution & Learning */}
          <div className="stage-card stage-execute">
            <div className="stage-number">03</div>
            <div className="stage-header">
              <span className="stage-icon">💬</span>
              <span className="stage-tag">TWO-WAY ACTION</span>
            </div>
            <h3 className="stage-title">Executor & Self-Learning</h3>
            <p className="stage-desc">
              Dispatches WhatsApp conversational recovery, auto-schedules promise-to-pay reminders, and updates Pinecone playbooks.
            </p>
            <div className="stage-footer">
              <span className="stage-agent-pill">⚡ Executor</span>
              <span className="stage-agent-pill">📊 Analyst</span>
            </div>
          </div>
        </div>

        {/* ── Main High-Impact CTA Button ── */}
        <div className="cta-wrapper">
          <button className="launch-swarm-btn" onClick={() => navigate('/war-room')}>
            <span className="btn-icon">⚡</span>
            <span>Enter RecoverAI War Room</span>
            <span className="btn-arrow">→</span>
          </button>
        </div>

        {/* ── Subtle Elegant Footer Attribution ── */}
        <div className="cover-footer-credit">
          <span>Built with ❤️ by <strong className="credit-author">Gagan Singhal</strong></span>
          <span className="credit-dot">•</span>
          <span>Razorpay Buildathon 2026</span>
        </div>
      </div>
    </div>
  );
}
