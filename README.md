# Finance Dashboard Backend

A production-ready **FastAPI** backend for a finance dashboard system with **JWT authentication**, **Role-Based Access Control (RBAC)**, real **SQL aggregation** queries, **Pydantic v2** validation, and **SQLite** persistence.

---

## Table of Contents
1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Setup Instructions](#setup-instructions)
4. [Authentication](#authentication)
5. [Role Permissions](#role-permissions)
6. [API Endpoints](#api-endpoints)
7. [Sample Requests & Responses](#sample-requests--responses)
8. [Assumptions & Design Decisions](#assumptions--design-decisions)

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.135 |
| Database | SQLite (via SQLAlchemy ORM) |
| Authentication | JWT (`python-jose`) |
| Password Hashing | bcrypt (`passlib`) |
| Validation | Pydantic v2 |
| Server | Uvicorn |
| Python | 3.12+ |

---

## Project Structure

```
app/
├── main.py                    # FastAPI app initialization, router registration
├── config.py                  # Environment-based configuration
├── db.py                      # SQLAlchemy engine, session, Base
├── models/
│   ├── user.py               # User ORM model (id, name, email, role, is_active)
│   └── record.py             # FinancialRecord ORM model with soft-delete
├── schemas/
│   ├── user_schema.py        # Pydantic schemas for user CRUD
│   ├── record_schema.py      # Pydantic schemas for record CRUD
│   └── dashboard_schema.py   # Response schemas for analytics endpoints
├── routes/
│   ├── auth.py               # POST /auth/register, /auth/login, /auth/refresh
│   ├── users.py              # CRUD /users/* with RBAC
│   ├── records.py            # CRUD /records/* with RBAC + filtering
│   └── dashboard.py          # GET /dashboard/* analytics endpoints
├── services/
│   ├── user_service.py       # User business logic
│   ├── record_service.py     # Record business logic + soft-delete
│   └── dashboard_service.py  # Real SQL aggregation queries
├── core/
│   ├── security.py           # JWT creation/verification, bcrypt hashing
│   └── dependencies.py       # Dependency injection (get_current_user, require_roles)
└── utils/
    └── exceptions.py         # Custom HTTP exceptions

requirements.txt
.env.example
README.md
```

---

## Setup Instructions

### 1. Clone & Install

```bash
git clone <repository-url>
cd finance-dashboard-backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set a strong SECRET_KEY
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload
```

The SQLite database (`finance.db`) is auto-created on first startup.

### 4. Explore the API

Open **http://localhost:8000/docs** for interactive Swagger UI.

---

## Authentication

The API uses **JWT Bearer tokens**.

1. Register: `POST /auth/register`
2. Login: `POST /auth/login` → receive `access_token` + `refresh_token`
3. Authorize requests: `Authorization: Bearer <access_token>`
4. Refresh: `POST /auth/refresh` with `refresh_token`

Tokens expire after **30 minutes** (access) and **7 days** (refresh).

---

## Role Permissions

| Action | Viewer | Analyst | Admin |
|--------|--------|---------|-------|
| View dashboard summary | ✅ | ✅ | ✅ |
| View recent activity | ✅ | ✅ | ✅ |
| View records list | ✅ | ✅ | ✅ |
| View category breakdown | ❌ | ✅ | ✅ |
| View monthly trends | ❌ | ✅ | ✅ |
| Create/Update/Delete records | ❌ | ❌ | ✅ |
| Create/Update/Delete users | ❌ | ❌ | ✅ |
| List all users | ❌ | ❌ | ✅ |
| View own profile | ✅ | ✅ | ✅ |
| Change own password | ✅ | ✅ | ✅ |

---

## API Endpoints

### Authentication
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login (returns JWT tokens) |
| POST | `/auth/refresh` | Refresh access token |

### Users
| Method | Path | Auth | Role |
|--------|------|------|------|
| GET | `/users/me` | ✅ | Any |
| GET | `/users/` | ✅ | Admin |
| POST | `/users/` | ✅ | Admin |
| GET | `/users/{id}` | ✅ | Admin / Own |
| PATCH | `/users/{id}` | ✅ | Admin / Own |
| POST | `/users/{id}/change-password` | ✅ | Own |
| DELETE | `/users/{id}` | ✅ | Admin |

### Financial Records
| Method | Path | Auth | Role |
|--------|------|------|------|
| GET | `/records/` | ✅ | Any |
| POST | `/records/` | ✅ | Admin |
| GET | `/records/{id}` | ✅ | Any |
| PUT | `/records/{id}` | ✅ | Admin |
| DELETE | `/records/{id}` | ✅ | Admin |

**Query parameters for `GET /records/`:**
- `page`, `page_size` – pagination
- `type` – `income` or `expense`
- `category` – partial match filter
- `start_date`, `end_date` – ISO date range
- `search` – searches category and notes

### Dashboard
| Method | Path | Auth | Role |
|--------|------|------|------|
| GET | `/dashboard/summary` | ✅ | Any |
| GET | `/dashboard/category-breakdown` | ✅ | Analyst, Admin |
| GET | `/dashboard/monthly-trends` | ✅ | Analyst, Admin |
| GET | `/dashboard/recent-activity` | ✅ | Any |

---

## Sample Requests & Responses

### Register & Login
```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"secret123","role":"admin"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@example.com&password=secret123"
# Returns: {"access_token":"...","refresh_token":"...","token_type":"bearer"}
```

### Create a Financial Record
```bash
curl -X POST http://localhost:8000/records/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount":50000,"type":"income","category":"Salary","date":"2026-03-01","notes":"Monthly salary"}'
```

### Dashboard Summary
```bash
curl http://localhost:8000/dashboard/summary \
  -H "Authorization: Bearer <token>"
# {
#   "total_income": 70000.0,
#   "total_expense": 20000.0,
#   "net_balance": 50000.0,
#   "record_count": 4
# }
```

### Filter Records
```bash
curl "http://localhost:8000/records/?type=expense&start_date=2026-01-01&page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

---

## Assumptions & Design Decisions

1. **Soft Delete**: `DELETE /records/{id}` sets `is_deleted=true`. Records are excluded from all queries automatically. Hard deletes are not exposed via API.

2. **Role Assignment on Register**: Users can self-assign a role at registration for demo purposes. In a production system, the registration endpoint would always assign `viewer` role and only admins could elevate roles.

3. **Record Ownership**: Any admin can create/edit/delete any record regardless of `user_id`. The `user_id` field on records tracks which admin created them.

4. **Password Storage**: Passwords are hashed with `bcrypt` (cost factor 12). Plain passwords are never stored or logged.

5. **Database**: SQLite is used for simplicity. The `DATABASE_URL` in `.env` can be changed to any SQLAlchemy-compatible database (PostgreSQL, MySQL) without code changes.

6. **CORS**: All origins are allowed (`*`) for development. Restrict in production.

7. **Token Refresh**: Refresh tokens are rotated on each use (new refresh token returned with each refresh).
