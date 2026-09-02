import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { getDetailedPatterns } from '../utils/api';
import {
  FiAlertTriangle,
  FiActivity,
  FiServer,
  FiTrendingUp,
  FiTrendingDown,
  FiCreditCard,
  FiDollarSign,
  FiZap,
  FiSearch,
  FiRefreshCw,
  FiExternalLink,
  FiCheckCircle,
  FiXCircle,
  FiShield,
  FiCpu,
  FiSliders,
  FiArrowRight,
  FiLayers,
  FiInfo,
} from 'react-icons/fi';

const BANK_BRAND_THEMES = {
  HDFC: { color: '#004c8f', gradient: 'linear-gradient(135deg, rgba(0, 76, 143, 0.25), rgba(15, 23, 42, 0.6))', border: '#004c8f' },
  SBI: { color: '#280071', gradient: 'linear-gradient(135deg, rgba(40, 0, 113, 0.25), rgba(15, 23, 42, 0.6))', border: '#38bdf8' },
  ICICI: { color: '#f58220', gradient: 'linear-gradient(135deg, rgba(245, 130, 32, 0.25), rgba(15, 23, 42, 0.6))', border: '#f58220' },
  AXIS: { color: '#97144d', gradient: 'linear-gradient(135deg, rgba(151, 20, 77, 0.25), rgba(15, 23, 42, 0.6))', border: '#f43f5e' },
  KOTAK: { color: '#ed1c24', gradient: 'linear-gradient(135deg, rgba(237, 28, 36, 0.25), rgba(15, 23, 42, 0.6))', border: '#ed1c24' },
  YES: { color: '#005b9f', gradient: 'linear-gradient(135deg, rgba(0, 91, 159, 0.25), rgba(15, 23, 42, 0.6))', border: '#005b9f' },
  DEFAULT: { color: '#6366f1', gradient: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(15, 23, 42, 0.6))', border: '#6366f1' },
};

const RAIL_ICONS = {
  card: '💳',
  upi: '📱',
  netbanking: '🏦',
  mandate: '🔄',
  emi: '🛍️',
  other: '⚡',
};

