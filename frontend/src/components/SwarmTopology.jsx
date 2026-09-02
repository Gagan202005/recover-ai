import React from 'react';
import { FiShield, FiSearch, FiCpu, FiLock, FiZap, FiActivity, FiArrowRight } from 'react-icons/fi';

const AGENTS = [
  {
    id: 'sentinel',
    name: 'Sentinel',
    role: 'Failure Detection & Urgency Scoring',
    icon: FiShield,
    color: '#06b6d4', // Cyan
    latency: '32ms',
    tools: 'Razorpay Webhook / Polling',
    status: 'ONLINE',
  },
  {
    id: 'diagnostician',
    name: 'Diagnostician',
    role: 'Root Cause & Bank Outage Radar',
    icon: FiSearch,
    color: '#8b5cf6', // Purple
    latency: '88ms',
    tools: 'RAG: Error Codes (Pinecone)',
    status: 'ONLINE',
  },
  {
    id: 'strategist',
    name: 'Strategist',
    role: 'Recovery Policy & Thompson Sampling',
    icon: FiCpu,
    color: '#6366f1', // Indigo
    latency: '145ms',
    tools: 'Gemini 2.5 + A/B Engine',
    status: 'OPTIMAL',
  },
  {
    id: 'compliance',
    name: 'Compliance Gate',
    role: '8 Guardrail Checks & DND Routing',
    icon: FiLock,
    color: '#f59e0b', // Amber
    latency: '42ms',
    tools: 'TRAI / RBI Regulatory KB',
    status: 'GUARDED',
  },
  {
    id: 'executor',
    name: 'Executor (MCP)',
    role: 'Autonomous Multi-Channel Dispatch',
    icon: FiZap,
    color: '#10b981', // Emerald
    latency: '110ms',
    tools: 'Wabery, Twilio, Razorpay Link',
    status: 'ACTIVE',
  },
  {
    id: 'analyst',
    name: 'Analyst',
    role: 'Continuous Playbook Learning Loop',
    icon: FiActivity,
    color: '#ec4899', // Pink
    latency: '65ms',
    tools: 'Supabase Vector Memory',
    status: 'LEARNING',
  },
];

export default function SwarmTopology({ activeAgent, onSelectAgent, activeCount = 6 }) {
  return (
    <div className="swarm-topology-deck">
      <div className="swarm-topology-header">
        <div className="swarm-header-left">
          <div className="swarm-live-pill">
            <span className="live-pulse-dot"></span>
            AUTONOMOUS LANGGRAPH SWARM
          </div>
          <span className="swarm-subtitle">6 Cooperative Neural Agents with Real-Time MCP Tool Execution</span>
        </div>
        <div className="swarm-header-right">
          {activeAgent && (
            <button className="swarm-reset-filter-btn" onClick={() => onSelectAgent(null)}>
              ✕ Clear Filter ({activeAgent})
            </button>
          )}
          <span className="swarm-latency-badge">
            ⚡ Avg Pipeline Latency: <strong>~480ms</strong>
          </span>
        </div>
      </div>

      <div className="swarm-nodes-container">
        {AGENTS.map((agent, index) => {
          const Icon = agent.icon;
          const isSelected = activeAgent === agent.id;
          const isLast = index === AGENTS.length - 1;

          return (
            <React.Fragment key={agent.id}>
              <div
                className={`swarm-node-card ${isSelected ? 'selected' : ''}`}
                style={{ '--agent-color': agent.color }}
                onClick={() => onSelectAgent(isSelected ? null : agent.id)}
                title={`Filter feed for ${agent.name} decisions`}
              >
                <div className="swarm-node-glow"></div>
                <div className="swarm-node-top">
                  <div className="swarm-node-icon" style={{ color: agent.color }}>
                    <Icon size={18} />
                  </div>
                  <div className="swarm-node-status-pill">
                    <span className="node-status-dot" style={{ background: agent.color }}></span>
                    {agent.status}
                  </div>
                </div>

                <div className="swarm-node-body">
                  <div className="swarm-node-name">{agent.name}</div>
                  <div className="swarm-node-role">{agent.role}</div>
                </div>

                <div className="swarm-node-footer">
                  <span className="swarm-node-tool">{agent.tools}</span>
                  <span className="swarm-node-latency">{agent.latency}</span>
                </div>
              </div>

              {!isLast && (
                <div className="swarm-connector-arrow">
                  <div className="connector-line">
                    <span className="data-packet-particle"></span>
                  </div>
                  <FiArrowRight className="connector-chevron" size={14} />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
