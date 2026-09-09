import os
import tempfile
from pathlib import Path

TEST_DIR = Path(tempfile.mkdtemp(prefix="campus-ai-test-"))
os.environ["DATABASE_PATH"] = str(TEST_DIR / "test.db")
os.environ["TOKEN_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
