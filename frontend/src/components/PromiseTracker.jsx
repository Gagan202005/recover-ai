import { useState, useEffect } from 'react';
import { formatDate, formatCurrencyFull } from '../utils/formatters';
import { getAllPromises, dispatchReminders, deletePromise, clearAllPromises } from '../utils/api';
import { FiTrash2, FiClock, FiSend, FiCheckCircle } from 'react-icons/fi';

export default function PromiseTracker() {
  const [promises, setPromises] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [clearingAll, setClearingAll] = useState(false);
  const [dispatchStatus, setDispatchStatus] = useState(null);

  const fetchPromises = async () => {
    try {
      const res = await getAllPromises();
      if (res?.data) {
        setPromises(res.data || []);
      }
    } catch (e) {
      console.error('Failed to load promises:', e);
    }
  };

  useEffect(() => {
    fetchPromises();
    // Fast polling every 3s for live WhatsApp demo reactivity
    const interval = setInterval(fetchPromises, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleDispatchReminders = async () => {
    setLoading(true);
    setDispatchStatus(null);
    try {
      const res = await dispatchReminders();
      const data = res?.data || {};
      if (data.dispatched_count > 0) {
        setDispatchStatus(`🎉 Dispatched ${data.dispatched_count} Reminder(s) via WhatsApp!`);
      } else {
        setDispatchStatus('ℹ️ All active reminders are already up to date!');
      }
      await fetchPromises();
      setTimeout(() => setDispatchStatus(null), 5000);
    } catch (err) {
      setDispatchStatus('⚠️ Dispatch failed. Check backend connection.');
      setTimeout(() => setDispatchStatus(null), 4000);
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePromise = async (id, e) => {
    e?.stopPropagation();
    setDeletingId(id);
    try {
      await deletePromise(id);
      setPromises(prev => prev.filter(p => p.id !== id));
      setDispatchStatus('🗑️ Reminder deleted successfully.');
      setTimeout(() => setDispatchStatus(null), 3000);
    } catch (err) {
      console.error('Failed to delete reminder:', err);
      setDispatchStatus('⚠️ Failed to delete reminder.');
      setTimeout(() => setDispatchStatus(null), 3000);
    } finally {
      setDeletingId(null);
    }
  };

  const handleClearAll = async () => {
    if (promises.length === 0) return;
    if (!window.confirm(`Are you sure you want to delete all ${promises.length} scheduled reminders?`)) {
      return;
    }
    setClearingAll(true);
    try {
      await clearAllPromises();
      setPromises([]);
      setDispatchStatus('🗑️ All reminders cleared.');
      setTimeout(() => setDispatchStatus(null), 3000);
    } catch (err) {
      console.error('Failed to clear reminders:', err);
      setDispatchStatus('⚠️ Failed to clear all reminders.');
      setTimeout(() => setDispatchStatus(null), 3000);
    } finally {
      setClearingAll(false);
    }
  };

  const activePromises = promises.filter(p => p.status === 'promised');
  const totalPromised = activePromises.reduce((acc, p) => acc + (p.promise_amount || 0), 0);

  const getDaysDiff = (dateStr) => {
    if (!dateStr) return '';
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const target = new Date(dateStr);
    target.setHours(0, 0, 0, 0);
    const diffTime = target - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return 'Due Today ⚡';
    if (diffDays === 1) return 'Tomorrow ⏳';
    if (diffDays > 1) return `In ${diffDays} days 📅`;
    return 'Overdue ⚠️';
  };

  return (
    <div className="card promise-tracker-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>

        <div className="card-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          🤝 Two-Way Promise & Reminder Scheduler
          <span style={{ 
            background: 'var(--accent-glow)', 
            color: 'var(--accent)', 
            padding: '2px 8px', 
            borderRadius: 12, 
            fontSize: 10, 
            fontWeight: 700 
          }}>
            {promises.length} SAVED
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {promises.length > 0 && (
            <button
              onClick={handleClearAll}
              disabled={clearingAll || loading}
              style={{
                background: 'rgba(239, 68, 68, 0.12)',
                color: '#f87171',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                padding: '6px 12px',
                borderRadius: 8,
                fontSize: 11,
                fontWeight: 700,
                cursor: clearingAll ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                transition: 'all 0.2s ease',
              }}
              title="Delete all reminders"
            >
              <FiTrash2 size={12} />
              {clearingAll ? 'Clearing...' : 'Clear All'}
            </button>
          )}

          <button
            onClick={handleDispatchReminders}
            disabled={loading || clearingAll}
            style={{
              background: loading ? 'var(--bg-secondary)' : 'var(--gradient-primary)',
              color: 'white',
              border: 'none',
              padding: '6px 14px',
              borderRadius: 8,
              fontSize: 11,
              fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              boxShadow: '0 2px 10px rgba(99, 102, 241, 0.3)',
              transition: 'all 0.2s ease',
            }}
          >
            <FiSend size={12} />
            {loading ? '⏳ Dispatching...' : '⚡ Trigger Due Reminders'}
          </button>
        </div>
      </div>

      {dispatchStatus && (
        <div style={{
          background: dispatchStatus.includes('🎉') ? 'var(--green-glow)' : dispatchStatus.includes('🗑️') ? 'rgba(239, 68, 68, 0.12)' : 'var(--bg-secondary)',
          border: `1px solid ${dispatchStatus.includes('🎉') ? 'var(--green)' : dispatchStatus.includes('🗑️') ? 'rgba(239, 68, 68, 0.3)' : 'var(--border)'}`,
          color: dispatchStatus.includes('🎉') ? 'var(--green)' : dispatchStatus.includes('🗑️') ? '#f87171' : 'var(--text-primary)',
          padding: '8px 12px',
          borderRadius: 6,
          fontSize: 12,
          fontWeight: 600,
          marginBottom: 12,
          textAlign: 'center',
        }}>
          {dispatchStatus}
        </div>
      )}

      {/* Summary KPI Banner */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 10,
        marginBottom: 16,
        background: 'var(--bg-secondary)',
        padding: 12,
        borderRadius: 8,
        border: '1px solid var(--border)',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Active Promises</div>
          <div style={{ fontSize: 17, fontWeight: 800, color: 'var(--accent)', marginTop: 2 }}>
            {activePromises.length}
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Reserved Revenue</div>
          <div style={{ fontSize: 17, fontWeight: 800, color: 'var(--green)', marginTop: 2 }}>
            {formatCurrencyFull(totalPromised)}
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Auto-Remind Engine</div>
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--cyan)', marginTop: 4 }}>
            Wabery WhatsApp 💬
          </div>
        </div>
      </div>

      {promises.length === 0 ? (
        <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '32px 0', background: 'rgba(255,255,255,0.02)', borderRadius: 8 }}>
          No customer promises recorded yet. Reply to any recovery WhatsApp with a date (e.g. "I will pay tomorrow") to test live!
        </div>
      ) : (
        <div className="promise-table-container">
          <table className="promise-table">
            <thead>
              <tr>
                <th className="th-customer">Customer</th>
                <th className="th-order">Order & Amount</th>
                <th className="th-timeline">Promise Timeline</th>
                <th className="th-status">Scheduled Status</th>
                <th className="th-action">Action</th>
              </tr>
            </thead>
            <tbody>
              {promises.map(p => {
                const diffLabel = getDaysDiff(p.promise_date);
                const isDueToday = diffLabel.includes('Today');
                const isDeleting = deletingId === p.id;

                return (
                  <tr key={p.id} className={`promise-row ${isDeleting ? 'row-deleting' : ''}`}>
                    <td className="td-customer">
                      <div className="customer-name-text">
                        {p.customers?.name || 'Gagan Singhal'}
                      </div>
                      <div className="customer-phone-mono">
                        {p.customers?.phone || '+918077344252'}
                      </div>
                    </td>
                    <td className="td-order">
                      <div className="order-name-text">
                        {p.transactions?.product_name || 'Silk Kurta Set'}
                      </div>
                      <div className="order-amount-pill">
                        {formatCurrencyFull(p.promise_amount)}
                      </div>
                    </td>
                    <td className="td-timeline">
                      <div className={`timeline-date-text ${isDueToday ? 'date-due-today' : ''}`}>
                        {formatDate(p.promise_date)}
                      </div>
                      <div className={`timeline-diff-tag ${isDueToday ? 'tag-today' : ''}`}>
                        {diffLabel}
                      </div>
                    </td>
                    <td className="td-status">
                      <span className={`promise-status-badge ${p.status === 'fulfilled' ? 'status-fulfilled' : p.status === 'promised' ? 'status-scheduled' : 'status-pending'}`}>
                        {p.status === 'promised' ? '⏳ Scheduled' : p.status === 'fulfilled' ? '✅ Reminded' : p.status}
                      </span>
                    </td>
                    <td className="td-action">
                      <button
                        className="promise-delete-btn"
                        onClick={(e) => handleDeletePromise(p.id, e)}
                        disabled={isDeleting || clearingAll}
                        title="Delete this reminder"
                      >
                        <FiTrash2 size={13} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
