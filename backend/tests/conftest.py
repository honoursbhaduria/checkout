import os
import pytest

# Ensure test mode is flagged before application imports
os.environ["TESTING"] = "1"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:secret@localhost:5433/interview_db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
