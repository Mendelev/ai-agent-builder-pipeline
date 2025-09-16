import React, { useState } from 'react';
import { Requirement } from '@/types';
import { Plus, Trash2, Save } from 'lucide-react';

interface RequirementEditorProps {
  requirement?: Requirement;
  onSave: (requirement: Requirement) => void;
  onCancel: () => void;
}

export const RequirementEditor: React.FC<RequirementEditorProps> = ({
  requirement,
  onSave,
  onCancel,
}) => {
  const [formData, setFormData] = useState<Requirement>(
    requirement || {
      key: '',
      title: '',
      description: '',
      priority: 'medium',
      acceptance_criteria: [],
      dependencies: [],
      metadata: {},
    }
  );

  const [newCriterion, setNewCriterion] = useState('');
  const [newDependency, setNewDependency] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  const addCriterion = () => {
    if (newCriterion.trim()) {
      setFormData({
        ...formData,
        acceptance_criteria: [...formData.acceptance_criteria, newCriterion],
      });
      setNewCriterion('');
    }
  };

  const removeCriterion = (index: number) => {
    setFormData({
      ...formData,
      acceptance_criteria: formData.acceptance_criteria.filter(
        (_, i) => i !== index
      ),
    });
  };

  const addDependency = () => {
    if (newDependency.trim()) {
      setFormData({
        ...formData,
        dependencies: [...formData.dependencies, newDependency],
      });
      setNewDependency('');
    }
  };

  const removeDependency = (index: number) => {
    setFormData({
      ...formData,
      dependencies: formData.dependencies.filter((_, i) => i !== index),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Key
          </label>
          <input
            type="text"
            value={formData.key}
            onChange={(e) => setFormData({ ...formData, key: e.target.value })}
            pattern="^[A-Z0-9_-]+$"
            required
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="REQ-001"
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Priority
          </label>
          <select
            value={formData.priority}
            onChange={(e) =>
              setFormData({
                ...formData,
                priority: e.target.value as Requirement['priority'],
              })
            }
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">
          Title
        </label>
        <input
          type="text"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          required
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">
          Description
        </label>
        <textarea
          value={formData.description}
          onChange={(e) =>
            setFormData({ ...formData, description: e.target.value })
          }
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Acceptance Criteria
        </label>
        <div className="space-y-2">
          {formData.acceptance_criteria.map((criterion, index) => (
            <div key={index} className="flex items-center gap-2">
              <span className="flex-1 p-2 bg-gray-50 rounded">
                {criterion}
              </span>
              <button
                type="button"
                onClick={() => removeCriterion(index)}
                className="p-2 text-red-600 hover:bg-red-50 rounded"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
          <div className="flex gap-2">
            <input
              type="text"
              value={newCriterion}
              onChange={(e) => setNewCriterion(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCriterion())}
              className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              placeholder="Add acceptance criterion"
            />
            <button
              type="button"
              onClick={addCriterion}
              className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Dependencies
        </label>
        <div className="space-y-2">
          {formData.dependencies.map((dep, index) => (
            <div key={index} className="flex items-center gap-2">
              <span className="flex-1 p-2 bg-gray-50 rounded">{dep}</span>
              <button
                type="button"
                onClick={() => removeDependency(index)}
                className="p-2 text-red-600 hover:bg-red-50 rounded"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
          <div className="flex gap-2">
            <input
              type="text"
              value={newDependency}
              onChange={(e) => setNewDependency(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addDependency())}
              className="flex-1 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              placeholder="Add dependency (e.g., REQ-001)"
            />
            <button
              type="button"
              onClick={addDependency}
              className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2"
        >
          <Save className="h-4 w-4" />
          Save Requirement
        </button>
      </div>
    </form>
  );
};