import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

SQLITE_URL = "sqlite:///./test.db"

with patch.dict(os.environ, {
    "DB_USERNAME": "test", "DB_PASSWORD": "test",
    "DB_SERVER": "localhost", "DB_DATABASE": "test",
}):
    import database
    import models

database.engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=database.engine)

for table in models.Base.metadata.tables.values():
    table.schema = None

import auth
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
    from fastapi.testclient import TestClient

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
