# Notification Service - Quick Start

## TLDR

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup and run
uv venv
./run.sh
```

Service runs at `http://localhost:8000` • Docs at `http://localhost:8000/docs`

---

## Test It

```bash
# Send Warning (forwards to Teams if configured)
curl -X POST http://localhost:8000/notifications \
  -H "Content-Type: application/json" \
  -d '{"Type":"Warning","Name":"Test Alert","Description":"Test warning"}'

# Send Info (stored only, not forwarded)
curl -X POST http://localhost:8000/notifications \
  -H "Content-Type: application/json" \
  -d '{"Type":"Info","Name":"Status","Description":"All good"}'

# Check stats
curl http://localhost:8000/stats
```

---

## Configuration

```bash
# Add Teams webhook URL
export TEAMS_WEBHOOK_URL="https://your-webhook-url"

```

Without Teams config: Service runs normally, Warning notifications log to `warning.log`

---

## Common Commands

```bash
# Run service
./run.sh

# Run tests
source .venv/bin/activate
pytest test_simple.py -v

# View API docs
http://localhost:8000/docs
```

---

## Speed: uv vs pip

**pip:** ~35 seconds  
**uv:** 0.2 seconds (150x faster!)

```bash
# Traditional way
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt  # ⏱️  35s

# Modern way (uv)
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt  # ⏱️  0.2s
```

---

## Full Documentation

See `README.md` for complete documentation including:

- All API endpoints
- Architecture details
- Testing strategy
- Troubleshooting
