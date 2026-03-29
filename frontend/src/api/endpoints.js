import api from './client';

export const authApi = {
  login: (payload) => api.post('/auth/login', payload),
  register: (payload) => api.post('/auth/register', payload),
  me: () => api.get('/auth/me'),
  updateWallet: (payload) => api.put('/auth/wallet', payload),
};

export const propertyApi = {
  list: (params = {}) => {
    const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== '' && v !== null && v !== undefined));
    return api.get('/properties', { params: clean });
  },
  detail: (id) => api.get(`/properties/${id}`),
  create: (formData) => api.post('/properties', formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  myListings: () => api.get('/properties/me/listings'),
};

export const investmentApi = {
  buyShares: (payload) => api.post('/investments/buy', payload),
  createListing: (payload) => api.post('/investments/list', payload),
  getListings: () => api.get('/investments/listings'),
  tradeShares: (payload) => api.post('/investments/trade', payload),
  exitSimulate: (payload) => api.post('/investments/exit-simulate', payload),
};

export const aiApi = {
  roi: (payload) => api.post('/ai/roi', payload),
  risk: (payload) => api.post('/ai/risk', payload),
  explain: (payload) => api.post('/ai/explain', payload),
};

export const dashboardApi = {
  investor: () => api.get('/dashboard/investor'),
  owner: () => api.get('/dashboard/owner'),
  admin: () => api.get('/dashboard/admin'),
};

export const adminApi = {
  pendingProperties: () => api.get('/admin/properties/pending'),
  propertyDocuments: (propertyId) => api.get(`/admin/properties/${propertyId}/documents`),
  pendingDocuments: () => api.get('/admin/documents/pending'),
  verifyDocument: (id, approve, rejectionReason = '') =>
    api.patch(`/admin/documents/${id}/verify`, { approve, rejection_reason: rejectionReason }),
  approveProperty: (id, approve, rejectionReason = '') =>
    api.patch(`/admin/properties/${id}/approve`, { approve, rejection_reason: rejectionReason }),
  listUsers: () => api.get('/admin/users'),
  toggleUserActive: (id) => api.patch(`/admin/users/${id}/toggle-active`),
};
