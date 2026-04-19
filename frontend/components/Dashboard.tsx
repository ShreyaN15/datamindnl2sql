'use client';

import { useState } from 'react';
import { useAuth } from './AuthProvider';
import DatabaseConnections from './DatabaseConnections';
import NL2SQLQuery from './NL2SQLQuery';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'connections' | 'query'>('connections');

  return (
    <div className="min-h-screen bg-white text-black selection:bg-black selection:text-white">
      <nav className="border-b border-gray-200">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center bg-black text-white rounded">
              <span className="text-xs font-bold tracking-tighter">DM</span>
            </div>
            <div className="leading-tight">
              <p className="text-sm font-semibold tracking-tight">DataMind</p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="hidden text-right text-sm sm:block">
              <p className="font-medium text-black truncate max-w-[160px]">
                {user?.username}
              </p>
              <p className="text-gray-500 truncate max-w-[200px] text-xs">
                {user?.email}
              </p>
            </div>
            <button
              onClick={logout}
              className="text-sm font-medium text-gray-500 hover:text-black transition-colors"
            >
              Log out
            </button>
          </div>
        </div>
      </nav>

      <main className="mx-auto max-w-7xl px-6 pb-12 pt-10 lg:px-8">
        <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-4xl font-medium tracking-tight text-black">Workspace</h1>
            <p className="mt-2 text-gray-500 text-lg">
              Manage your database connections or query with natural language.
            </p>
          </div>
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('connections')}
              className={`pb-2 text-sm font-medium transition-colors border-b-2 ${
                activeTab === 'connections'
                  ? 'border-black text-black'
                  : 'border-transparent text-gray-500 hover:text-black hover:border-gray-300'
              }`}
            >
              Connections
            </button>
            <button
              onClick={() => setActiveTab('query')}
              className={`pb-2 text-sm font-medium transition-colors border-b-2 ${
                activeTab === 'query'
                  ? 'border-black text-black'
                  : 'border-transparent text-gray-500 hover:text-black hover:border-gray-300'
              }`}
            >
              Studio
            </button>
          </div>
        </div>

        <div className="animate-in fade-in slide-in-from-bottom-2 duration-500 ease-in-out">
          {activeTab === 'connections' && (
            <DatabaseConnections />
          )}
          {activeTab === 'query' && (
            <NL2SQLQuery />
          )}
        </div>
      </main>
    </div>
  );
}
