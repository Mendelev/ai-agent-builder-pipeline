import { create } from 'zustand';
import { ProjectStatus, Requirement, Plan, PromptBundle } from '@/types';

interface ProjectStore {
  currentProjectId: string | null;
  currentProject: ProjectStatus | null;
  requirements: Requirement[];
  currentPlan: Plan | null;
  currentPrompts: PromptBundle | null;
  
  setCurrentProjectId: (projectId: string | null) => void;
  setCurrentProject: (project: ProjectStatus | null) => void;
  setRequirements: (requirements: Requirement[]) => void;
  updateRequirement: (key: string, updates: Partial<Requirement>) => void;
  setCurrentPlan: (plan: Plan | null) => void;
  setCurrentPrompts: (prompts: PromptBundle | null) => void;
  reset: () => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  currentProjectId: null,
  currentProject: null,
  requirements: [],
  currentPlan: null,
  currentPrompts: null,

  setCurrentProjectId: (projectId) =>
    set({ currentProjectId: projectId ?? null }),

  setCurrentProject: (project) =>
    set({
      currentProject: project,
      currentProjectId: project ? project.id : null,
    }),
  
  setRequirements: (requirements) => set({ requirements }),
  
  updateRequirement: (key, updates) =>
    set((state) => ({
      requirements: state.requirements.map((req) =>
        req.key === key ? { ...req, ...updates } : req
      ),
    })),
  
  setCurrentPlan: (plan) => set({ currentPlan: plan }),
  
  setCurrentPrompts: (prompts) => set({ currentPrompts: prompts }),
  
  reset: () =>
    set({
      currentProjectId: null,
      currentProject: null,
      requirements: [],
      currentPlan: null,
      currentPrompts: null,
    }),
}));
