"""Pytest configuration for E2E tests."""

import pytest
import pytest_asyncio
import asyncio
import logging
from pathlib import Path
import sys
from typing import AsyncGenerator

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Configure logging for E2E tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# Removed custom event_loop fixture - let pytest-asyncio handle it


@pytest_asyncio.fixture(scope="session")
async def shared_e2e_runner() -> AsyncGenerator["E2ETestRunner", None]:
    """Shared E2E test runner for the entire test session."""
    from tests.e2e.test_e2e_automation import E2ETestRunner
    runner = E2ETestRunner()
    await runner.setup()
    yield runner
    await runner.teardown()


@pytest_asyncio.fixture
async def e2e_runner() -> AsyncGenerator["E2ETestRunner", None]:
    """Fresh E2E test runner for each test."""
    from tests.e2e.test_e2e_automation import E2ETestRunner
    runner = E2ETestRunner()
    await runner.setup()
    yield runner
    await runner.teardown()


@pytest.fixture
def e2e_test_data():
    """Common test data for E2E tests."""
    return {
        "initiative": {
            "title": "Test Initiative",
            "description": "Test initiative for E2E validation",
            "type": "initiative"
        },
        "epic": {
            "title": "Test Epic",
            "description": "Test epic for E2E validation",
            "type": "epic"
        },
        "feature": {
            "title": "Test Feature",
            "description": "Test feature for E2E validation",
            "type": "feature"
        },
        "story": {
            "title": "As a user, I want to test E2E functionality",
            "description": "Test user story for E2E validation",
            "type": "story"
        },
        "task": {
            "title": "Test Task",
            "description": "Test task for E2E validation",
            "type": "task"
        }
    }


# Pytest markers for E2E tests
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow
pytest.mark.integration = pytest.mark.integration