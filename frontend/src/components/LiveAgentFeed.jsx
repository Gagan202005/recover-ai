import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { agentIcons, agentColors, formatRelativeTime } from '../utils/formatters';
import { FiFilter, FiSearch, FiChevronDown, FiChevronUp, FiExternalLink, FiPause, FiPlay, FiZap } from 'react-icons/fi';

export default function LiveAgentFeed({ feed, selectedAgent, onSelectAgent }) {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [isPaused, setIsPaused] = useState(false);

  const filterAgent = selectedAgent || 'all';

  const filteredFeed = useMemo(() => {
    return feed.filter((item) => {
      // Agent filter
      if (filterAgent !== 'all' && item.agent !== filterAgent) {
        return false;
      }
      // Search filter
      if (searchTerm.trim()) {
        const term = searchTerm.toLowerCase();
        const txn = (item.transaction_id || '').toLowerCase();
        const action = (item.action || '').toLowerCase();
        const agent = (item.agent || '').toLowerCase();
        const details = JSON.stringify(item.details || {}).toLowerCase();
        return txn.includes(term) || action.includes(term) || agent.includes(term) || details.includes(term);
      }
      return true;
    });
  }, [feed, filterAgent, searchTerm]);

  const getActionHeadline = (item) => {
    const agent = item.agent || '';
    const action = item.action || '';
    const details = item.details || {};

    if (agent === 'sentinel') {
      return {
        tag: 'INGESTED',
        tagColor: '#06b6d4',
        text: `Ingested failure — Priority: ${details.priority || 'medium'} | Urgency: ${details.urgency_score || 'N/A'}`,
      };
    }
    if (agent === 'diagnostician') {
      return {
        tag: 'DIAGNOSED',
        tagColor: '#8b5cf6',
        text: `Root cause identified: ${details.root_cause || 'unknown'} (${Math.round((details.confidence || 0) * 100)}% confidence)`,
      };
    }
    if (agent === 'strategist') {
      return {
        tag: 'PLANNED',
        tagColor: '#6366f1',
        text: `Recovery policy: ${details.channel || 'N/A'} in ${details.language || 'english'} (Tone: ${details.tone || 'friendly'})`,
      };
    }
    if (agent === 'compliance' && action === 'blocked') {
      return {
        tag: 'BLOCKED',
        tagColor: '#ef4444',
        text: `Compliance Gate Blocked: ${details.block_reason || 'Guardrail restriction enforced'}`,
      };
    }
    if (agent === 'compliance' && action === 'modified') {
      return {
        tag: 'MODIFIED',
        tagColor: '#f59e0b',
        text: `Compliance Modified channel/schedule per regulatory rules.`,
      };
    }
    if (agent === 'compliance') {
      return {
        tag: 'APPROVED',
        tagColor: '#10b981',
        text: `All 8 Guardrail checks passed — Approved for dispatch.`,
      };
    }
    if (action === 'promise_reminder_dispatched') {
      return {
        tag: 'REMINDER',
        tagColor: '#06b6d4',
        text: `Scheduled Reminder Dispatched via ${details.channel || 'WhatsApp'}`,
      };
    }
    if (agent === 'executor') {
      return {
        tag: 'DISPATCHED',
        tagColor: '#10b981',
        text: `Executed via MCP: ${details.channel || 'N/A'} → outcome: ${details.outcome || 'sent'}`,
      };
    }
    if (agent === 'analyst') {
      return {
        tag: details.recovery_successful ? 'RECOVERED' : 'ANALYZED',
        tagColor: details.recovery_successful ? '#10b981' : '#ec4899',
        text: details.recovery_successful
          ? `💰 Capital Salvaged via ${details.channel_used || 'channel'}! Knowledge graph updated.`
          : `Post-recovery analysis completed | Playbook updated.`,
      };
    }
    return { tag: 'ACTION', tagColor: '#6366f1', text: action };
  };

  const agentPills = [
    { id: 'all', label: 'All Agents', icon: '⚡' },
    { id: 'sentinel', label: 'Sentinel', icon: '🛡️' },
    { id: 'diagnostician', label: 'Diagnostician', icon: '🔬' },
    { id: 'strategist', label: 'Strategist', icon: '🧠' },
    { id: 'compliance', label: 'Compliance', icon: '⚖️' },
    { id: 'executor', label: 'Executor', icon: '⚡' },
    { id: 'analyst', label: 'Analyst', icon: '📊' },
  ];

  return (
    <div className="card neural-feed-deck">
      {/* FEED HEADER & CONTROLS */}
      <div className="neural-feed-header">
        <div className="feed-header-title-box">
          <div className="feed-title-with-pulse">
            <span className="neural-activity-beacon"></span>
            ⚡ Neural Agent Stream
          </div>
          <span className="feed-counter-pill">{filteredFeed.length} Events</span>
        </div>

        <div className="feed-header-actions">
          <button
            className={`feed-pause-btn ${isPaused ? 'active' : ''}`}
            onClick={() => setIsPaused(!isPaused)}
            title={isPaused ? 'Resume live autoscroll' : 'Pause live autoscroll'}
          >
            {isPaused ? <FiPlay size={12} /> : <FiPause size={12} />}
            <span>{isPaused ? 'Live Stream Paused' : 'Live Stream'}</span>
          </button>
        </div>
      </div>

      {/* FILTER PILLS & SEARCH BAR */}
      <div className="feed-control-bar">
        <div className="feed-agent-pills-row">
          {agentPills.map((pill) => (
            <button
              key={pill.id}
              className={`feed-agent-pill ${filterAgent === pill.id ? 'active' : ''}`}
              onClick={() => onSelectAgent(pill.id === 'all' ? null : pill.id)}
            >
              <span>{pill.icon}</span>
              <span>{pill.label}</span>
            </button>
          ))}
        </div>

        <div className="feed-search-wrap">
          <FiSearch className="feed-search-icon" size={13} />
          <input
            type="text"
            placeholder="Search txn ID, action, channel..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="feed-search-input"
          />
          {searchTerm && (
            <button className="feed-search-clear" onClick={() => setSearchTerm('')}>
              ✕
            </button>
          )}
        </div>
      </div>

      {/* FEED LIST */}
      <div className="neural-feed-list">
        {filteredFeed.length === 0 ? (
          <div className="feed-empty-state">
            <div className="empty-icon">🛰️</div>
            <div className="empty-title">No matching agent activities found</div>
            <div className="empty-subtitle">Trigger a live demo scenario to watch the 6-agent swarm collaborate!</div>
          </div>
        ) : (
          filteredFeed.slice(0, 40).map((item, i) => {
            const headline = getActionHeadline(item);
            const isExpanded = expandedIndex === i;
            const agentCol = agentColors[item.agent] || '#6366f1';

            return (
              <div key={item.id || i} className="neural-feed-row">
                <div className="feed-timeline-node">
                  <div className="feed-avatar" style={{ '--agent-col': agentCol }}>
                    {agentIcons[item.agent] || '🤖'}
                  </div>
                  <div className="feed-timeline-stem"></div>
                </div>

                <div className="feed-body-card">
                  <div className="feed-body-top">
                    <div className="feed-agent-info">
                      <span className="feed-agent-name" style={{ color: agentCol }}>
                        {item.agent ? item.agent.toUpperCase() : 'SWARM'}
                      </span>
                      <span className="feed-action-badge" style={{ '--tag-col': headline.tagColor }}>
                        {headline.tag}
                      </span>
                    </div>

                    <div className="feed-meta-right">
                      <span className="feed-time-text">{formatRelativeTime(item.created_at)}</span>
                      {item.transaction_id && (
                        <button
                          className="feed-txn-link-btn"
                          onClick={() => navigate(`/transaction/${item.transaction_id}`)}
                          title="Inspect full transaction recovery audit"
                        >
                          <span>{item.transaction_id}</span>
                          <FiExternalLink size={10} />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="feed-headline-text">{headline.text}</div>

                  {/* Expandable JSON Details */}
                  {item.details && Object.keys(item.details).length > 0 && (
                    <div className="feed-details-section">
                      <button
                        className="feed-expand-toggle"
                        onClick={() => setExpandedIndex(isExpanded ? null : i)}
                      >
                        <span>{isExpanded ? 'Hide Execution Telemetry' : 'Inspect Agent Reasoning & MCP Metadata'}</span>
                        {isExpanded ? <FiChevronUp size={12} /> : <FiChevronDown size={12} />}
                      </button>

                      {isExpanded && (
                        <div className="feed-details-drawer">
                          <pre className="feed-json-viewer">{JSON.stringify(item.details, null, 2)}</pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
