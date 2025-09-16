export interface Requirement {
  id?: string;
  project_id?: string;
  key: string;
  title: string;
  description?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  acceptance_criteria: string[];
  dependencies: string[];
  metadata?: Record<string, any>;
  is_coherent?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface RequirementQuestion {
  id: string;
  requirement_id: string;
  question: string;
  answer?: string;
  is_resolved: boolean;
  created_at: string;
  answered_at?: string;
}

export interface RequirementBulkCreate {
  requirements: Requirement[];
}