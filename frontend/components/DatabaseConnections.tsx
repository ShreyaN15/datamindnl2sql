'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useAuth } from './AuthProvider';
import { DatabaseConnection } from '@/types/api';

export default function DatabaseConnections() {
  const { userId } = useAuth();
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    db_type: 'postgresql',
    host: 'localhost',
    port: 5432,
    database_name: '',
    username: '',
    password: '',
  });

  useEffect(() => {
    if (userId) {
      loadConnections();
    }
  }, [userId]);

  const loadConnections = async () => {
    try {
      const data = await api.connections.list(userId!);
      setConnections(data.connections || []);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await api.connections.create(userId!, formData);
      setShowAddForm(false);
      setFormData({
        name: '',
        db_type: 'postgresql',
        host: 'localhost',
        port: 5432,
        database_name: '',
        username: '',
        password: '',
      });
      await loadConnections();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async (connectionId: number) => {
    try {
      const result = await api.connections.test(userId!, connectionId);
      alert(`Connection ${result.status === 'success' ? 'successful' : 'failed'}!\n${result.message}`);
      await loadConnections();
    } catch (err: any) {
      alert(`Test failed: ${err.message}`);
    }
  };

  const handleDelete = async (connectionId: number) => {
    if (!confirm('Are you sure you want to delete this connection?')) return;
    
    try {
      await api.connections.delete(userId!, connectionId);
      await loadConnections();
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-gray-200 pb-4">
        <div>
          <h2 className="text-xl font-medium text-black">Database Sources</h2>
          <p className="text-sm text-gray-500 mt-1">Configure your read-only data layer.</p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-black text-white px-4 py-2 text-sm font-medium rounded hover:bg-gray-800 transition-colors"
        >
          {showAddForm ? 'Cancel' : 'Add Source +'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 px-4 py-3 text-sm rounded-md border border-red-100 font-medium">
          {error}
        </div>
      )}

      {showAddForm && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-medium text-black mb-1">New Connection Setup</h3>
          <p className="text-sm text-gray-500 mb-6">Credentials are used securely and not stored explicitly.</p>
          
          <form onSubmit={handleCreate} className="space-y-5">
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-1">
                <label className="text-sm font-medium text-black">Connection Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full bg-white border border-gray-300 px-3 py-2 text-sm text-black placeholder:text-gray-400 focus:border-black focus:outline-none rounded-md"
                  placeholder="Analytics Warehouse"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="text-sm font-medium text-black">Database Engine</label>
                <select
                  value={formData.db_type}
                  onChange={(e) => setFormData({ ...formData, db_type: e.target.value })}
                  className="w-full bg-white border border-gray-300 px-3 py-2 text-sm text-black focus:border-black focus:outline-none rounded-md"
                >
                  <option value="postgresql">PostgreSQL</option>
                  <option value="mysql">MySQL</option>
                  <option value="sqlite">SQLite</option>
                  <option value="mssql">MS SQL Server</option>
                  <option value="oracle">Oracle</option>
                </select>
              </div>

              {formData.db_type !== 'sqlite' && (
                <>
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-black">Host</label>
                    <input
                      type="text"
                      value={formData.host}
                      onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                      className="w-full bg-white border border-gray-300 px-3 py-2 text-sm text-black placeholder:text-gray-400 focus:border-black focus:outline-none rounded-md"
                      placeholder="db.internal"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-medium text-black">Port</label>
                    <input
                      type="number"
                      value={formData.port}
                      onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) })}
                      className="w-full bg-white border border-gray-300 px-3 py-2 text-sm text-black focus:border-black focus:outline-none rounded-md"
                    />
                  </div>
                </>
              )}

              <div className="space-y-1">
                <label className="text-sm font-medium text-black">Database Name</label>
                <input
                  type="text"
                  value={formData.database_name}
                  onChange={(e) => setFormData({ ...formData, database_name: e.target.value })}
                  className="w-full bg-white border border-gray-300 px-3 py-2 text-sm text-black placeholder:text-gray-400 focus:border-black focus:outline-none rounded-md"
                  placeholder="analytics"
                  required
                />
              </div>

              {formData.db_type !== 'sqlite' && (
                <>
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-black">Read-Only Username</label>
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      className="w-full bg-white border border-gray-300 px-3 py-2 text-sm text-black placeholder:text-gray-400 focus:border-black focus:outline-none rounded-md"
                      placeholder="readonly_user"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-medium text-black">Password</label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full bg-white border border-gray-300 px-3 py-2 text-sm text-black placeholder:text-gray-400 focus:border-black focus:outline-none rounded-md"
                      placeholder="••••••••"
                    />
                  </div>
                </>
              )}
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="bg-black text-white px-5 py-2.5 text-sm font-medium rounded hover:bg-gray-900 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Creating...' : 'Finalize Connection'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {connections.map((conn) => (
          <div
            key={conn.id}
            className="group flex flex-col border border-gray-200 bg-white hover:border-black transition-colors rounded-lg overflow-hidden"
          >
            <div className="p-5 flex-1">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-medium text-black">{conn.name}</h3>
                <span className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded font-mono uppercase">
                  {conn.db_type}
                </span>
              </div>
              
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>Database</span>
                  <span className="font-medium text-black">{conn.database_name}</span>
                </div>
                {conn.table_count !== undefined && (
                  <div className="flex justify-between">
                    <span>Schema</span>
                    <span className="font-medium text-black">{conn.table_count} tables</span>
                  </div>
                )}
                {conn.last_test_status && (
                  <div className="flex justify-between items-center pt-2 mt-2 border-t border-gray-100">
                    <span>Status</span>
                    <span className={`text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-full ${
                      conn.last_test_status === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {conn.last_test_status}
                    </span>
                  </div>
                )}
              </div>
            </div>

            <div className="border-t border-gray-200 bg-gray-50 flex divide-x divide-gray-200">
              <button
                onClick={() => handleTest(conn.id)}
                className="flex-1 py-2.5 text-xs font-semibold text-gray-600 hover:text-black hover:bg-gray-100 transition-colors"
              >
                TEST
              </button>
              <button
                onClick={() => handleDelete(conn.id)}
                className="flex-1 py-2.5 text-xs font-semibold text-red-600 hover:bg-red-50 transition-colors"
              >
                DELETE
              </button>
            </div>
          </div>
        ))}

        {connections.length === 0 && !showAddForm && (
          <div className="col-span-full py-16 text-center border border-dashed border-gray-300 rounded-lg bg-gray-50/50">
            <h3 className="text-lg font-medium text-black">No Connections Yet</h3>
            <p className="mt-1 text-sm text-gray-500 max-w-sm mx-auto mb-4">
              Connect a database to start analyzing your data and asking natural language queries.
            </p>
            <button
              onClick={() => setShowAddForm(true)}
              className="mt-2 text-sm font-medium text-black bg-white border border-gray-200 shadow-sm px-4 py-2 hover:bg-gray-50 rounded"
            >
              Add Connection
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
