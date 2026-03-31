import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001/api/v1',
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('estatex_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  console.log('[API Request]', config.method?.toUpperCase(), `${config.baseURL}${config.url}`, config.data || '');
  return config;
});

const formatApiError = (error) => {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (!item || typeof item !== 'object') return String(item || '');
        const path = Array.isArray(item.loc) ? item.loc.join('.') : '';
        const msg = item.msg || item.message || 'Invalid value';
        return path ? `${path}: ${msg}` : msg;
      })
      .filter(Boolean);
    if (parts.length > 0) return parts.join('\n');
  }
  if (typeof detail === 'string') return detail;
  return error?.message || 'Unknown API error';
};

api.interceptors.response.use(
  (response) => {
    console.log('[API Response]', response.status, response.config.url, response.data);
    return response;
  },
  (error) => {
    const message = formatApiError(error);
    console.error('[API Error]', error?.config?.url, message, error?.response?.data || '');
    return Promise.reject(new Error(message));
  }
);

export default api;
