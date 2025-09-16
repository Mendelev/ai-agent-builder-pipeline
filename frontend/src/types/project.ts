export enum ProjectState {
  DRAFT = 'DRAFT',
  REQS_REFINING = 'REQS_REFINING',
  REQS_READY = 'REQS_READY',
  CODE_VALIDATED = 'CODE_VALIDATED',
  PLAN_READY = 'PLAN_READY',
  PROMPTS_READY = 'PROMPTS_READY',
  DONE = 'DONE',
  BLOCKED = 'BLOCKED',
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  status: ProjectState;
  context?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectStatus {
  id: string;
  name: string;
  state: ProjectState;
  created_at: string;
  updated_at: string;
  recent_events: Event[];
  metadata: Record<string, any>;
}

export interface Event {
  type: string;
  action: string;
  success: boolean;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  project_id: string;
  correlation_id?: string;
  event_type: string;
  agent_type?: string;
  action: string;
  details: Record<string, any>;
  user_id?: string;
  duration_ms?: number;
  success: boolean;
  error_message?: string;
  created_at: string;
}