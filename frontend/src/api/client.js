import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1',
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

api.interceptors.response.use(
  (response) => {
    console.log('[API Response]', response.status, response.config.url, response.data);
    return response;
  },
  (error) => {
    const message = error?.response?.data?.detail || error.message || 'Unknown API error';
    console.error('[API Error]', error?.config?.url, message, error?.response?.data || '');
    return Promise.reject(new Error(message));
  }
);

export default api;
