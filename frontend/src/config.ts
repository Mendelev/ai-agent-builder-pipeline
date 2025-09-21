export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
export const SSE_URL = import.meta.env.VITE_SSE_URL || '';
export const DEFAULT_PROJECT_ID = import.meta.env.VITE_DEFAULT_PROJECT_ID || '';
export const ENABLE_DEVTOOLS = (import.meta.env.VITE_ENABLE_DEVTOOLS || 'false').toLowerCase() === 'true';
