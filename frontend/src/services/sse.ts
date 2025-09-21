export class SSEClient {
  private eventSource: EventSource | null = null;
  private url: string;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  constructor(url: string) {
    this.url = url;
  }

  connect(projectId: string): void {
    if (this.eventSource) {
      this.disconnect();
    }

    if (!this.url) {
      console.warn('SSE URL not configured; skipping connection');
      return;
    }

    const sseUrl = `${this.url}/projects/${projectId}/events`;
    this.eventSource = new EventSource(sseUrl);

    this.eventSource.onopen = () => {
      console.log('SSE connection established');
    };

    this.eventSource.onerror = (error) => {
      console.error('SSE error:', error);
    };

    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.notifyListeners(data.type, data);
      } catch (error) {
        console.error('Failed to parse SSE message:', error);
      }
    };
  }

  disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  on(eventType: string, callback: (data: any) => void): void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType)!.add(callback);
  }

  off(eventType: string, callback: (data: any) => void): void {
    this.listeners.get(eventType)?.delete(callback);
  }

  private notifyListeners(eventType: string, data: any): void {
    this.listeners.get(eventType)?.forEach(callback => callback(data));
    this.listeners.get('*')?.forEach(callback => callback(data));
  }
}

export const sseClient = new SSEClient(
  import.meta.env.VITE_SSE_URL || 'http://localhost:8000/sse'
);
