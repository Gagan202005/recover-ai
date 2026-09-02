import { useState, useEffect } from 'react';
import MetricCards from './MetricCards';
import SwarmTopology from './SwarmTopology';
import LiveDemoButtons from './LiveDemoButtons';
import LiveAgentFeed from './LiveAgentFeed';
import PromiseTracker from './PromiseTracker';
import ABTestResults from './ABTestResults';
import LanguageStats from './LanguageStats';
import ExceptionReport from './ExceptionReport';
import Confetti from './Confetti';
import { getDashboardMetrics, getFailurePatterns, getAgentFeed, syncRazorpayFailures, downloadPDF } from '../utils/api';
import { useRealtimeFeed } from '../hooks/useSupabaseRealtime';
import { useSounds } from '../hooks/useSounds';
import { FiZap, FiCalendar, FiTrendingUp, FiShield, FiVolume2, FiVolumeX, FiRefreshCw } from 'react-icons/fi';

export default function WarRoom() {
  const [metrics, setMetrics] = useState(null);
  const [patterns, setPatterns] = useState([]);
  const [initialFeed, setInitialFeed] = useState([]);
  const [realtimeFeed, setRealtimeFeed] = useRealtimeFeed();
  const [showConfetti, setShowConfetti] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [activeTab, setActiveTab] = useState('feed'); // 'feed' | 'promises' | 'ab_tests' | 'compliance'
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [syncing, setSyncing] = useState(false);

  const { play } = useSounds();

  const fetchData = async () => {
    try {
      const [metricsRes, patternsRes, feedRes] = await Promise.all([
        getDashboardMetrics(),
        getFailurePatterns(),
        getAgentFeed(50),
      ]);
      setMetrics(metricsRes.data);
      setPatterns(patternsRes.data);
      setInitialFeed(feedRes.data);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRecovery = () => {
    setShowConfetti(true);
    if (soundEnabled) {
      play('kaching');
    }
    setTimeout(() => setShowConfetti(false), 4500);
    fetchData();
  };

  const handleAgentSelect = (agentId) => {
    setSelectedAgent(agentId);
    if (agentId) {
      setActiveTab('feed'); // automatically switch to feed when filtering by agent
    }
  };

  const handleSyncRazorpay = async () => {
    setSyncing(true);
    try {
      const res = await syncRazorpayFailures();
      fetchData();
      alert(`✅ Synced with Razorpay API!\n• Ingested: ${res.data?.newly_ingested_count || 0} new failures.`);
    } catch (e) {
      console.error('Sync failed:', e);
    } finally {
      setSyncing(false);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const res = await downloadPDF();
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'RecoverAI_Audit_Report.html';
      a.click();
    } catch (err) {
      console.error('PDF download failed:', err);
    }
  };

  const allFeed = [...realtimeFeed, ...initialFeed];

  const streamTabs = [
    { id: 'feed', label: '⚡ Neural Agent Stream', badge: allFeed.length },
    { id: 'promises', label: '🤝 WhatsApp Promises & Reminders', badge: null },
    { id: 'ab_tests', label: '🧪 A/B & Language Matrix', badge: null },
    { id: 'compliance', label: '🛡️ Guardrail Ledger', badge: metrics?.exceptions?.count || 0 },
  ];

  return (
    <div className="war-room-command-center">
      {showConfetti && <Confetti />}

      {/* SECTION 1: EXECUTIVE METRIC CARDS */}
      <section className="war-room-section telemetry-section">
        <MetricCards
          metrics={metrics}
          onSync={handleSyncRazorpay}
          onDownloadPDF={handleDownloadPDF}
          syncing={syncing}
        />
      </section>

      {/* SECTION 2: TOPOLOGICAL 6-AGENT SWARM VISUALIZER */}
      <section className="war-room-section topology-section">
        <SwarmTopology
          activeAgent={selectedAgent}
          onSelectAgent={handleAgentSelect}
        />
      </section>

      {/* SECTION 3: DUAL-COCKPIT WORKSPACE */}
      <section className="war-room-section cockpit-section">
        <div className="dual-cockpit-grid">
          {/* LEFT COCKPIT: LIVE FAILURE INJECTION & DEMO LAUNCHPAD */}
          <div className="cockpit-column left-cockpit">
            <LiveDemoButtons
              onRecovery={handleRecovery}
              onRefresh={fetchData}
            />
          </div>

          {/* RIGHT COCKPIT: MODULAR INTELLIGENCE & STREAM DECK */}
          <div className="cockpit-column right-cockpit">
            <div className="stream-deck-card">
              {/* TAB SELECTOR HEADER */}
              <div className="stream-deck-tabs-header">
                <div className="stream-deck-tabs">
                  {streamTabs.map((tab) => (
                    <button
                      key={tab.id}
                      className={`stream-tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                      onClick={() => setActiveTab(tab.id)}
                    >
                      <span>{tab.label}</span>
                      {tab.badge !== null && tab.badge > 0 && (
                        <span className="stream-tab-badge">{tab.badge}</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* TAB CONTENT AREA */}
              <div className="stream-deck-content">
                {activeTab === 'feed' && (
                  <LiveAgentFeed
                    feed={allFeed}
                    selectedAgent={selectedAgent}
                    onSelectAgent={handleAgentSelect}
                  />
                )}

                {activeTab === 'promises' && (
                  <div className="tab-pane-padded">
                    <PromiseTracker />
                  </div>
                )}

                {activeTab === 'ab_tests' && (
                  <div className="tab-pane-padded intelligence-subgrid">
                    <ABTestResults />
                    <LanguageStats />
                  </div>
                )}

                {activeTab === 'compliance' && (
                  <div className="tab-pane-padded">
                    <ExceptionReport />
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
