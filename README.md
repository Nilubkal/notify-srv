# Notification Service

A simple, pragmatic RESTful web service that receives notifications and forwards warnings to Microsoft Teams.

## Philosophy

Built following these principles:

- **Classical Python** - No type hints, no decorators, no magic
- **Explicit over implicit** - All behavior is visible
- **Simple data structures** - Clean notification model with explicit methods
- **No special cases** - Straightforward filtering logic
- **Pragmatic** - Solves the actual problem without overengineering
- **Production-ready** - Focused tests, proper error handling

## Features

- RESTful API using FastAPI
- Forwards "Warning" notifications to Microsoft Teams
- Stores "Info" notifications but doesn't forward them
- In-memory storage (no database needed)
- Multiple service support (concurrent notifications)
- **Classical Python** (no type hints, no decorators)
- **Explicit implementation** (explicit **init**, explicit route registration)
- **3 focused tests** covering core functionality
- Simple configuration via environment variables

## Quick Start

### 0. Install uv (if not already installed)

```bash
# Install uv - fast Python package installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv
```

### 1. Install Dependencies

```bash
# Using uv (recommended - 10-100x faster than pip)
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Or use the quick start script
./run.sh
```

### 2. Configure Teams Webhook

```bash
# Set Teams webhook URL as environment variable
export TEAMS_WEBHOOK_URL="https://your-teams-webhook-url"
```

### 3. Run the Service

```bash
# Quick start (handles everything)
./run.sh

# Or manually
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

Service will be available at: `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

## API Endpoints

### POST /notifications

Create a new notification.

**Request Body:**

```json
{
  "Type": "Warning",
  "Name": "Backup Failure",
  "Description": "The backup failed due to a database problem"
}
```

**Response:**

```json
{
  "status": "created",
  "notification": {
    "type": "Warning",
    "name": "Backup Failure",
    "description": "The backup failed due to a database problem",
    "received_at": "2025-01-28T20:30:00.123456"
  },
  "forwarding": {
    "forwarded": true,
    "status": "success"
  }
}
```

**Behavior:**

- `Type: "Warning"` → Stored + Forwarded to Teams
- `Type: "Info"` → Stored only (not forwarded)

### GET /notifications

List stored notifications.

**Query Parameters:**

- `filter` (optional): `forwarded`, `ignored`, or omit for all

**Example:**

```bash
curl http://localhost:8000/notifications?filter=forwarded
```

### GET /stats

Get notification statistics.

**Response:**

```json
{
  "total": 10,
  "forwarded": 6,
  "ignored": 4
}
```

### DELETE /notifications

Clear all stored notifications (useful for testing).

### GET /

Health check endpoint.

## Testing

Run the simplified test suite (3 basic tests):

```bash
# Run all tests
pytest test_simple.py -v

# Or run manually
python test_simple.py
```

### Test Coverage

The test suite covers core functionality:

- **Test 1**: Health check endpoint
- **Test 2**: Warning notification (created and forwarded)
- **Test 3**: Info notification (created but NOT forwarded)

**Why only 3 tests?**

- Focused on essential functionality
- No decorator complexity in test fixtures
- Explicit setup/teardown functions
- Easy to understand and maintain

## Architecture

### Project Structure

```
notify_srv/
├── main.py              # FastAPI app (324 lines)
├── models.py            # Data + storage + Teams (214 lines)
├── test_simple.py       # 3 focused tests (115 lines)
├── requirements.txt     # 7 dependencies
├── run.sh               # Quick start script
├── README.md            # Complete documentation
└── QUICKSTART.md        # TLDR + quick setup
```

### Design Decisions

**1. Classical Python (No Type Hints, No Decorators)**

- No type hints: `def __init__(self, type, name, description):`
- No decorators: explicit `__init__`, `__repr__`, `__eq__`
- `from_dict()` module function (not a class method)
- Explicit route registration with `app.add_api_route()`
- Explicit startup/shutdown events
- Flat structure - no unnecessary nesting

**2. Simple Filtering Logic**

```python
def should_forward(notification):
    return notification.type == "Warning"
```

No special cases, no complex conditions.

**3. In-Memory Storage**

- List-based storage for simplicity (potential high memory consumption)
- Easy to test and reason about
- No database overhead for this use case

**4. Async/Await for I/O**

- Teams webhook calls are async (non-blocking)
- Service remains responsive during forwards
- Handles multiple concurrent notifications

**5. Error Handling**

- Teams forwarding failures don't crash the service
- Notifications are always stored even if forward fails
- Clear error messages in responses

## Configuration

### Environment Variables

| Variable            | Description                          | Required |
| ------------------- | ------------------------------------ | -------- |
| `TEAMS_WEBHOOK_URL` | Microsoft Teams incoming webhook URL | Yes      |

## Usage Examples

### Example 1: Warning Notification (Forwarded)

```bash
curl -X POST http://localhost:8000/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "Type": "Warning",
    "Name": "Backup Failure",
    "Description": "The backup failed due to a database problem"
  }'
```

Result: Notification stored + forwarded to Teams with red warning card.

### Example 2: Info Notification (Not Forwarded)

```bash
curl -X POST http://localhost:8000/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "Type": "Info",
    "Name": "Quota Exceeded",
    "Description": "Compute Quota exceeded"
  }'
```

Result: Notification stored but NOT forwarded to Teams.

### Example 3: Check Statistics

```bash
curl http://localhost:8000/stats
```

### Example 4: List Forwarded Notifications

```bash
curl http://localhost:8000/notifications?filter=forwarded
```

## Multiple Service Support

The API is designed for multiple services to send notifications concurrently:

```python
# Service A
POST /notifications {"Type": "Warning", "Name": "ServiceA-Alert", ...}

# Service B
POST /notifications {"Type": "Info", "Name": "ServiceB-Status", ...}

# Service C
POST /notifications {"Type": "Warning", "Name": "ServiceC-Error", ...}
```

## Troubleshooting

### Service starts but doesn't forward to Teams

**Check:**

1. Is `TEAMS_WEBHOOK_URL` exported as environment variable?
2. Is the webhook URL valid and not expired?
3. Check console output for error messages
4. Verify: `echo $TEAMS_WEBHOOK_URL`

### Tests fail with import errors

**Solution:**

```bash
# Make sure you're in the notify_srv directory
cd notify_srv

# Install test dependencies with uv
uv pip install -r requirements.txt

# Run tests
pytest test_main.py -v
```
