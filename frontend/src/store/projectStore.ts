import { create } from 'zustand';
import { Project, Requirement, Plan, PromptBundle } from '@/types';

interface ProjectStore {
  currentProject: Project | null;
  requirements: Requirement[];
  currentPlan: Plan | null;
  currentPrompts: PromptBundle | null;
  
  setCurrentProject: (project: Project | null) => void;
  setRequirements: (requirements: Requirement[]) => void;
  updateRequirement: (key: string, updates: Partial<Requirement>) => void;
  setCurrentPlan: (plan: Plan | null) => void;
  setCurrentPrompts: (prompts: PromptBundle | null) => void;
  reset: () => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  currentProject: null,
  requirements: [],
  currentPlan: null,
  currentPrompts: null,

  setCurrentProject: (project) => set({ currentProject: project }),
  
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
      currentProject: null,
      requirements: [],
      currentPlan: null,
      currentPrompts: null,
    }),
}));