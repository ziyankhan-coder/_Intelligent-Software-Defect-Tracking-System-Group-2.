# BugFlow — Software Issue Tracking & Resolution Platform

> Infosys 8-Week Software Group Project

A centralized Software Issue Tracking & Resolution Platform built with **Django + DRF** (backend), **PostgreSQL** (database), and **React.js** (frontend).

## 🚀 Quick Start (Backend)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env          # Configure your environment
python manage.py migrate
python manage.py runserver 8000
```
## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register/` | Register new user |
| `POST` | `/api/v1/auth/login/` | Login → JWT tokens + user role |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh expired token |
| `GET` | `/api/v1/auth/me/` | Get authenticated user profile |
| `GET/POST` | `/api/v1/bugs/` | List/Create issues |
| `GET/PATCH` | `/api/v1/bugs/<id>/` | Issue detail/update |
| `GET` | `/api/v1/bugs/summary/` | Dashboard counts |
| `GET/POST` | `/api/v1/projects/` | List/Create projects |

## 🔑 Authentication

Uses **SimpleJWT** (self-hosted, no external API key needed).

```bash
# Login
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "ziyan", "password": "BugFlow@2026"}'

# Use the token
curl http://127.0.0.1:8000/api/v1/bugs/ \
  -H "Authorization: Bearer <access_token>"
```

## 👥 Team

| Member | Role | Modules |
|--------|------|---------|
| Ziyan | Backend Lead | Django setup, JWT auth, Issue models, RBAC |
| Ramya | Frontend Lead | React.js, Tailwind, Kanban board |
| Sreevarshinii | AI Logic Lead | NLP triage, duplicate detection |
| Naren | Integration & Test | Docker, CI/CD, pytest |
| Nandhini | Backend & QA | Collaboration, QA testing |

## 📋 Tech Stack

- **Backend:** Python 3, Django 5, Django REST Framework
- **Auth:** SimpleJWT (HMAC-SHA256)
- **Database:** PostgreSQL (SQLite for local dev)
- **Frontend:** React.js + Tailwind CSS (separate repo)
## Project Status
- [x] Project setup, modular Django apps, PostgreSQL schema
- [x] JWT authentication (login, register, token refresh)
- [x] Issue and project REST APIs
- [ ] Role-based access control (in progress)
- [ ] Workflow state machine, sprints, analytics, AI triage
