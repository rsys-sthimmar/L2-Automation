import asyncio
import os
import tempfile
import uuid
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.db.database import Base, get_db
from app.models.user import User, UserRole
from app.utils.auth import get_password_hash, create_access_token

# Use a temp file-based SQLite to allow connection sharing across sessions
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_db_path}"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()
    try:
        os.unlink(_db_path)
    except OSError:
        pass


@pytest_asyncio.fixture
async def db_session(test_db):
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def mock_llm():
    mock = MagicMock()
    mock.query = AsyncMock(return_value={
        "answer": "RRCSetup is defined in TS 38.331 Section 6.2.2.",
        "references": ["TS 38.331 Section 6.2.2"],
        "confidence": "high",
        "domain": "RRC",
        "message_flow": None,
        "edge_cases": None,
    })
    mock.analyze_logs = AsyncMock(return_value="Log analysis: RRCSetup detected. No failures found.")
    mock.generate_test_plan = AsyncMock(return_value=(
        "Objective: Test RRC Setup\n"
        "Preconditions:\n- UE powered on\n- Network available\n"
        "Steps:\n- Trigger RRC setup\n- Verify messages\n"
        "Expected Results:\n- Setup completes successfully\n"
    ))
    return mock


@pytest_asyncio.fixture
async def async_client(test_db):
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def master_user(db_session):
    suffix = uuid.uuid4().hex[:8]
    user = User(
        username=f"master_{suffix}",
        email=f"master_{suffix}@test.com",
        hashed_password=get_password_hash("masterpass"),
        role=UserRole.master,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def child_user(db_session):
    suffix = uuid.uuid4().hex[:8]
    user = User(
        username=f"child_{suffix}",
        email=f"child_{suffix}@test.com",
        hashed_password=get_password_hash("childpass"),
        role=UserRole.child,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def master_user_token(master_user):
    return create_access_token({"sub": master_user.username, "role": master_user.role.value})


@pytest_asyncio.fixture
async def child_user_token(child_user):
    return create_access_token({"sub": child_user.username, "role": child_user.role.value})
