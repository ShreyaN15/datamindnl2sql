'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useAuth } from './AuthProvider';
import { DatabaseConnection, SchemaInfo } from '@/types/api';

export default function NL2SQLQuery() {
  const { userId } = useAuth();
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<number | null>(null);
  const [schema, setSchema] = useState<SchemaInfo | null>(null);
  const [question, setQuestion] = useState('');
  const [sql, setSql] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [error, setError] = useState('');

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

  const loadSchema = async (connectionId: number) => {
    setLoadingSchema(true);
    setError('');
    try {
      const schemaData = await api.connections.getSchema(userId!, connectionId);
      setSchema(schemaData);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoadingSchema(false);
    }
  };

  const handleConnectionChange = (connectionId: string) => {
    const id = parseInt(connectionId);
    setSelectedConnection(id);
    setSql('');
    loadSchema(id);
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!schema) return;

    setLoading(true);
    setError('');
    setSql('');

    try {
      // Convert foreign keys to API format
      const foreignKeys = schema.foreign_keys.map(([from_table, from_column, to_table, to_column]) => ({
        from_table,
        from_column,
        to_table,
        to_column,
      }));

      const response = await api.query.nl2sql({
        question,
        schema: schema.tables,
        foreign_keys: foreignKeys,
        use_sanitizer: true,
      });

      setSql(response.sql);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const exampleQueries = [
    'Show all users',
    'Get all products with their category names',
    'Find orders made by john_doe',
    'What are the top 5 most expensive products',
    'Count how many orders each user has made',
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-gray-900">Natural Language to SQL</h2>

      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Database Connection
            </label>
            <select
              value={selectedConnection || ''}
              onChange={(e) => handleConnectionChange(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">-- Select a connection --</option>
              {connections.map((conn) => (
                <option key={conn.id} value={conn.id}>
                  {conn.name} ({conn.db_type} - {conn.database_name})
                </option>
              ))}
            </select>
          </div>

          {loadingSchema && (
            <div className="text-center py-4 text-gray-600">
              Loading schema...
            </div>
          )}

          {schema && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 mb-2">Schema Loaded ✓</h3>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-blue-700">Tables:</span>{' '}
                  <span className="font-medium">{schema.table_count}</span>
                </div>
                <div>
                  <span className="text-blue-700">Columns:</span>{' '}
                  <span className="font-medium">{schema.total_columns}</span>
                </div>
                <div>
                  <span className="text-blue-700">Foreign Keys:</span>{' '}
                  <span className="font-medium">{schema.foreign_keys.length}</span>
                </div>
              </div>
              
              <details className="mt-4">
                <summary className="cursor-pointer text-blue-700 font-medium hover:text-blue-800">
                  View Schema Details
                </summary>
                <div className="mt-3 space-y-2 text-sm max-h-64 overflow-y-auto">
                  {Object.entries(schema.tables).map(([table, columns]) => (
                    <div key={table} className="bg-white p-3 rounded border border-blue-200">
                      <div className="font-semibold text-gray-900 mb-1">{table}</div>
                      <div className="text-gray-600 text-xs">
                        {columns.join(', ')}
                      </div>
                    </div>
                  ))}
                  
                  {schema.foreign_keys.length > 0 && (
                    <div className="bg-white p-3 rounded border border-blue-200">
                      <div className="font-semibold text-gray-900 mb-2">Foreign Keys:</div>
                      <div className="space-y-1 text-xs text-gray-600">
                        {schema.foreign_keys.map((fk, idx) => (
                          <div key={idx}>
                            {fk[0]}.{fk[1]} → {fk[2]}.{fk[3]}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </details>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {schema && (
            <>
              <form onSubmit={handleQuery} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ask a Question in Natural Language
                  </label>
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g., Show me all users who made orders in the last month"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 h-24 resize-none"
                    required
                  />
                </div>

                <div className="flex flex-wrap gap-2">
                  <span className="text-sm text-gray-600">Examples:</span>
                  {exampleQueries.map((example, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setQuestion(example)}
                      className="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                    >
                      {example}
                    </button>
                  ))}
                </div>

                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 font-medium transition-colors w-full"
                >
                  {loading ? 'Generating SQL...' : 'Generate SQL'}
                </button>
              </form>

              {sql && (
                <div className="bg-gray-900 text-green-400 p-4 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-semibold text-sm">Generated SQL:</span>
                    <button
                      onClick={() => navigator.clipboard.writeText(sql)}
                      className="text-xs px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600"
                    >
                      Copy
                    </button>
                  </div>
                  <pre className="overflow-x-auto text-sm font-mono">
                    {sql}
                  </pre>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
