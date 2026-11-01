# Placement Intelligence Portal

Centralized college placement portal for students and the Placement Cell (PCELL) and Training & Placement Officer (TPO).

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | React (Vite), Tailwind CSS, React Router, Axios, Recharts, Lucide |
| Backend | FastAPI, SQLAlchemy, Pydantic, Alembic, JWT, bcrypt |
| Database | PostgreSQL (Supabase-compatible connection string) |
| Storage | Supabase Storage (optional) or local `./uploads` |

## Project structure

```
placement-portal/
├── frontend/          # React SPA
├── backend/           # FastAPI API
├── docker-compose.yml # Local PostgreSQL
├── .env.example
└── README.md
```

## Quick start (local)

### 1. Database

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example ..\.env   # or symlink
python -m scripts.init_db
python -m scripts.seed
uvicorn app.main:app --reload --port 8000
```

Run commands from `backend/` with `PYTHONPATH=.` (default when using `python -m scripts.*` from `backend/`).

### 3. Frontend

```bash
cd frontend
npm install
echo VITE_API_BASE_URL=http://localhost:8000 > .env
npm run dev
```

Open http://localhost:5173

## Demo accounts (after seed)

Password for all: `Demo@12345`

| Role | Email |
|------|--------|
| Student | `student@college.demo` |
| PCELL | `pcell@college.demo` |
| TPO | `tpo@college.demo` |

## Student registration

Student self-registration with college email is **disabled by default** (`ALLOW_STUDENT_REGISTRATION=false`) until your college identity source is connected. Login works with seeded demo users.

## Supabase (production)

Set in `.env`:

- `DATABASE_URL` / `DATABASE_URL_SYNC` — Supabase Postgres connection strings
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_STORAGE_BUCKET`
- `USE_LOCAL_STORAGE=false`

## Deployment

- **Frontend:** Vercel — root `frontend`, build `npm run build`, output `dist`
- **Backend:** Render/Railway — start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **DB / storage:** Supabase

## Key features implemented

- Three-level RBAC: STUDENT → PCELL_MEMBER → TPO
- Year-wise company history and roles
- Canonical interview questions with student submissions, duplicate detection, PCELL verification (contributors hidden from students)
- Interview experiences with rounds
- Events and registration forms with deadline-based OPEN/CLOSED status
- Dashboard feed prioritizing nearest registration deadlines
- Resume PDF upload, text extraction (PyMuPDF), skill dictionary extraction (no role gap analysis)
- Placement analytics (from stored records only)
- TPO PCELL approval workflow and audit logging
- Global search across companies, questions, topics, skills, events

## API docs

With backend running: http://localhost:8000/docs

## Tests

```bash
cd backend
pip install -r requirements-dev.txt   # inside the venv
python -m pytest
```

Tests use a separate `placement_portal_test` database (created automatically; Postgres from docker compose must be running) and never touch dev data.
