import { useState, useEffect } from 'react';
import { getScenarios, createCheckoutOrder, reportGatewayFailure, reportGatewaySuccess, triggerScenario, syncRazorpayFailures, downloadPDF } from '../utils/api';
import { FiZap, FiRefreshCw, FiFileText } from 'react-icons/fi';

// Dynamic script loader for Razorpay checkout SDK
const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    const existingScript = document.querySelector('script[src="https://checkout.razorpay.com/v1/checkout.js"]');
    if (existingScript) {
      existingScript.onload = () => resolve(true);
      existingScript.onerror = () => resolve(false);
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

export default function LiveDemoButtons({ onRecovery, onRefresh }) {
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState({});
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadRazorpayScript();
    getScenarios()
      .then(res => setScenarios(res.data))
      .catch(() => {});
  }, []);

  const SCENARIO_ORDER = [
    'card_expired',
    'invoice_overdue',
    'checkout_abandoned',
    'opted_out',
    'bank_decline',
  ];

  const meta = {
    card_expired: {
      icon: '💳',
      title: 'Card Expired / 3DS Fail',
      strategy: '1-Click WhatsApp Payment Link',
      product: 'Silk Kurta Set (₹4,299)',
      persona: 'VIP Customer',
      color: '#6366f1',
    },
    invoice_overdue: {
      icon: '📄',
      title: 'B2B Invoice Overdue',
      strategy: 'AI Voice Call Reminder + Email Link',
      product: 'IT Support Contract (₹45,000)',
      persona: 'Enterprise B2B',
      color: '#f59e0b',
    },
    checkout_abandoned: {
      icon: '🛒',
      title: 'Checkout Drop-Off',
      strategy: 'Email Recovery + Multi-Channel',
      product: 'Coffee Machine (₹8,999)',
      persona: 'Cart Abandoner',
      color: '#10b981',
    },
    opted_out: {
      icon: '❌',
      title: 'DND Opt-Out Request',
      strategy: 'Zero-Contact Compliance Block',
      product: 'Perfume Set (₹2,999)',
      persona: 'TRAI DND Active',
      color: '#ef4444',
    },
    bank_decline: {
      icon: '🏦',
      title: 'Bank Outage / Decline',
      strategy: 'Outage Radar + 2h Auto-Retry',
      product: 'Premium Headphones (₹2,499)',
      persona: 'HDFC Node',
      color: '#06b6d4',
    },
  };

  // Open Real Razorpay Checkout Popup with dynamic fallback
  const handleOpenRazorpayPopup = async (scenarioKey) => {
    setLoading(prev => ({ ...prev, [scenarioKey]: true }));

    try {
      // 1. Ensure Razorpay SDK is loaded
      const isLoaded = await loadRazorpayScript();

      // 2. Create order on backend
      const res = await createCheckoutOrder(scenarioKey);
      const data = res.data || {};

      if (!isLoaded || !window.Razorpay) {
        console.warn('⚠️ Razorpay SDK not available, executing direct backend simulation trigger...');
        await triggerScenario(scenarioKey);
        setTimeout(() => onRefresh(), 1000);
        return;
      }

      const options = {
        key: data.key_id || 'rzp_test_SgR14AJe2VUGPV',
        amount: data.amount || 429900,
        currency: data.currency || 'INR',
        name: 'StyleBazaar (RecoverAI)',
        description: data.product_name || 'Recovery Demo Order',
        prefill: {
          name: data.customer?.name || 'Gagan Singhal',
          email: data.customer?.email || 'gagansinghal2005@gmail.com',
          contact: data.customer?.contact || '+918077344252',
        },
        theme: {
          color: '#6366f1',
          backdrop_color: 'rgba(10, 10, 26, 0.85)',
        },
        modal: {
          ondismiss: () => {
            setLoading(prev => ({ ...prev, [scenarioKey]: false }));
            setTimeout(() => onRefresh(), 1000);
          },
        },
        handler: async (response) => {
          setLoading(prev => ({ ...prev, [scenarioKey]: false }));
          try {
            await reportGatewaySuccess({
              transaction_id: data.transaction_id,
              order_id: data.order_id,
              payment_id: response.razorpay_payment_id,
            });
          } catch (e) {}
          onRecovery();
          setTimeout(() => onRefresh(), 1000);
        },
      };

      if (data.order_id) {
        options.order_id = data.order_id;
      }

      const rzp = new window.Razorpay(options);

      rzp.on('payment.failed', async (response) => {
        setLoading(prev => ({ ...prev, [scenarioKey]: false }));
        try {
          const err = response.error || {};
          const failurePayload = {
            scenario_key: scenarioKey,
            transaction_id: data.transaction_id,
            order_id: data.order_id,
            payment_id: err.metadata?.payment_id || '',
            error_code: err.code || 'GATEWAY_ERROR',
            error_description: err.description || 'Payment failed at bank gateway',
            error_source: err.source || 'gateway',
            error_reason: err.reason || 'payment_failed',
          };
          await reportGatewayFailure(failurePayload);
        } catch (e) {
          console.error('Failed to report gateway failure:', e);
        }
        setTimeout(() => onRefresh(), 1000);
      });

      rzp.open();
    } catch (err) {
      console.error('Razorpay popup error, falling back to direct swarm trigger:', err);
      try {
        await triggerScenario(scenarioKey);
        setTimeout(() => onRefresh(), 1000);
      } catch (e) {}
    } finally {
      setLoading(prev => ({ ...prev, [scenarioKey]: false }));
    }
  };

  const handleSyncRazorpay = async () => {
    setSyncing(true);
    try {
      const res = await syncRazorpayFailures();
      const count = res.data?.newly_ingested_count || 0;
      onRefresh();
      alert(`✅ Synced with Razorpay API!\n• Total Failures Found: ${res.data?.total_failures_in_razorpay || 0}\n• Newly Ingested: ${count}`);
    } catch (e) {
      console.error('Sync failed:', e);
    } finally {
      setSyncing(false);
    }
  };

  const handlePDF = async () => {
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

  // Deterministically sort scenarios according to specified order: Card -> Checkout -> DND -> Bank Outage -> Invoice
  const sortedScenarios = [...scenarios].sort((a, b) => {
    const indexA = SCENARIO_ORDER.indexOf(a.key);
    const indexB = SCENARIO_ORDER.indexOf(b.key);
    return (indexA === -1 ? 99 : indexA) - (indexB === -1 ? 99 : indexB);
  });

  return (
    <div className="card scenario-launchpad-card">
      <div className="launchpad-header">
        <div>
          <div className="card-title" style={{ marginBottom: 4 }}>
            ⚡ Autonomous Revenue Recovery Launchpad
          </div>
          <p className="launchpad-subtitle">
            Trigger real-time payment failure recovery scenarios through the 6-agent swarm.
          </p>
        </div>

        <div className="launchpad-quick-actions">
          <button
            className="launchpad-sync-btn"
            onClick={handleSyncRazorpay}
            disabled={syncing}
            title="Poll Razorpay Dashboard API directly for recent failed payments"
          >
            <FiRefreshCw className={syncing ? 'spin-icon' : ''} size={12} />
            <span>{syncing ? 'Syncing...' : 'Sync Gateway'}</span>
          </button>

          <button
            className="launchpad-report-btn"
            onClick={handlePDF}
            title="Download executive regulatory compliance and recovery audit report"
          >
            <FiFileText size={12} />
            <span>Audit PDF</span>
          </button>
        </div>
      </div>

      <div className="scenario-deck-grid">
        {sortedScenarios.map((s) => {
          const info = meta[s.key] || {
            icon: '⚡',
            title: s.key.replace(/_/g, ' '),
            strategy: 'Autonomous Recovery',
            product: 'Demo Order',
            persona: 'Test Customer',
            color: '#6366f1',
          };
          const isLoading = loading[s.key];

          return (
            <div
              key={s.key}
              className="scenario-glass-box"
              style={{ '--box-accent': info.color }}
            >
              <div className="scenario-top-line">
                <span className="scenario-vector-icon">{info.icon}</span>
                <div className="scenario-name-wrap">
                  <div className="scenario-title-text">{info.title}</div>
                  <div className="scenario-product-tag">{info.product}</div>
                </div>
              </div>

              <div className="scenario-strategy-badge">
                <span className="strategy-dot" style={{ background: info.color }}></span>
                <span>{info.strategy}</span>
              </div>

              <button
                className={`scenario-trigger-btn ${isLoading ? 'btn-loading' : ''}`}
                onClick={() => handleOpenRazorpayPopup(s.key)}
                disabled={isLoading}
                title="Open authentic Razorpay Checkout modal in Test Mode"
              >
                <FiZap size={13} />
                <span>{isLoading ? 'Launching Razorpay...' : '⚡ Pay on Razorpay Gateway'}</span>
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
