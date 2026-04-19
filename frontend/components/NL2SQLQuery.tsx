'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useAuth } from './AuthProvider';
import { DatabaseConnection, SchemaInfo, QueryExecutionResult } from '@/types/api';
import dynamic from 'next/dynamic';

// Dynamically import DataVisualization to avoid SSR issues with Chart.js
const DataVisualization = dynamic(() => import('./DataVisualization'), {
  ssr: false,
  loading: () => <div className="text-center py-8 text-gray-500">Loading chart...</div>,
});

interface VisualizationResult {
  is_visualizable: boolean;
  reason: string;
  recommended_chart: string;
  chart_config: any;
  data: any;
}

export default function NL2SQLQuery() {
  const { userId } = useAuth();
  const [connections, setConnections] = useState<DatabaseConnection[]>([]);
  const [selectedConnection, setSelectedConnection] = useState<number | null>(null);
  const [schema, setSchema] = useState<SchemaInfo | null>(null);
  const [question, setQuestion] = useState('');
  const [sql, setSql] = useState('');
  const [modelSuggestions, setModelSuggestions] = useState<string[]>([]);
  const [executionResult, setExecutionResult] = useState<QueryExecutionResult | null>(null);
  const [visualization, setVisualization] = useState<VisualizationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingSchema, setLoadingSchema] = useState(false);
  const [loadingVisualization, setLoadingVisualization] = useState(false);
  const [executingSuggestionIdx, setExecutingSuggestionIdx] = useState<number | null>(null);
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
    setModelSuggestions([]);
    setExecutionResult(null);
    loadSchema(id);
  };

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!schema) return;

    setLoading(true);
    setError('');
    setSql('');
    setModelSuggestions([]);
    setExecutionResult(null);
    setVisualization(null);

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
      setModelSuggestions((response.model_suggestions || []).slice(0, 3));
      if (response.execution_result) {
        setExecutionResult(response.execution_result);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVisualize = async () => {
    if (!executionResult || !executionResult.success || !executionResult.data.length) {
      return;
    }

    setLoadingVisualization(true);
    setError('');
    setVisualization(null);

    try {
      // Prepare column info
      const columnInfo = executionResult.columns.map((colName) => {
        // Try to infer type from first row of data
        const sampleValue = executionResult.data[0]?.[colName];
        let type = 'varchar';
        
        if (typeof sampleValue === 'number') {
          type = Number.isInteger(sampleValue) ? 'integer' : 'float';
        } else if (sampleValue instanceof Date) {
          type = 'datetime';
        }
        
        return { name: colName, type };
      });

      const vizResult = await api.query.visualize({
        query_result: executionResult.data,
        column_info: columnInfo,
        sql_query: sql,
      });

      setVisualization(vizResult);
    } catch (err: any) {
      setError(`Visualization error: ${err.message}`);
    } finally {
      setLoadingVisualization(false);
    }
  };

  const handleExecuteSuggestion = async (candidateSql: string, idx: number) => {
    if (!selectedConnection) {
      setError('Please select a database connection first.');
      return;
    }

    setExecutingSuggestionIdx(idx);
    setError('');
    setVisualization(null);

    try {
      const result = await api.query.executeSql(userId!, {
        sql: candidateSql,
        database_id: selectedConnection,
      });
      setSql(candidateSql);
      setExecutionResult(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setExecutingSuggestionIdx(null);
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
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-medium tracking-tight text-black">
            NL2SQL Studio
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Ask questions in natural language, inspect the generated SQL and safely execute against your schema.
          </p>
        </div>
        {schema && (
          <span className="inline-flex items-center gap-2 rounded bg-gray-100 border border-gray-200 px-3 py-1 text-xs font-medium text-black">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
            Schema loaded
            <span className="text-gray-500 font-normal">
              ({schema.table_count} tables · {schema.total_columns} columns)
            </span>
          </span>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-5 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div>
            <label className="mb-2 block text-sm font-medium text-black">
              Select database connection
            </label>
            <select
              value={selectedConnection || ''}
              onChange={(e) => handleConnectionChange(e.target.value)}
              className="w-full rounded border border-gray-300 bg-white px-3 py-2.5 text-sm text-black focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
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
            <div className="rounded border border-gray-200 bg-gray-50 px-3 py-2 text-center text-sm text-gray-600">
              Loading schema...
            </div>
          )}

          {schema && (
            <div className="rounded border border-gray-200 bg-gray-50 p-4">
              <h3 className="mb-2 text-sm font-semibold text-black">
                Schema overview
              </h3>
              <div className="grid grid-cols-3 gap-3 text-sm text-gray-600">
                <div>
                  <span className="text-gray-500">Tables:</span>{' '}
                  <span className="font-semibold text-black">
                    {schema.table_count}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Columns:</span>{' '}
                  <span className="font-semibold text-black">
                    {schema.total_columns}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Foreign keys:</span>{' '}
                  <span className="font-semibold text-black">
                    {schema.foreign_keys.length}
                  </span>
                </div>
              </div>

              <details className="mt-3">
                <summary className="cursor-pointer text-sm font-medium text-gray-700 hover:text-black">
                  View schema details
                </summary>
                <div className="mt-3 max-h-64 space-y-2 overflow-y-auto text-sm">
                  {Object.entries(schema.tables).map(([table, columns]) => (
                    <div
                      key={table}
                      className="rounded border border-gray-200 bg-white p-2.5"
                    >
                      <div className="mb-1 text-sm font-semibold text-black">
                        {table}
                      </div>
                      <div className="text-xs text-gray-600 font-mono">
                        {columns.join(', ')}
                      </div>
                    </div>
                  ))}

                  {schema.foreign_keys.length > 0 && (
                    <div className="rounded border border-gray-200 bg-white p-2.5">
                      <div className="mb-1 text-sm font-semibold text-black">
                        Foreign keys
                      </div>
                      <div className="space-y-1 text-xs text-gray-600 font-mono">
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
            <div className="rounded border border-yellow-300 bg-yellow-50 px-3 py-2.5 text-sm text-yellow-800 font-medium flex items-center gap-2">
              <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              {error}
            </div>
          )}

          {schema && (
            <>
              <form onSubmit={handleQuery} className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-black">
                    Ask a question in natural language
                  </label>
                  <textarea
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="e.g., Show me all users who made orders in the last 30 days with their total spend"
                    className="h-28 w-full resize-none rounded border border-gray-300 bg-white px-3 py-2.5 text-sm text-black placeholder:text-gray-400 focus:border-black focus:outline-none focus:ring-1 focus:ring-black"
                    required
                  />
                </div>

                <div className="flex items-center justify-between gap-2 pt-2">
                  <label className="inline-flex cursor-pointer items-center gap-2 text-xs text-gray-700">
                    <input
                      type="checkbox"
                      id="executeQuery"
                      checked={executeQuery}
                      onChange={(e) => setExecuteQuery(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 bg-white text-black focus:ring-black"
                    />
                    <span className="font-medium">Execute query and show results</span>
                  </label>
                  <button
                    type="submit"
                    disabled={loading || !question.trim()}
                    className="inline-flex items-center justify-center gap-2 rounded bg-black px-4 py-2 text-sm font-medium text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-300"
                  >
                    {loading ? 'Generating SQL…' : executeQuery ? 'Generate & execute SQL' : 'Generate SQL only'}
                  </button>
                </div>
              </form>
            </>
          )}
        </div>

        <div className="flex flex-col space-y-4 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          {!sql ? (
            <div className="flex flex-1 items-center justify-center text-sm text-gray-400">
              Generated SQL and results will appear here
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded border border-gray-200 bg-gray-50 px-4 py-3">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 text-sm font-semibold text-black">
                    <span className="h-1.5 w-1.5 rounded-full bg-black" />
                    Generated SQL
                  </div>
                  <button
                    onClick={() => navigator.clipboard.writeText(sql)}
                    className="rounded bg-white border border-gray-200 px-3 py-1 text-xs font-medium text-gray-700 transition hover:bg-gray-100"
                  >
                    Copy
                  </button>
                </div>
                <pre className="max-h-52 overflow-auto whitespace-pre-wrap leading-relaxed rounded-md bg-black p-5 text-sm font-mono text-white shadow-inner">
                  {sql}
                </pre>
              </div>

              {modelSuggestions.length > 0 && (
                <div className="rounded border border-gray-200 bg-gray-50 p-4">
                  <div className="mb-3 flex items-center justify-between gap-2">
                    <h4 className="text-sm font-semibold text-black">
                      Model alternatives
                    </h4>
                  </div>
                  <div className="space-y-3">
                    {modelSuggestions.map((candidate, idx) => (
                      <div
                        key={idx}
                        className="rounded border border-gray-200 bg-white p-4 shadow-sm"
                      >
                        <div className="mb-2 flex items-center justify-between gap-2">
                          <div className="text-xs font-medium text-gray-600">
                            Suggestion {idx + 1}
                          </div>
                          <button
                            onClick={() => handleExecuteSuggestion(candidate, idx)}
                            disabled={executingSuggestionIdx !== null}
                            className="inline-flex items-center gap-1 rounded bg-black px-3 py-1.5 text-xs font-medium text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:bg-gray-300"
                          >
                            {executingSuggestionIdx === idx ? 'Executing…' : 'Execute variant'}
                          </button>
                        </div>
                        <pre className="overflow-x-auto whitespace-pre-wrap text-xs font-mono text-gray-800 bg-gray-50 p-2 rounded">
                          {candidate}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}
        </div>
      </div>

      {/* Execution Results (Full Width) */}
      {executionResult && (
        <div className="space-y-6 pt-2">
          {executionResult.success ? (
            <>
              {visualization && (
                visualization.is_visualizable && visualization.data ? (
                  <DataVisualization
                    chartType={visualization.recommended_chart}
                    data={visualization.data}
                    config={visualization.chart_config || {}}
                  />
                ) : (
                  <div className="rounded border border-yellow-300 bg-yellow-50 p-4">
                    <div className="flex items-start gap-3">
                      <svg
                        className="mt-0.5 h-4 w-4 text-yellow-600"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <div>
                        <h4 className="text-sm font-medium text-yellow-900">
                          Cannot visualize this result
                        </h4>
                        <p className="mt-1 text-xs text-yellow-800">
                          {visualization.reason}
                        </p>
                        <p className="mt-2 text-xs text-yellow-700">
                          Tip: queries with aggregations (COUNT, AVG, SUM) and GROUP BY are
                          usually visualizable.
                        </p>
                      </div>
                    </div>
                  </div>
                )
              )}

              {executionResult.data.length === 0 && (
                <div className="rounded border border-gray-200 bg-gray-50 p-4 text-center text-sm text-gray-500">
                  Query executed successfully. No rows returned.
                </div>
              )}

              {executionResult.data.length > 0 && (
                <div className="rounded border border-gray-200 bg-white overflow-hidden shadow-sm">
                  <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-5 py-4">
                    <div className="flex items-center gap-4">
                      <h4 className="text-base font-semibold text-black">
                        Query results
                      </h4>
                      <span className="rounded-full bg-gray-200 px-3 py-1 text-xs font-medium text-black">
                        {executionResult.row_count} row(s) {executionResult.has_more && '(limited)'}
                      </span>
                    </div>
                    <button
                      onClick={handleVisualize}
                      disabled={loadingVisualization || !executionResult.data.length}
                      className="inline-flex items-center gap-1.5 rounded bg-white border border-gray-300 px-4 py-2 text-sm font-medium text-black transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400"
                    >
                      {loadingVisualization ? (
                        <>
                          <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Analyzing…
                        </>
                      ) : (
                        <>
                          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                          Visualize data
                        </>
                      )}
                    </button>
                  </div>
                  <div className="max-h-[500px] overflow-auto">
                    <table className="w-full text-sm">
                      <thead className="sticky top-0 bg-white border-b border-gray-200">
                        <tr>
                          {executionResult.columns.map((col) => (
                            <th
                              key={col}
                              className="px-5 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 whitespace-nowrap"
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100 border-t border-gray-100">
                        {executionResult.data.map((row, idx) => (
                          <tr
                            key={idx}
                            className="hover:bg-gray-50 transition-colors"
                          >
                            {executionResult.columns.map((col) => (
                              <td key={col} className="px-5 py-3 text-black whitespace-nowrap">
                                {row[col] !== null && row[col] !== undefined
                                  ? String(row[col])
                                  : <span className="text-gray-400">—</span>}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="rounded border border-yellow-300 bg-yellow-50 p-6">
              <div className="mb-3 flex items-center gap-2 text-base text-yellow-900">
                <svg className="h-5 w-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
                </svg>
                <span className="font-semibold">Oops! We encountered a hiccup.</span>
              </div>
              <p className="text-sm text-yellow-800 mb-4">
                The generated SQL couldn't be executed due to a syntax issue or data mismatch.
              </p>
              <details className="mt-2 group">
                <summary className="text-sm cursor-pointer font-medium text-yellow-800 hover:text-yellow-900 list-inside">
                  Developer details
                </summary>
                <div className="mt-3 rounded bg-white border border-yellow-200 p-4 text-xs font-mono text-gray-700 overflow-auto whitespace-pre-wrap max-h-40 leading-relaxed shadow-sm">
                  {executionResult.error}
                </div>
              </details>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
