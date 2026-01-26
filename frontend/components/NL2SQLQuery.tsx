'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useAuth } from './AuthProvider';
import { DatabaseConnection, SchemaInfo, QueryExecutionResult } from '@/types/api';

export default function NL2SQLQuery() {
  const { userId } = useAuth();
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<number | null>(null);
  const [schema, setSchema] = useState<SchemaInfo | null>(null);
  const [question, setQuestion] = useState('');
  const [sql, setSql] = useState('');
  const [executionResult, setExecutionResult] = useState<QueryExecutionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [error, setError] = useState('');
  const [executeQuery, setExecuteQuery] = useState(true);

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
    setExecutionResult(null);
    loadSchema(id);
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!schema) return;

    setLoading(true);
    setError('');
    setSql('');
    setExecutionResult(null);

    try {
      // Convert foreign keys to API format
      const foreignKeys = schema.foreign_keys.map(([from_table, from_column, to_table, to_column]) => ({
        from_table,
        from_column,
        to_table,
        to_column,
      }));

      const response = await api.query.nl2sql(userId!, {
        question,
        schema: schema.tables,
        foreign_keys: foreignKeys,
        use_sanitizer: true,
        execute_query: executeQuery,
        database_id: selectedConnection || undefined,
      });

      setSql(response.sql);
      if (response.execution_result) {
        setExecutionResult(response.execution_result);
      }
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

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="executeQuery"
                    checked={executeQuery}
                    onChange={(e) => setExecuteQuery(e.target.checked)}
                    className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
                  />
                  <label htmlFor="executeQuery" className="text-sm text-gray-700">
                    Execute query and show results
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 font-medium transition-colors w-full"
                >
                  {loading ? 'Generating SQL...' : executeQuery ? 'Generate & Execute SQL' : 'Generate SQL'}
                </button>
              </form>

              {sql && (
                <div className="space-y-4">
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

                  {executionResult && (
                    <div className="space-y-4">
                      {executionResult.success ? (
                        <>
                          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                            <div className="flex items-center gap-2 text-green-800 mb-2">
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                              </svg>
                              <span className="font-semibold">Query Executed Successfully</span>
                            </div>
                            <div className="text-sm text-green-700">
                              Returned {executionResult.row_count} row(s)
                              {executionResult.has_more && ' (limited to 1000)'}
                            </div>
                          </div>

                          {executionResult.data.length > 0 && (
                            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                              <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                                <h4 className="font-semibold text-gray-900">Query Results</h4>
                              </div>
                              <div className="overflow-x-auto max-h-96">
                                <table className="w-full text-sm">
                                  <thead className="bg-gray-100 sticky top-0">
                                    <tr>
                                      {executionResult.columns.map((col) => (
                                        <th key={col} className="px-4 py-2 text-left font-semibold text-gray-700 border-b">
                                          {col}
                                        </th>
                                      ))}
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {executionResult.data.map((row, idx) => (
                                      <tr key={idx} className="hover:bg-gray-50 border-b">
                                        {executionResult.columns.map((col) => (
                                          <td key={col} className="px-4 py-2 text-gray-900">
                                            {row[col] !== null && row[col] !== undefined ? String(row[col]) : '—'}
                                          </td>
                                        ))}
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          )}

                          {executionResult.is_visualizable && executionResult.data.length > 0 && (
                            <div className="bg-white border border-gray-200 rounded-lg p-4">
                              <h4 className="font-semibold text-gray-900 mb-4">Data Visualization</h4>
                              <div className="bg-gradient-to-br from-indigo-50 to-blue-50 rounded-lg p-8">
                                {executionResult.suggested_chart === 'bar' && (
                                  <div className="space-y-2">
                                    {executionResult.data.slice(0, 10).map((row, idx) => {
                                      const label = row[executionResult.columns[0]];
                                      const value = row[executionResult.columns[1]];
                                      const maxValue = Math.max(...executionResult.data.map(r => Number(r[executionResult.columns[1]]) || 0));
                                      const percentage = maxValue > 0 ? (Number(value) / maxValue) * 100 : 0;
                                      
                                      return (
                                        <div key={idx} className="flex items-center gap-2">
                                          <div className="w-32 text-sm text-gray-700 truncate" title={String(label)}>
                                            {String(label)}
                                          </div>
                                          <div className="flex-1 bg-gray-200 rounded-full h-6 relative">
                                            <div 
                                              className="bg-indigo-600 h-full rounded-full flex items-center justify-end pr-2"
                                              style={{ width: `${percentage}%` }}
                                            >
                                              <span className="text-xs text-white font-medium">{String(value)}</span>
                                            </div>
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                )}
                                
                                {executionResult.suggested_chart === 'line' && (
                                  <div className="text-center text-gray-600">
                                    <svg className="w-16 h-16 mx-auto mb-2 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                                    </svg>
                                    <p>Line chart visualization (Advanced charts coming soon)</p>
                                  </div>
                                )}
                                
                                {!['bar', 'line'].includes(executionResult.suggested_chart || '') && (
                                  <div className="text-center text-gray-600">
                                    <svg className="w-16 h-16 mx-auto mb-2 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
                                    </svg>
                                    <p>Data visualization (Chart type: {executionResult.suggested_chart})</p>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </>
                      ) : (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                          <div className="flex items-center gap-2 text-red-800 mb-2">
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                            <span className="font-semibold">Query Execution Failed</span>
                          </div>
                          <div className="text-sm text-red-700 font-mono bg-red-100 p-2 rounded mt-2">
                            {executionResult.error}
                          </div>
                          <div className="text-sm text-red-600 mt-2">
                            The SQL was generated but couldn't be executed. This might be due to syntax errors or data issues.
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
