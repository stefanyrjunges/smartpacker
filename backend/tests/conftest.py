import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use an in-memory database so tests never touch the real smartpack.db.
# This must be set before flask_app is imported.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from flask_app import app, db


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()

        with app.test_client() as test_client:
            yield test_client

        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth_headers(client):
    # Register a user and return headers with their token
    res = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = res.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}
