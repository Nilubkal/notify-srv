"""
Simple test suite - 3 basic unit tests.

Mocking: We use unittest.mock to replace real Teams HTTP calls with fake ones.
This makes tests fast, reliable, and prevents spamming Teams channels.
    patch(): Temporarily replaces real objects with mocks
    AsyncMock(): Creates fake async functions that return predetermined values

Imports:
    fastapi.testclient.TestClient: HTTP client for testing FastAPI endpoints
    unittest.mock: Mocking tools (AsyncMock, patch) to fake external dependencies
    main.app: The FastAPI application to test
    models.notification_store: Singleton to clear between tests
"""

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main import app
from models import notification_store


client = TestClient(app)


def setup_function():
    """Run before each test."""
    notification_store.clear()


def teardown_function():
    """Run after each test."""
    notification_store.clear()


def test_health_check():
    """Test 1: Health check endpoint works."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["service"] == "Notification Service"


def test_create_warning_notification():
    """Test 2: Warning notification is created and would be forwarded."""
    # Mock the teams forwarder to avoid real HTTP calls
    with patch("main.teams_forwarder") as mock_forwarder:
        mock_forwarder.should_forward = lambda n: n.type == "Warning"
        mock_forwarder.forward = AsyncMock(return_value=True)
        
        # Send notification
        notification_data = {
            "Type": "Warning",
            "Name": "Test Warning",
            "Description": "This is a test warning"
        }
        
        response = client.post("/notifications", json=notification_data)
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "created"
        assert data["notification"]["type"] == "Warning"
        assert data["notification"]["name"] == "Test Warning"
        assert data["forwarding"]["forwarded"] is True


def test_create_info_notification():
    """Test 3: Info notification is created but NOT forwarded."""
    # Mock the teams forwarder
    with patch("main.teams_forwarder") as mock_forwarder:
        mock_forwarder.should_forward = lambda n: n.type == "Warning"
        mock_forwarder.forward = AsyncMock(return_value=True)
        
        # Send notification
        notification_data = {
            "Type": "Info",
            "Name": "Test Info",
            "Description": "This is just information"
        }
        
        response = client.post("/notifications", json=notification_data)
        
        # Verify response
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "created"
        assert data["notification"]["type"] == "Info"
        assert data["notification"]["name"] == "Test Info"
        assert data["forwarding"]["forwarded"] is False
        assert data["forwarding"]["status"] == "skipped_info_type"


if __name__ == "__main__":
    print("Running test 1: Health check...")
    setup_function()
    test_health_check()
    teardown_function()
    print("Test 1 passed")
    
    print("\nRunning test 2: Warning notification...")
    setup_function()
    test_create_warning_notification()
    teardown_function()
    print("Test 2 passed")
    
    print("\nRunning test 3: Info notification...")
    setup_function()
    test_create_info_notification()
    teardown_function()
    print("Test 3 passed")
    
    print("\n All 3 tests passed!")
