# DataMind NL2SQL Frontend

Next.js frontend application for the DataMind Natural Language to SQL system.

## Features

- **Authentication**: Secure login and registration
- **Database Connections**: Add, test, and manage database connections
- **Schema Inference**: Automatically extract table schemas, columns, and foreign key relationships
- **NL2SQL Queries**: Convert natural language questions to SQL queries using the T5 model
- **Real-time Results**: View generated SQL and execution results

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Environment Configuration

The `.env.local` file is already configured:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Build for Production

```bash
npm run build
npm start
```

## Usage Guide

### 1. Authentication

- **Register**: Create a new account with email and password
- **Login**: Sign in with your credentials
- Tokens are stored in localStorage for persistent sessions

### 2. Database Connections

**Add a Database:**

- Click "Add Database" button
- Fill in connection details:
  - Name (e.g., "Production DB")
  - Type (postgresql, mysql, sqlite)
  - Host, Port, Database name
  - Username & Password

**View Schema:**

- After connection, schema is automatically extracted
- View:
  - Number of tables
  - Total columns
  - Foreign key relationships
  - Last schema refresh timestamp

**Test Connection:**

- Click "Test" to verify connection is active
- Green checkmark indicates successful connection

**Refresh Schema:**

- Click "Refresh" to re-extract schema from database
- Useful when database structure changes

### 3. NL2SQL Queries

**Select Database:**

- Choose from your connected databases

**View Schema Details:**

- Expand "Database Schema" section to see:
  - All tables and their columns with types
  - Foreign key relationships (e.g., orders.user_id → users.id)

**Ask Questions:**

- Type natural language questions like:
  - "Show all users"
  - "List top 5 expensive products"
  - "Find total orders per user"
  - "Show products with their categories"

**Example Queries:**

- Click any example to auto-fill the question field
- Modify and submit

**View Results:**

- Generated SQL query is displayed
- Can copy SQL to clipboard or use in your application

## Architecture

```
frontend/
├── app/
│   ├── layout.tsx         # Root layout with AuthProvider
│   ├── page.tsx           # Main page (AuthScreen or Dashboard)
│   └── globals.css        # Tailwind CSS styles
├── components/
│   ├── AuthProvider.tsx   # Authentication context
│   ├── AuthScreen.tsx     # Login/Register UI
│   ├── Dashboard.tsx      # Main dashboard layout
│   ├── DatabaseConnections.tsx  # DB connection management
│   └── NL2SQLQuery.tsx    # Query interface
├── lib/
│   └── api.ts            # API client wrapper
├── types/
│   └── api.ts            # TypeScript interfaces
└── .env.local            # Environment variables
```

## API Integration

The frontend communicates with the FastAPI backend:

- `POST /auth/register` - User registration
- `POST /auth/login` - User authentication
- `POST /databases/` - Create database connection
- `GET /databases/` - List user's databases
- `GET /databases/{id}` - Get database details
- `PUT /databases/{id}/test` - Test connection
- `DELETE /databases/{id}` - Delete connection
- `POST /databases/{id}/refresh-schema` - Refresh schema
- `POST /query/nl2sql` - Generate SQL from natural language

## Component Details

### AuthProvider

- Manages global authentication state
- Persists user session in localStorage
- Provides `login()`, `logout()`, and `user` to all components

### AuthScreen

- Tab-based UI for Login/Register
- Form validation and error handling
- Automatic redirect on successful auth

### DatabaseConnections

- CRUD operations for database connections
- Real-time connection testing
- Schema statistics display
- Refresh functionality

### NL2SQLQuery

- Database selection dropdown
- Schema visualization (tables, columns, foreign keys)
- Natural language input field
- Example queries for quick testing
- SQL output display

## Tech Stack

- **Next.js 16.1.3** - React framework with App Router
- **React 19.2.3** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS 4** - Styling
- **React Context** - State management

## Troubleshooting

### Connection Refused Error

- Ensure backend API is running on port 8000
- Check `.env.local` has correct API URL

### Authentication Issues

- Clear localStorage and re-login
- Check browser console for errors

### Schema Not Loading

- Verify database connection is valid
- Click "Refresh" to re-extract schema
- Check backend logs for errors

### SQL Generation Errors

- Ensure database schema is loaded
- Try simpler questions first
- Check if T5 model is properly loaded in backend

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
