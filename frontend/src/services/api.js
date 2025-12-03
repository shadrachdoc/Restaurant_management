import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If token expired, try to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/api/v1/auth/login', credentials),
  signup: (userData) => api.post('/api/v1/auth/signup', userData),
  logout: () => api.post('/api/v1/auth/logout'),
  refreshToken: (refreshToken) => api.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
  changePassword: (data) => api.post('/api/v1/auth/change-password', data),
  getCurrentUser: () => api.get('/api/v1/users/me'),
};

// Restaurant API
export const restaurantAPI = {
  list: (params) => api.get('/api/v1/restaurants', { params }),
  get: (id) => api.get(`/api/v1/restaurants/${id}`),
  create: (data) => api.post('/api/v1/restaurants', data),
  update: (id, data) => api.put(`/api/v1/restaurants/${id}`, data),
  delete: (id) => api.delete(`/api/v1/restaurants/${id}`),
  getAnalytics: (id) => api.get(`/api/v1/restaurants/${id}/analytics`),
  updateBranding: (id, data) => api.patch(`/api/v1/restaurants/${id}/branding`, data),
  toggleStatus: (id) => api.patch(`/api/v1/restaurants/${id}/toggle-status`),
};

// Menu API
export const menuAPI = {
  list: (restaurantId, params) => api.get(`/api/v1/restaurants/${restaurantId}/menu-items`, { params }),
  get: (restaurantId, itemId) => api.get(`/api/v1/restaurants/${restaurantId}/menu-items/${itemId}`),
  create: (restaurantId, data) => api.post(`/api/v1/restaurants/${restaurantId}/menu-items`, data),
  update: (restaurantId, itemId, data) => api.put(`/api/v1/restaurants/${restaurantId}/menu-items/${itemId}`, data),
  delete: (restaurantId, itemId) => api.delete(`/api/v1/restaurants/${restaurantId}/menu-items/${itemId}`),
  toggleAvailability: (restaurantId, itemId) => api.patch(`/api/v1/restaurants/${restaurantId}/menu-items/${itemId}/toggle-availability`),
};

// Table API
export const tableAPI = {
  list: (restaurantId, params) => api.get(`/api/v1/restaurants/${restaurantId}/tables`, { params }),
  get: (restaurantId, tableId) => api.get(`/api/v1/restaurants/${restaurantId}/tables/${tableId}`),
  getById: (restaurantId, tableId) => api.get(`/api/v1/restaurants/${restaurantId}/tables/${tableId}`), // Alias for get
  create: (restaurantId, data) => api.post(`/api/v1/restaurants/${restaurantId}/tables`, data),
  update: (restaurantId, tableId, data) => api.put(`/api/v1/restaurants/${restaurantId}/tables/${tableId}`, data),
  delete: (restaurantId, tableId) => api.delete(`/api/v1/restaurants/${restaurantId}/tables/${tableId}`),
  updateStatus: (restaurantId, tableId, status) =>
    api.patch(`/api/v1/restaurants/${restaurantId}/tables/${tableId}/status`, null, { params: { new_status: status } }),
  getQRCode: (restaurantId, tableId) => api.get(`/api/v1/restaurants/${restaurantId}/tables/${tableId}/qr-code`),
  regenerateQR: (restaurantId, tableId) => api.post(`/api/v1/restaurants/${restaurantId}/tables/${tableId}/regenerate-qr`),
};

// Feedback API
export const feedbackAPI = {
  list: (restaurantId, params) => api.get(`/api/v1/restaurants/${restaurantId}/feedback`, { params }),
  get: (restaurantId, feedbackId) => api.get(`/api/v1/restaurants/${restaurantId}/feedback/${feedbackId}`),
  create: (restaurantId, data) => api.post(`/api/v1/restaurants/${restaurantId}/feedback`, data),
  delete: (restaurantId, feedbackId) => api.delete(`/api/v1/restaurants/${restaurantId}/feedback/${feedbackId}`),
  getSummary: (restaurantId, days) => api.get(`/api/v1/restaurants/${restaurantId}/feedback/stats/summary`, { params: { days } }),
};
