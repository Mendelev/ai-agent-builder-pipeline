export * from './project';
export * from './requirement';
export * from './plan';
export * from './prompt';

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ErrorResponse {
  detail: string;
  status?: number;
}