export interface PromptBundle {
  id: string;
  project_id: string;
  plan_id: string;
  version: number;
  include_code: boolean;
  context_md: string;
  metadata: Record<string, any>;
  total_prompts: number;
  prompts: PromptItem[];
  created_at: string;
  updated_at: string;
}

export interface PromptItem {
  id: string;
  phase_id: string;
  sequence: number;
  title: string;
  content_md: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface PromptGenerateRequest {
  include_code: boolean;
  plan_id?: string;
}

export interface PromptBundleSummary {
  id: string;
  project_id: string;
  plan_id: string;
  version: number;
  total_prompts: number;
  include_code: boolean;
  created_at: string;
}
