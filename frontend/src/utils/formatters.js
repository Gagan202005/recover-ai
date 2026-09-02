export const formatCurrency = (paise) => {
  const rupees = Math.floor(paise / 100);
  if (rupees >= 100000) return `₹${(rupees / 100000).toFixed(1)}L`;
  if (rupees >= 1000) return `₹${(rupees / 1000).toFixed(1)}K`;
  return `₹${rupees.toLocaleString('en-IN')}`;
};

export const formatCurrencyFull = (paise) => {
  return `₹${Math.floor(paise / 100).toLocaleString('en-IN')}`;
};

export const formatTime = (isoString) => {
  if (!isoString) return '';
  const d = new Date(isoString);
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

export const formatDate = (isoString) => {
  if (!isoString) return '';
  return new Date(isoString).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
};

export const formatRelativeTime = (isoString) => {
  if (!isoString) return '';
  const seconds = Math.floor((new Date() - new Date(isoString)) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
};

export const agentIcons = {
  sentinel: '🛡️',
  diagnostician: '🔬',
  strategist: '🎯',
  compliance: '⚖️',
  executor: '⚡',
  analyst: '📊',
};

export const agentColors = {
  sentinel: '#60a5fa',
  diagnostician: '#a78bfa',
  strategist: '#f59e0b',
  compliance: '#ef4444',
  executor: '#22c55e',
  analyst: '#06b6d4',
};

export const statusColors = {
  recovered: '#22c55e',
  exception: '#ef4444',
  in_progress: '#f59e0b',
  pending: '#6b7280',
  human_review: '#f97316',
  blocked: '#ef4444',
};
