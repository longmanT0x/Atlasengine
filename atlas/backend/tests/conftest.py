"""
Pytest configuration and fixtures.

Provides shared fixtures for all tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from app.api.schemas import AnalyzeRequest
from tests.fixtures.sample_ideas import get_all_test_ideas


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    from main import app
    return TestClient(app)


@pytest.fixture
def sample_ideas():
    """Get all sample test ideas."""
    return get_all_test_ideas()


@pytest.fixture
def fintech_eu_idea():
    """FinTech EU idea fixture."""
    from tests.fixtures.sample_ideas import FINTECH_EU_IDEA
    return FINTECH_EU_IDEA


@pytest.fixture
def travel_belgium_idea():
    """Travel Belgium idea fixture."""
    from tests.fixtures.sample_ideas import TRAVEL_BELGIUM_IDEA
    return TRAVEL_BELGIUM_IDEA


@pytest.fixture
def b2b_saas_benelux_idea():
    """B2B SaaS Benelux idea fixture."""
    from tests.fixtures.sample_ideas import B2B_SAAS_BENELUX_IDEA
    return B2B_SAAS_BENELUX_IDEA


