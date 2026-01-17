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
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Database Connections</h2>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
        >
          {showAddForm ? 'Cancel' : '+ Add Connection'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {showAddForm && (
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Add New Connection</h3>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Connection Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Database Type
                </label>
                <select
                  value={formData.db_type}
                  onChange={(e) => setFormData({ ...formData, db_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
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
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Host
                    </label>
                    <input
                      type="text"
                      value={formData.host}
                      onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Port
                    </label>
                    <input
                      type="number"
                      value={formData.port}
                      onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Database Name
                </label>
                <input
                  type="text"
                  value={formData.database_name}
                  onChange={(e) => setFormData({ ...formData, database_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              {formData.db_type !== 'sqlite' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Username
                    </label>
                    <input
                      type="text"
                      value={formData.username}
                      onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Password
                    </label>
                    <input
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 transition-colors"
            >
              {loading ? 'Creating...' : 'Create Connection'}
            </button>
          </form>
        </div>
      )}

      <div className="grid gap-4">
        {connections.map((conn) => (
          <div
            key={conn.id}
            className="bg-white p-6 rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow"
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">{conn.name}</h3>
                <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">Type:</span>{' '}
                    <span className="font-medium uppercase">{conn.db_type}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Database:</span>{' '}
                    <span className="font-medium">{conn.database_name}</span>
                  </div>
                  {conn.table_count !== undefined && (
                    <>
                      <div>
                        <span className="text-gray-600">Tables:</span>{' '}
                        <span className="font-medium">{conn.table_count}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Columns:</span>{' '}
                        <span className="font-medium">{conn.total_columns}</span>
                      </div>
                    </>
                  )}
                  {conn.last_test_status && (
                    <div className="col-span-2">
                      <span className="text-gray-600">Status:</span>{' '}
                      <span
                        className={`font-medium ${
                          conn.last_test_status === 'success'
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        {conn.last_test_status}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-2 ml-4">
                <button
                  onClick={() => handleTest(conn.id)}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm font-medium transition-colors"
                >
                  Test
                </button>
                <button
                  onClick={() => handleDelete(conn.id)}
                  className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm font-medium transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}

        {connections.length === 0 && !showAddForm && (
          <div className="text-center py-12 text-gray-500">
            <p>No database connections yet. Click &quot;Add Connection&quot; to get started!</p>
          </div>
        )}
      </div>
    </div>
  );
}
