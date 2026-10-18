import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

logger = logging.getLogger("exam_portal.database")

# Environment detection: set ENVIRONMENT=production in .env to disable SQLite fallback
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development").lower()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_url = settings.DATABASE_URL
connect_args = {}

# Test connecting to configured database (e.g. Postgres), fallback to SQLite if Postgres unavailable
if db_url.startswith("postgresql"):
    try:
        temp_engine = create_engine(db_url, connect_args={"connect_timeout": 2})
        with temp_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection established successfully.")
    except Exception as e:
        if ENVIRONMENT == "production":
            # #11: In production, fail loudly if PostgreSQL is unreachable
            logger.critical("FATAL: PostgreSQL is unreachable in production mode: %s", e)
            raise RuntimeError(
                f"PostgreSQL database is unreachable in production mode. "
                f"Set ENVIRONMENT=development to enable SQLite fallback. Error: {e}"
            )
        # Fallback to SQLite for local development only
        logger.warning("PostgreSQL unavailable, falling back to SQLite for development.")
        sqlite_file = os.path.join(BASE_DIR, "exam_portal.db").replace("\\", "/")
        db_url = f"sqlite:///{sqlite_file}"
        connect_args = {"check_same_thread": False}
elif db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Ensure relative SQLite path is always anchored to the backend directory
    raw_path = db_url.replace("sqlite:///", "")
    if not os.path.isabs(raw_path):
        clean_rel = raw_path.lstrip("./").lstrip(".\\")
        abs_db = os.path.join(BASE_DIR, clean_rel).replace("\\", "/")
        db_url = f"sqlite:///{abs_db}"


# Create Engine
engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for getting DB session in endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> dict:
    """Helper function to test database connectivity"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            return {"status": "connected", "database_type": engine.dialect.name}
    except Exception as e:
        return {"status": "disconnected", "error": str(e)}

