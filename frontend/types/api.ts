export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginResponse {
  user_id: number;
  username: string;
  email: string;
  message: string;
}

export interface DatabaseConnection {
  id: number;
  user_id: number;
  name: string;
  db_type: string;
  host?: string;
  port?: number;
  database_name: string;
  username?: string;
  is_active: boolean;
  last_tested_at?: string;
  last_test_status?: string;
  table_count?: number;
  total_columns?: number;
  schema_extracted_at?: string;
  created_at: string;
}

export interface SchemaInfo {
  connection_id: number;
  connection_name: string;
  database_name: string;
  db_type: string;
  schema_text: string;
  tables: Record<string, string[]>;
  foreign_keys: [string, string, string, string][];
  primary_keys: Record<string, string[]>;
  table_count: number;
  total_columns: number;
  schema_extracted_at?: string;
  cached: boolean;
}

export interface NL2SQLRequest {
  question: string;
  schema: Record<string, string[]>;
  foreign_keys?: Array<{
    from_table: string;
    from_column: string;
    to_table: string;
    to_column: string;
  }>;
  use_sanitizer?: boolean;
}

export interface NL2SQLResponse {
  sql: string;
  question: string;
}