export default function PatternDeepDive() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('all');
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all'); // all, outage, low_recovery, high_risk
  const [selectedInspectItem, setSelectedInspectItem] = useState(null);

  useEffect(() => {
    fetchPatterns();
  }, []);

  const fetchPatterns = async () => {
    setRefreshing(true);
    try {
      const res = await getDetailedPatterns();
      setData(res.data);
    } catch (err) {
      console.error('Failed to load detailed patterns:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const getBankTheme = (bankName) => {
    const key = Object.keys(BANK_BRAND_THEMES).find(k =>
      bankName.toUpperCase().includes(k)
    );
    return BANK_BRAND_THEMES[key] || BANK_BRAND_THEMES.DEFAULT;
  };

  // Filtered lists
  const filteredBanks = useMemo(() => {
    if (!data?.banks) return [];
    return data.banks.filter(b => {
      const matchSearch = b.bank.toLowerCase().includes(search.toLowerCase()) ||
        b.status.toLowerCase().includes(search.toLowerCase()) ||
        (b.error_codes || []).some(c => c.toLowerCase().includes(search.toLowerCase()));

      if (!matchSearch) return false;

      if (severityFilter === 'outage') return b.is_outage || b.outage_failures >= 3;
      if (severityFilter === 'low_recovery') return b.recovery_rate < 40;
      if (severityFilter === 'high_risk') return b.amount >= 20000;
      return true;
    });
  }, [data, search, severityFilter]);

  const filteredCauses = useMemo(() => {
    if (!data?.root_causes) return [];
    return data.root_causes.filter(r => {
      const matchSearch = r.title.toLowerCase().includes(search.toLowerCase()) ||
        r.reason.toLowerCase().includes(search.toLowerCase()) ||
        r.fix.toLowerCase().includes(search.toLowerCase());

      if (!matchSearch) return false;

      if (severityFilter === 'outage') return r.reason.includes('bank') || r.reason.includes('timeout') || r.reason.includes('network');
      if (severityFilter === 'low_recovery') return r.recovery_rate < 40;
      if (severityFilter === 'high_risk') return r.amount >= 30000;
      return true;
    });
  }, [data, search, severityFilter]);

  const filteredRails = useMemo(() => {
    if (!data?.payment_rails) return [];
    return data.payment_rails.filter(rail => {
      const matchSearch = rail.label.toLowerCase().includes(search.toLowerCase()) ||
        rail.method.toLowerCase().includes(search.toLowerCase());
      if (!matchSearch) return false;
      if (severityFilter === 'low_recovery') return rail.recovery_rate < 40;
      if (severityFilter === 'high_risk') return rail.amount >= 20000;
      return true;
    });
  }, [data, search, severityFilter]);

  const filteredHighValue = useMemo(() => {
    if (!data?.high_value_transactions) return [];
    return data.high_value_transactions.filter(t => {
      return (
        t.customer_name?.toLowerCase().includes(search.toLowerCase()) ||
        t.id?.toLowerCase().includes(search.toLowerCase()) ||
        t.product_name?.toLowerCase().includes(search.toLowerCase()) ||
        t.bank?.toLowerCase().includes(search.toLowerCase()) ||
        t.failure_reason?.toLowerCase().includes(search.toLowerCase())
      );
    });
  }, [data, search]);

  if (loading) {
    return (
      <div className="pattern-page-container">
        <div className="pattern-loading-hero">
          <div className="pattern-loading-icon">
            <FiCpu className="spin-slow" />
          </div>
          <h2>Correlating Multi-Dimensional Failure Telemetry...</h2>
          <p>Analyzing gateway downtime, rail friction, and customer drop-off signals in real time</p>
          <div className="loading-bar-wrapper">
            <div className="loading-bar-indeterminate"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { summary } = data;
  const totalRecoveredCount = (data.root_causes || []).reduce((acc, c) => acc + (c.recovered_count || 0), 0);
  const totalFailedCount = summary.total_failed || 1;
  const computedRecoveryRate = Math.round((totalRecoveredCount / totalFailedCount) * 100);

  return (
    <div className="pattern-page-container">
      {/* ── Page Header with Navigation & Live Refresh ── */}
      <div className="pattern-page-header">
        <div className="pattern-header-left">
          <div className="pattern-breadcrumbs">
            <Link to="/war-room" className="pattern-back-link">
              ← War Room
            </Link>
            <span className="pattern-breadcrumb-sep">/</span>
            <span className="pattern-breadcrumb-current">Failure Patterns & Root-Cause Radar</span>
          </div>
          <div className="pattern-title-row">
            <h1 className="pattern-page-title">Failure Patterns & Root-Cause Radar</h1>
            <span className="pattern-live-status-pill">
              <span className="pattern-pulse-dot"></span>
              Autonomous Multi-Agent Telemetry Active
            </span>
          </div>
          <p className="pattern-page-subtitle">
            Real-time multi-dimensional correlation distinguishing bank gateway downtime from customer balance drop-offs.
          </p>
        </div>

        <div className="pattern-header-right">
          <button
            className={`pattern-refresh-btn ${refreshing ? 'spinning' : ''}`}
            onClick={fetchPatterns}
            disabled={refreshing}
          >
            <FiRefreshCw className={`icon ${refreshing ? 'spin' : ''}`} />
            <span>{refreshing ? 'Updating Radar...' : 'Live Re-Cluster'}</span>
          </button>
        </div>
      </div>

      {/* ── Autonomous Directive Banner ── */}
      <div className={`pattern-directive-banner ${summary.outage_banks_count > 0 ? 'warning-theme' : 'stable-theme'}`}>
        <div className="directive-badge">
          <FiZap size={13} />
          <span>AUTONOMOUS SWARM DIRECTIVE</span>
        </div>
        <div className="directive-message">
          {summary.outage_banks_count > 0 ? (
            <span>
              🚨 <strong>Bank Gateway Cluster Alert:</strong> {summary.outage_banks_count} banking gateway(s) experiencing server-side drop-offs. Sentinel Agent has placed retries in a 2-hour hold-off buffer.
            </span>
          ) : (
            <span>
              ✅ <strong>Banking Rails Healthy:</strong> Core gateway health is optimal across major nodes. Recovery focused on customer balance shortfalls via 1-Click WhatsApp links.
            </span>
          )}
        </div>
        <div className="directive-meta">
          <span className="meta-label">Diagnostics</span>
          <span className="meta-val">4 Active Knowledge Bases</span>
        </div>
      </div>

      {/* ── SECTION 1: METRICS GRID (War Room style) ── */}
      <div className="simple-metrics-grid" style={{ marginBottom: '28px' }}>
        <div className="simple-metric-card at-risk-border">
          <div className="simple-metric-top">
            <span className="simple-metric-label">Revenue At Risk</span>
            <span className="simple-metric-pill red-pill">
              <FiAlertTriangle size={10} /> {summary.total_failed} Failed
            </span>
          </div>
          <div className="simple-metric-value text-red">
            ₹{(summary.total_at_risk || 0).toLocaleString()}
          </div>
          <div className="simple-metric-sub">
            Across <strong>{data.banks?.length || 0}</strong> Bank Gateway Rails
          </div>
        </div>

        <div className="simple-metric-card processing-border">
          <div className="simple-metric-top">
            <span className="simple-metric-label">Gateway Outages</span>
            <span className={`simple-metric-pill ${summary.outage_banks_count > 0 ? 'yellow-pill' : 'green-pill'}`}>
              <FiServer size={10} /> {summary.outage_banks_count > 0 ? 'Degraded' : 'Operational'}
            </span>
          </div>
          <div className={`simple-metric-value ${summary.outage_banks_count > 0 ? 'text-yellow' : 'text-green'}`}>
            {summary.outage_banks_count} <small style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)' }}>Nodes Down</small>
          </div>
          <div className="simple-metric-sub">
            {summary.outage_banks_count > 0 ? 'Smart 2h retry buffer active' : 'All gateway nodes healthy'}
          </div>
        </div>

        <div className="simple-metric-card exceptions-border">
          <div className="simple-metric-top">
            <span className="simple-metric-label">Primary Friction</span>
            <span className="simple-metric-pill purple-pill">
              <FiActivity size={10} /> Top Cause
            </span>
          </div>
          <div className="simple-metric-value text-purple" style={{ fontSize: '16px', lineHeight: '1.3', wordBreak: 'break-word' }}>
            {summary.top_failure_cause || 'Card Validity Expired'}
          </div>
          <div className="simple-metric-sub">
            Autonomous multi-rail routing
          </div>
        </div>

        <div className="simple-metric-card recovered-border">
          <div className="simple-metric-top">
            <span className="simple-metric-label">Swarm Recovery Yield</span>
            <span className="simple-metric-pill green-pill">
              <FiTrendingUp size={10} /> {computedRecoveryRate}% Rate
            </span>
          </div>
          <div className="simple-metric-value text-green">
            {computedRecoveryRate}%
          </div>
          <div className="simple-metric-sub">
            Top vulnerable: <strong>{summary.top_vulnerable_rail?.toUpperCase() || 'CARD'}</strong>
          </div>
        </div>
      </div>

      {/* ── SECTION 2: STREAM DECK COCKPIT (War Room style) ── */}
      <div className="stream-deck-card">
        {/* SUBSECTIONS TAB BAR HEADER */}
        <div className="stream-deck-tabs-header">
          <div className="stream-deck-tabs-top-row">
            <div className="stream-deck-tabs">
              <button
                className={`stream-tab-btn ${activeTab === 'all' ? 'active' : ''}`}
                onClick={() => setActiveTab('all')}
              >
                <FiLayers size={13} />
                <span>All Dimensions</span>
                <span className="stream-tab-badge">
                  {(data.banks?.length || 0) + (data.root_causes?.length || 0) + (data.payment_rails?.length || 0)}
                </span>
              </button>

              <button
                className={`stream-tab-btn ${activeTab === 'banks' ? 'active' : ''}`}
                onClick={() => setActiveTab('banks')}
              >
                <FiServer size={13} />
                <span>Bank Nodes</span>
                <span className={`stream-tab-badge ${filteredBanks.length < (data.banks?.length || 0) ? 'filtered' : ''}`}>
                  {filteredBanks.length}
                </span>
              </button>

              <button
                className={`stream-tab-btn ${activeTab === 'causes' ? 'active' : ''}`}
                onClick={() => setActiveTab('causes')}
              >
                <FiZap size={13} />
                <span>Root Causes</span>
                <span className={`stream-tab-badge ${filteredCauses.length < (data.root_causes?.length || 0) ? 'filtered' : ''}`}>
                  {filteredCauses.length}
                </span>
              </button>

              <button
                className={`stream-tab-btn ${activeTab === 'rails' ? 'active' : ''}`}
                onClick={() => setActiveTab('rails')}
              >
                <FiCreditCard size={13} />
                <span>Payment Rails</span>
                <span className={`stream-tab-badge ${filteredRails.length < (data.payment_rails?.length || 0) ? 'filtered' : ''}`}>
                  {filteredRails.length}
                </span>
              </button>

              <button
                className={`stream-tab-btn ${activeTab === 'high_value' ? 'active' : ''}`}
                onClick={() => setActiveTab('high_value')}
              >
                <FiDollarSign size={13} />
                <span>High-Value Orders</span>
                <span className={`stream-tab-badge high-val ${filteredHighValue.length < (data.high_value_transactions?.length || 0) ? 'filtered' : ''}`}>
                  {filteredHighValue.length}
                </span>
              </button>
            </div>

            {/* Context status & reset button */}
            <div className="deck-status-actions">
              {(search || severityFilter !== 'all') ? (
                <button
                  className="deck-reset-btn"
                  onClick={() => { setSearch(''); setSeverityFilter('all'); }}
                  title="Reset search and filters"
                >
                  <span>✕ Reset Filters</span>
                </button>
              ) : (
                <div className="deck-live-summary">
                  <span className="summary-dot"></span>
                  <span>
                    {activeTab === 'all' && `Displaying All Telemetry Vectors`}
                    {activeTab === 'banks' && `${filteredBanks.length} Bank Nodes Monitored`}
                    {activeTab === 'causes' && `${filteredCauses.length} Root Cause Clusters`}
                    {activeTab === 'rails' && `${filteredRails.length} Payment Rail Vectors`}
                    {activeTab === 'high_value' && `${filteredHighValue.length} High-Exposure Orders`}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Sub-bar: Search & Filter Chips */}
          <div className="stream-deck-filter-bar">
            <div className="deck-search-wrap">
              <FiSearch className="search-lead-icon" />
              <input
                type="text"
                placeholder="Filter by bank name, error code (GATEWAY_TIMEOUT...), rail, or reason..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="deck-search-field"
              />
              {search && (
                <button className="deck-search-clear" onClick={() => setSearch('')} title="Clear search">
                  ✕
                </button>
              )}
            </div>

            <div className="deck-chips-group">
              <span className="chips-label">FILTER BY:</span>

              <button
                className={`deck-filter-chip chip-all ${severityFilter === 'all' ? 'active' : ''}`}
                onClick={() => setSeverityFilter('all')}
              >
                <span>All Status</span>
              </button>

              <button
                className={`deck-filter-chip chip-outage ${severityFilter === 'outage' ? 'active' : ''}`}
                onClick={() => setSeverityFilter(severityFilter === 'outage' ? 'all' : 'outage')}
              >
                <span className="chip-dot red"></span>
                <span>Bank Outages</span>
              </button>

              <button
                className={`deck-filter-chip chip-low-yield ${severityFilter === 'low_recovery' ? 'active' : ''}`}
                onClick={() => setSeverityFilter(severityFilter === 'low_recovery' ? 'all' : 'low_recovery')}
              >
                <span className="chip-dot amber"></span>
                <span>Low Yield (&lt;40%)</span>
              </button>

              <button
                className={`deck-filter-chip chip-high-risk ${severityFilter === 'high_risk' ? 'active' : ''}`}
                onClick={() => setSeverityFilter(severityFilter === 'high_risk' ? 'all' : 'high_risk')}
              >
                <span className="chip-dot purple"></span>
                <span>High Exposure (≥₹20k)</span>
              </button>
            </div>
          </div>
        </div>

        <div className="stream-deck-content">

          {/* ═══════════════════════════════════════════════════════════
          SECTION 1: BANK TELEMETRY & GATEWAY NODES
      ════════════════════════════════════════════════════════════ */}
          {(activeTab === 'all' || activeTab === 'banks') && (
            <div className="pattern-radar-section">
              <div className="radar-section-header">
                <div className="header-badge-group">
                  <span className="radar-icon-wrap">
                    <FiServer />
                  </span>
                  <div>
                    <h2 className="radar-section-title">Banking Infrastructure & Telemetry Nodes</h2>
                    <p className="radar-section-desc">
                      Autonomous health grading distinguishing core bank downtime from customer-side balance or authorization issues.
                    </p>
                  </div>
                </div>
                <div className="header-meta-pill">
                  <span>Cluster Dimension:</span>
                  <code>metadata.bank</code>
                </div>
              </div>

              {filteredBanks.length === 0 ? (
                <div className="radar-empty-state">
                  <FiInfo className="empty-icon" />
                  <span>No bank nodes matched your search or severity filter.</span>
                </div>
              ) : (
                <div className="bank-nodes-grid">
                  {filteredBanks.map((b) => {
                    const theme = getBankTheme(b.bank);
                    const isOutage = b.is_outage || b.status.includes('OUTAGE');
                    const isDegraded = b.status.includes('INSTABILITY') || b.status.includes('WARNING');
                    const outagePercent = b.count > 0 ? Math.round((b.outage_failures / b.count) * 100) : 0;
                    const customerPercent = 100 - outagePercent;

                    return (
                      <div
                        key={b.bank}
                        className={`bank-node-card ${isOutage ? 'node-outage' : isDegraded ? 'node-warning' : 'node-healthy'}`}
                        style={{ '--node-accent': theme.border }}
                      >


                        <div className="node-card-header">
                          <div className="node-brand-wrap">
                            <div
                              className="bank-logo-shield"
                              style={{ borderColor: theme.border, background: theme.gradient }}
                            >
                              <span className="bank-initials">{b.bank.substring(0, 4).toUpperCase()}</span>
                            </div>
                            <div className="node-name-block">
                              <div className="node-bank-name">{b.bank} Bank</div>
                              <div className="node-rail-tag">
                                <span>Rail:</span> <strong>{b.top_method?.toUpperCase()}</strong>
                              </div>
                            </div>
                          </div>

                          {/* Status Ping Badge */}
                          <div className={`node-status-beacon ${isOutage ? 'beacon-red' : isDegraded ? 'beacon-yellow' : 'beacon-green'}`}>
                            <span className="beacon-ping"></span>
                            <span className="beacon-label">{b.status}</span>
                          </div>
                        </div>

                        {/* Telemetry Visual Gauge: Gateway vs Customer */}
                        <div className="node-telemetry-gauge">
                          <div className="gauge-labels">
                            <span className="gauge-lbl red">
                              Gateway Drops: <strong>{b.outage_failures}</strong> ({outagePercent}%)
                            </span>
                            <span className="gauge-lbl cyan">
                              Customer Auth: <strong>{b.customer_failures}</strong> ({customerPercent}%)
                            </span>
                          </div>
                          <div className="gauge-split-bar">
                            <div
                              className="gauge-segment red"
                              style={{ width: `${outagePercent}%` }}
                              title={`Gateway Server Drops: ${b.outage_failures}`}
                            ></div>
                            <div
                              className="gauge-segment cyan"
                              style={{ width: `${customerPercent}%` }}
                              title={`Customer Balance/Auth: ${b.customer_failures}`}
                            ></div>
                          </div>
                        </div>

                        {/* Micro Stats Grid */}
                        <div className="node-metrics-cluster">
                          <div className="node-stat-box">
                            <span className="stat-caption">Total Volume</span>
                            <span className="stat-figure">{b.count} <small>txns</small></span>
                          </div>
                          <div className="node-stat-box">
                            <span className="stat-caption">Rupees At Risk</span>
                            <span className="stat-figure highlight-val">₹{b.amount?.toLocaleString()}</span>
                          </div>
                          <div className="node-stat-box">
                            <span className="stat-caption">Swarm Recovered</span>
                            <span
                              className="stat-figure"
                              style={{ color: b.recovery_rate >= 40 ? 'var(--green)' : 'var(--accent)' }}
                            >
                              {b.recovery_rate}% <small>({b.recovered_count || 0})</small>
                            </span>
                          </div>
                        </div>

                        {/* Error Code Badges */}
                        {b.error_codes && b.error_codes.length > 0 && (
                          <div className="node-codes-ribbon">
                            <span className="codes-caption">Detected Errors:</span>
                            <div className="codes-chips-wrap">
                              {b.error_codes.map((code) => (
                                <span key={code} className="node-code-chip" title={`Razorpay Error Code: ${code}`}>
                                  {code}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Autonomous Swarm Directive Copilot Box */}
                        <div className="node-directive-copilot">
                          <div className="copilot-header">
                            <FiCpu className="copilot-icon" />
                            <span>AI SWARM MITIGATION DIRECTIVE</span>
                          </div>
                          <p className="copilot-text">
                            {b.recommended_action}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ═══════════════════════════════════════════════════════════
          SECTION 2: ROOT CAUSE CLUSTERING & SWARM STRATEGY
      ════════════════════════════════════════════════════════════ */}
          {(activeTab === 'all' || activeTab === 'causes') && (
            <div className="pattern-radar-section">
              <div className="radar-section-header">
                <div className="header-badge-group">
                  <span className="radar-icon-wrap" style={{ color: 'var(--accent)' }}>
                    <FiZap />
                  </span>
                  <div>
                    <h2 className="radar-section-title">Root-Cause Clusters & Autonomous Recovery Blueprints</h2>
                    <p className="radar-section-desc">
                      Machine-classified failure categories correlated with tailored multi-channel resolution playbooks.
                    </p>
                  </div>
                </div>
                <div className="header-meta-pill">
                  <span>Cluster Dimension:</span>
                  <code>metadata.failure_reason</code>
                </div>
              </div>

              {filteredCauses.length === 0 ? (
                <div className="radar-empty-state">
                  <FiInfo className="empty-icon" />
                  <span>No root cause clusters matched your search criteria.</span>
                </div>
              ) : (
                <div className="causes-radar-grid">
                  {filteredCauses.map((cause, idx) => {
                    const isHighShare = cause.share_percent >= 25;
                    const isGoodRecovery = cause.recovery_rate >= 50;

                    return (
                      <div key={cause.reason || idx} className="cause-radar-card">
                        {/* Top Identity & Category */}
                        <div className="cause-card-head">
                          <div className="cause-icon-block">
                            <span className="cause-emoji-avatar">{cause.icon || '⚡'}</span>
                            <div>
                              <h3 className="cause-main-title">{cause.title}</h3>
                              <div className="cause-slug-code">
                                <code>{cause.reason}</code>
                              </div>
                            </div>
                          </div>

                          <div className="cause-share-pill-wrapper">
                            <span className={`cause-share-pill ${isHighShare ? 'high-volume' : ''}`}>
                              {cause.share_percent}% Total Share
                            </span>
                          </div>
                        </div>

                        {/* Share of Failures Progress Track */}
                        <div className="cause-share-track-container">
                          <div className="track-fill-glow" style={{ width: `${Math.min(100, cause.share_percent * 2.2)}%` }}></div>
                        </div>

                        {/* Financial & Yield Matrix */}
                        <div className="cause-financial-matrix">
                          <div className="fin-metric-cell">
                            <span className="fin-lbl">Occurrences</span>
                            <span className="fin-val">{cause.count}</span>
                          </div>
                          <div className="fin-metric-cell">
                            <span className="fin-lbl">At-Risk Exposure</span>
                            <span className="fin-val highlight-red">₹{cause.amount?.toLocaleString()}</span>
                          </div>
                          <div className="fin-metric-cell">
                            <span className="fin-lbl">Recovery Yield</span>
                            <span className={`fin-val ${isGoodRecovery ? 'good-recovery' : 'low-recovery'}`}>
                              {cause.recovery_rate}% <small>({cause.recovered_count || 0} saved)</small>
                            </span>
                          </div>
                        </div>

                        {/* Autonomous Swarm Blueprint Box */}
                        <div className="cause-strategy-blueprint">
                          <div className="blueprint-tag-row">
                            <div className="blueprint-tag">
                              <FiShield className="bp-icon" />
                              <span>AUTONOMOUS SWARM BLUEPRINT</span>
                            </div>
                            <span className="blueprint-channel-tag">Wabery Omnichannel</span>
                          </div>
                          <div className="blueprint-body">
                            <p className="blueprint-desc">{cause.fix}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ═══════════════════════════════════════════════════════════
          SECTION 3: PAYMENT RAILS FRICTION VECTORS
      ════════════════════════════════════════════════════════════ */}
          {(activeTab === 'all' || activeTab === 'rails') && (
            <div className="pattern-radar-section">
              <div className="radar-section-header">
                <div className="header-badge-group">
                  <span className="radar-icon-wrap" style={{ color: 'var(--cyan)' }}>
                    <FiCreditCard />
                  </span>
                  <div>
                    <h2 className="radar-section-title">Payment Rails Friction Vectors</h2>
                    <p className="radar-section-desc">
                      Breakdown across payment methods to identify conversion bottlenecks and switchable rails.
                    </p>
                  </div>
                </div>
                <div className="header-meta-pill">
                  <span>Cluster Dimension:</span>
                  <code>transaction.method</code>
                </div>
              </div>

              {filteredRails.length === 0 ? (
                <div className="radar-empty-state">
                  <FiInfo className="empty-icon" />
                  <span>No payment rails matched your criteria.</span>
                </div>
              ) : (
                <div className="rails-matrix-grid">
                  {filteredRails.map((rail) => {
                    const icon = RAIL_ICONS[rail.method] || '💳';
                    const isHealthyRecovery = rail.recovery_rate >= 40;

                    return (
                      <div key={rail.method} className="rail-friction-card">
                        <div className="rail-card-head">
                          <div className="rail-icon-title">
                            <span className="rail-icon-box">{icon}</span>
                            <div>
                              <div className="rail-name">{rail.label}</div>
                              <span className="rail-method-slug">{rail.method.toUpperCase()}</span>
                            </div>
                          </div>
                          <span className="rail-share-badge">{rail.share_percent}% Volume</span>
                        </div>

                        <div className="rail-stats-deck">
                          <div className="rail-deck-item">
                            <span className="deck-lbl">Failures</span>
                            <span className="deck-val">{rail.count}</span>
                          </div>
                          <div className="rail-deck-item">
                            <span className="deck-lbl">At Risk</span>
                            <span className="deck-val highlight-val">₹{rail.amount?.toLocaleString()}</span>
                          </div>
                          <div className="rail-deck-item">
                            <span className="deck-lbl">Recovery</span>
                            <span className={`deck-val ${isHealthyRecovery ? 'text-green' : 'text-amber'}`}>
                              {rail.recovery_rate}%
                            </span>
                          </div>
                        </div>

                        <div className="rail-progress-wrapper">
                          <div className="rail-progress-track">
                            <div
                              className="rail-progress-fill"
                              style={{ width: `${Math.min(100, rail.recovery_rate)}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ═══════════════════════════════════════════════════════════
          SECTION 4: HIGH-VALUE AT-RISK ORDERS TABLE
      ════════════════════════════════════════════════════════════ */}
          {(activeTab === 'all' || activeTab === 'high_value') && (
            <div className="pattern-radar-section">
              <div className="radar-section-header">
                <div className="header-badge-group">
                  <span className="radar-icon-wrap" style={{ color: 'var(--yellow)' }}>
                    <FiDollarSign />
                  </span>
                  <div>
                    <h2 className="radar-section-title">High-Value Exposure Orders (&gt; ₹10,000)</h2>
                    <p className="radar-section-desc">
                      Priority recovery queue with direct link to autonomous agent reasoning trace and multi-agent debates.
                    </p>
                  </div>
                </div>
                <div className="header-meta-pill">
                  <span>Filter:</span>
                  <code>amount &gt;= ₹10,000</code>
                </div>
              </div>

              <div className="high-value-table-card">
                {filteredHighValue.length === 0 ? (
                  <div className="radar-empty-state">
                    <FiInfo className="empty-icon" />
                    <span>No high-value orders matched your criteria.</span>
                  </div>
                ) : (
                  <div className="table-responsive-wrap">
                    <table className="cyber-table">
                      <thead>
                        <tr>
                          <th>TXN REFERENCE</th>
                          <th>CUSTOMER PROFILE</th>
                          <th>PRODUCT & ORDER</th>
                          <th>EXPOSURE AMOUNT</th>
                          <th>BANK & RAIL</th>
                          <th>FAILURE REASON</th>
                          <th>RECOVERY STATE</th>
                          <th>AGENT AUDIT</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredHighValue.map((t) => {
                          const isRecovered = t.recovery_status === 'recovered';
                          const isPending = t.recovery_status === 'in_progress' || t.recovery_status === 'pending';

                          return (
                            <tr key={t.id}>
                              <td>
                                <div className="txn-id-pill">
                                  <code>{t.id}</code>
                                </div>
                              </td>
                              <td>
                                <div className="customer-cell">
                                  <span className="customer-name">{t.customer_name || 'Customer'}</span>
                                  <span className={`segment-chip ${t.customer_segment?.toLowerCase() || 'retail'}`}>
                                    {t.customer_segment || 'Retail'}
                                  </span>
                                </div>
                              </td>
                              <td>
                                <span className="product-title">{t.product_name || 'E-Commerce Order'}</span>
                              </td>
                              <td>
                                <span className="amount-highlight">₹{t.amount?.toLocaleString()}</span>
                              </td>
                              <td>
                                <div className="bank-rail-cell">
                                  <span className="bank-name-text">{t.bank || 'Unknown Bank'}</span>
                                  <span className="rail-sub-tag">{t.method?.toUpperCase()}</span>
                                </div>
                              </td>
                              <td>
                                <span className="reason-bubble" title={t.failure_reason}>
                                  {t.failure_reason?.replace(/_/g, ' ') || 'Failure'}
                                </span>
                              </td>
                              <td>
                                <span className={`recovery-badge ${t.recovery_status}`}>
                                  {isRecovered ? '✅ Recovered' : isPending ? '⏳ In Progress' : t.recovery_status}
                                </span>
                              </td>
                              <td>
                                <Link to={`/transaction/${t.id}`} className="audit-trail-link-btn">
                                  <span>Inspect Swarm</span>
                                  <FiArrowRight />
                                </Link>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
