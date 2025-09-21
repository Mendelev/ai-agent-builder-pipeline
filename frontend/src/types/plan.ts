export interface Plan {
  id: string;
  project_id: string;
  version: number;
  status: string;
  source: string;
  use_code: boolean;
  include_checklist: boolean;
  constraints: Record<string, any>;
  metadata: Record<string, any>;
  total_duration_days: number;
  risk_score: number;
  coverage_percentage: number;
  phases: PlanPhase[];
  created_at: string;
  updated_at: string;
}

export interface PlanPhase {
  id: string;
  phase_id: string;
  sequence: number;
  title: string;
  objective: string;
  deliverables: string[];
  activities: string[];
  dependencies: string[];
  estimated_days: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risks: string[];
  requirements_covered: string[];
  definition_of_done: string[];
  resources_required: Record<string, number>;
  created_at: string;
}

export interface PlanGenerateRequest {
  source: 'requirements' | 'checklist' | 'hybrid';
  use_code: boolean;
  include_checklist: boolean;
  constraints?: {
    deadline_days?: number;
    team_size?: number;
    max_parallel_phases?: number;
    nfrs?: string[];
    budget?: number;
  };
}

export interface PlanSummary {
  id: string;
  project_id: string;
  version: number;
  status: string;
  total_phases: number;
  total_duration_days: number;
  coverage_percentage: number;
  risk_score: number;
  created_at: string;
}
