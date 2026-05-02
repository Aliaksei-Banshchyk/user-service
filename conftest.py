"""
conftest.py – UserService
Place this file at the ROOT of the user-service repo alongside users.py.

What it does:
  1. Adds the shared package to sys.path (same trick as the service files)
  2. Swaps Azure SQL for SQLite in-memory (strips schema= from table args)
  3. Provides a `client` fixture with DB + auth overrides
"""
import sys
import os

# ── point to the shared repo (adjust relative path if needed) ────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))
sys.path.insert(0, os.path.dirname(__file__))

# ── patch database BEFORE any service module is imported ─────────────────────
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch

SQLITE_URL = "sqlite:///./test.db"

# Patch pyodbc / SQL Server connection so importing database.py doesn't crash
with patch.dict(os.environ, {
    "DB_USERNAME": "test", "DB_PASSWORD": "test",
    "DB_SERVER": "localhost", "DB_DATABASE": "test",
}):
    import database
    import models

# Replace the engine with SQLite
database.engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
database.SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=database.engine
)

# Strip SQL-Server schema from all tables so SQLite accepts them
for table in models.Base.metadata.tables.values():
    table.schema = None

import auth
import schemas
from main import app
from database import get_db
from auth import get_current_user


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    models.Base.metadata.create_all(bind=database.engine)
    yield
    models.Base.metadata.drop_all(bind=database.engine)
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture()
def db():
    connection = database.engine.connect()
    transaction = connection.begin()
    session = database.SessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """TestClient with DB and auth overridden."""
    from fastapi.testclient import TestClient

    # Create a reusable test user
    test_user = models.User(
        id=1, login="testuser",
        password=auth.hash_password("password123"),
        name="Test User",
    )
    db.add(test_user)
    db.commit()

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: test_user

    with TestClient(app) as c:
        yield c, test_user

    app.dependency_overrides.clear()
