import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { v4 as uuidv4 } from 'uuid';
import toast from 'react-hot-toast';

import { API_URL } from '@/config';

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const SKIP_ERROR_TOAST_HEADER = 'X-Skip-Error-Toast';

// Request interceptor for correlation ID
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add correlation ID
    if (!config.headers['X-Correlation-ID']) {
      config.headers['X-Correlation-ID'] = uuidv4();
    }
    
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail: string }>) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    const skipToast = error.config?.headers?.[SKIP_ERROR_TOAST_HEADER] === 'true';

    if (!skipToast) {
      toast.error(message);
    }

    // Log error with correlation ID
    console.error('API Error:', {
      correlationId: error.config?.headers?.['X-Correlation-ID'],
      status: error.response?.status,
      message,
    });
    
    return Promise.reject(error);
  }
);

export default apiClient;
