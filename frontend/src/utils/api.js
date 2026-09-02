import axios from 'axios';

const api = axios.create({
  baseURL: '',
  timeout: 10000,
});


// Dashboard
export const getDashboardMetrics = () => api.get('/api/dashboard/metrics');
export const getAgentFeed = (limit = 50) => api.get(`/api/dashboard/agent-feed?limit=${limit}`);
export const getRecoveryFunnel = () => api.get('/api/dashboard/funnel');
export const getFailurePatterns = () => api.get('/api/dashboard/patterns');
export const getDetailedPatterns = () => api.get('/api/dashboard/patterns/detailed');
export const getABTests = () => api.get('/api/dashboard/ab-tests');
export const getLanguageStats = () => api.get('/api/dashboard/language-stats');

// Transactions
export const getTransactions = (params = {}) => api.get('/api/transactions/', { params });
export const getTransaction = (id) => api.get(`/api/transactions/${id}`);
export const getAuditTrail = (id) => api.get(`/api/transactions/${id}/audit-trail`);
export const getDebates = (id) => api.get(`/api/transactions/${id}/debates`);
export const getPromises = (id) => api.get(`/api/transactions/${id}/promises`);
export const getAllPromises = () => api.get('/api/transactions/promises/all');
export const dispatchReminders = () => api.post('/api/transactions/reminders/dispatch');
export const deletePromise = (id) => api.delete(`/api/transactions/promises/${id}`);
export const clearAllPromises = () => api.delete('/api/transactions/promises/all');


// Simulation & Gateway
export const getScenarios = () => api.get('/api/simulation/scenarios');
export const triggerScenario = (key) => api.post(`/api/simulation/trigger/${key}`);
export const createCheckoutOrder = (key) => api.post(`/api/simulation/create-checkout-order/${key}`);
export const reportGatewayFailure = (data) => api.post('/api/simulation/report-gateway-failure', data);
export const reportGatewaySuccess = (data) => api.post('/api/simulation/report-gateway-success', data);
export const syncRazorpayFailures = () => api.post('/api/transactions/sync-razorpay-failures');
export const approveTransaction = (id) => api.post(`/api/simulation/approve/${id}`);

// Reports
export const downloadPDF = () => api.get('/api/reports/pdf', { responseType: 'blob' });

// MCP
export const getMCPServers = () => api.get('/api/mcp/servers');

export default api;
