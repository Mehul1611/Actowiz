from fastapi import APIRouter
from sqlalchemy import text
from app.core.database import engine

router = APIRouter(tags=["health"])


def check_postgres_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "up"
    except Exception as exc:
        return f"down: {exc}"


@router.get("/health")
def health_check():
    postgres_status = check_postgres_connection()
    overall = "ok" if postgres_status == "up" else "degraded"
    return {"status": overall, "postgres": postgres_status}
