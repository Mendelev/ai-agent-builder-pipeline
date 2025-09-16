import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home,
  FileText,
  Code,
  Calendar,
  MessageSquare,
  History,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useUIStore } from '@/store';
import clsx from 'clsx';

const menuItems = [
  { path: '/', label: 'Dashboard', icon: Home },
  { path: '/requirements', label: 'Requirements', icon: FileText },
  { path: '/code-checklist', label: 'Code & Checklist', icon: Code },
  { path: '/planning', label: 'Planning', icon: Calendar },
  { path: '/prompts', label: 'Prompts', icon: MessageSquare },
  { path: '/audit', label: 'Audit', icon: History },
];

export const Sidebar: React.FC = () => {
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <aside
      className={clsx(
        'fixed left-0 top-0 h-full bg-gray-900 text-white transition-all duration-300 z-10',
        sidebarOpen ? 'w-64' : 'w-16'
      )}
    >
      <div className="flex flex-col h-full pt-20">
        <nav className="flex-1">
          <ul className="space-y-2 px-3">
            {menuItems.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center px-3 py-2 rounded-lg transition-colors',
                      isActive
                        ? 'bg-blue-600 text-white'
                        : 'hover:bg-gray-800 text-gray-300'
                    )
                  }
                >
                  <item.icon className="h-5 w-5 flex-shrink-0" />
                  {sidebarOpen && (
                    <span className="ml-3">{item.label}</span>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <button
          onClick={toggleSidebar}
          className="p-3 border-t border-gray-800 hover:bg-gray-800"
        >
          {sidebarOpen ? (
            <ChevronLeft className="h-5 w-5 mx-auto" />
          ) : (
            <ChevronRight className="h-5 w-5 mx-auto" />
          )}
        </button>
      </div>
    </aside>
  );
};