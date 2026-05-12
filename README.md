# squadron-ops

A modern naval aviation operations platform. Multi-squadron, multi-
community, designed to expand to all Navy aviation communities.

Forked from hsc-squadron-ops v1.0-demo (single-tenant HSC-specific
prototype). See ROADMAP.md for current capabilities and direction.

## Status

In active development. v1.0-demo predecessor still runs as a working
HSC operations demo.

## Stack

- Backend: FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + Alembic, Python 3.12
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS + TanStack Query
- Database: PostgreSQL via Docker Compose

## Quickstart

docker compose up -d
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload
# in another terminal
cd frontend && npm run dev

Visit http://localhost:5173 (or :5174 if running alongside v1)
