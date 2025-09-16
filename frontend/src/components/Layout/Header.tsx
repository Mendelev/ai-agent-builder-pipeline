import React from 'react';
import { Menu, Bell, User } from 'lucide-react';
import { useUIStore, useProjectStore } from '@/store';

export const Header: React.FC = () => {
  const { toggleSidebar } = useUIStore();
  const { currentProject } = useProjectStore();

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center">
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-md hover:bg-gray-100"
          >
            <Menu className="h-6 w-6" />
          </button>
          <h1 className="ml-4 text-xl font-semibold text-gray-800">
            Requirements Manager
          </h1>
          {currentProject && (
            <span className="ml-4 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
              {currentProject.name}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-4">
          <button className="p-2 rounded-md hover:bg-gray-100">
            <Bell className="h-5 w-5" />
          </button>
          <button className="p-2 rounded-md hover:bg-gray-100">
            <User className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
};