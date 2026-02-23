# LiveDocAI – Environment Variables Setup (Phase 1)

End-to-end instructions to collect all required environment variables and where to use them.

---

## Overview

| Service        | Purpose                    | Where to get variables              |
|----------------|----------------------------|-------------------------------------|
| **Supabase**   | Auth, Database, Storage    | [Supabase Dashboard](https://supabase.com/dashboard) |
| **Qdrant Cloud** | Vector store (embeddings) | [Qdrant Cloud](https://cloud.qdrant.io) |
| **Gemini API** | Embeddings + RAG chat      | [Google AI Studio](https://aistudio.google.com/apikey) |

---

## Step 1 – Supabase

### 1.1 Create a project (if you don’t have one)

1. Go to **https://supabase.com/dashboard**
2. Sign in (GitHub or email).
3. Click **New project**.
4. Choose organization, set **Name** (e.g. `livedocai`), **Database password**, **Region**.
5. Wait for the project to be ready.

### 1.2 Get project URL and keys

1. In the project, open **Project Settings** (gear icon in the left sidebar).
2. Go to **API**.
3. Copy and store:

| Variable | Where to copy | Used by |
|----------|----------------|---------|
| `SUPABASE_URL` | **Project URL** (e.g. `https://xxxx.supabase.co`) | Backend, Frontend |
| `SUPABASE_ANON_KEY` | **Project API keys** → **anon** **public** | Backend (JWT verify), Frontend (auth) |
| `SUPABASE_SERVICE_ROLE_KEY` | **Project API keys** → **service_role** **secret** | Backend only (admin/Storage/DB) |
| `SUPABASE_JWT_AUDIENCE` | Usually `authenticated` | Backend (JWT verify audience check) |

- **Never** expose `SUPABASE_SERVICE_ROLE_KEY` in the frontend or in git.

### 1.3 Enable Google OAuth (for “Sign in with Google”)

1. In Supabase: **Authentication** → **Providers** → **Google**.
2. Enable Google.
3. Use [Google Cloud Console](https://console.cloud.google.com/) to create OAuth 2.0 credentials (Web application), set Authorized redirect URI to the one Supabase shows (e.g. `https://<project-ref>.supabase.co/auth/v1/callback`).
4. Paste **Client ID** and **Client secret** into Supabase Google provider and save.

(OAuth credentials are configured in Supabase UI, not as env vars in this app.)

---

## Step 2 – Qdrant Cloud

### 2.1 Create a cluster

1. Go to **https://cloud.qdrant.io**
2. Sign up / log in (no credit card for free tier).
3. Click **Create cluster**.
4. Choose a name and region; select the **Free** tier (1 GB).
5. Wait for the cluster to be created.

### 2.2 Get URL and API key

1. Open your cluster.
2. Find **Cluster URL** (e.g. `https://xxxx-xxxx.aws.cloud.qdrant.io:6333`) and **API Key** (or create one under API Keys).
3. Copy and store:

| Variable | Where to copy | Used by |
|----------|----------------|---------|
| `QDRANT_URL` | **Cluster URL** (include `https://` and port if shown) | Backend |
| `QDRANT_API_KEY` | **API Key** | Backend |

- Use the exact URL format Qdrant shows (with or without port, e.g. `:6333`).

---

## Step 3 – Gemini API

### 3.1 Get an API key

1. Go to **https://aistudio.google.com/apikey**
2. Sign in with your Google account.
3. Click **Create API key** (use an existing Google Cloud project or create one when prompted).
4. Copy the key and store it.

| Variable | Where to copy | Used by |
|----------|----------------|---------|
| `GEMINI_API_KEY` | **API key** from Google AI Studio | Backend (embeddings + chat) |

- Keep the key secret; do not commit it to git.

---

## Step 4 – Create your `.env` file

1. In the project root, copy the example file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in every value using the tables above. Leave no required variable empty.
3. For **backend**: ensure the backend app loads `.env` from the correct path (e.g. `backend/.env` or project root). See **Where each app reads .env** below.
4. For **frontend**: Vite only exposes variables that start with `VITE_`. Use `frontend/.env` with `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_URL` (see `.env.example`).

---

## Where each app reads `.env`

- **Backend (FastAPI)**  
  - Prefer loading from `backend/.env` (or project root if you run the server from there).  
  - Required: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `GEMINI_API_KEY`.

- **Frontend (Vite + React)**  
  - Uses `frontend/.env` (or root `.env` if you use one and Vite is configured to load it).  
  - Required for auth and API: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`.

---

## Quick reference – variable list

| Variable | Required | Service   | Used by  |
|----------|----------|-----------|----------|
| `SUPABASE_URL` | Yes | Supabase  | Backend, Frontend |
| `SUPABASE_ANON_KEY` | Yes | Supabase  | Backend, Frontend |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase  | Backend only |
| `SUPABASE_JWT_AUDIENCE` | No (default `authenticated`) | Supabase | Backend |
| `QDRANT_URL` | Yes | Qdrant    | Backend |
| `QDRANT_API_KEY` | Yes | Qdrant    | Backend |
| `GEMINI_API_KEY` | Yes | Gemini    | Backend |
| `VITE_SUPABASE_URL` | Yes (frontend) | Supabase  | Frontend |
| `VITE_SUPABASE_ANON_KEY` | Yes (frontend) | Supabase  | Frontend |
| `VITE_API_URL` | Yes (frontend) | Backend URL | Frontend |
| `PORT` | No | Backend   | Server port (default 8000) |

---

## Security reminders

- Add `.env` to `.gitignore` and never commit real keys.
- Use `.env.example` (with empty or placeholder values) as the only env file in git.
- Restrict `SUPABASE_SERVICE_ROLE_KEY` and `GEMINI_API_KEY` to backend only; frontend must not see them.
