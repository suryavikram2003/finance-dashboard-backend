from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app.models import record, user  # noqa: F401 – ensure models are registered
from app.routes import auth, dashboard, records, users

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Finance Dashboard API",
    description=(
        "A production-ready FastAPI backend for a finance dashboard system.\n\n"
        "### Roles\n"
        "- **Viewer** – read-only dashboard access\n"
        "- **Analyst** – read records + analytics\n"
        "- **Admin** – full CRUD + user management\n\n"
        "### Authentication\n"
        "Use `POST /auth/login` with email + password to receive a JWT token.\n"
        "Then click **Authorize** and enter `Bearer <your_token>`."
    ),
    version="1.0.0",
    contact={"name": "Suryavikram K", "email": "suryavikramkrishnan@gmail.com"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(records.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Finance Dashboard API is running"}
