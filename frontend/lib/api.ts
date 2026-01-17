const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export const api = {
  // Auth endpoints
  auth: {
    register: async (
      username: string,
      email: string,
      password: string,
      fullName?: string
    ) => {
      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          email,
          password,
          full_name: fullName,
        }),
      });
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },

    login: async (username: string, password: string) => {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },

    getUser: async (userId: number) => {
      const response = await fetch(`${API_URL}/auth/users/${userId}`);
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },
  },

  // Database connection endpoints
  connections: {
    list: async (userId: number) => {
      const response = await fetch(
        `${API_URL}/db/connections?user_id=${userId}`
      );
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },

    create: async (userId: number, data: any) => {
      const response = await fetch(
        `${API_URL}/db/connections?user_id=${userId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data),
        }
      );
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },

    get: async (userId: number, connectionId: number) => {
      const response = await fetch(
        `${API_URL}/db/connections/${connectionId}?user_id=${userId}`
      );
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },

    delete: async (userId: number, connectionId: number) => {
      const response = await fetch(
        `${API_URL}/db/connections/${connectionId}?user_id=${userId}`,
        {
          method: "DELETE",
        }
      );
      if (!response.ok) throw new Error(await response.text());
      return response.status === 204;
    },

    test: async (userId: number, connectionId: number) => {
      const response = await fetch(
        `${API_URL}/db/connections/${connectionId}/test?user_id=${userId}`,
        {
          method: "POST",
        }
      );
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },

    getSchema: async (
      userId: number,
      connectionId: number,
      useCached: boolean = true
    ) => {
      const response = await fetch(
        `${API_URL}/db/connections/${connectionId}/schema?user_id=${userId}&use_cached=${useCached}`
      );
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },

    refreshSchema: async (userId: number, connectionId: number) => {
      const response = await fetch(
        `${API_URL}/db/connections/${connectionId}/refresh-schema?user_id=${userId}`,
        { method: "POST" }
      );
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },
  },

  // NL2SQL endpoint
  query: {
    nl2sql: async (data: any) => {
      const response = await fetch(`${API_URL}/query/nl2sql`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    },
  },
};
