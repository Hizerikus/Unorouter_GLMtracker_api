# Unorouter Pricing API Wrapper

FastAPI wrapper around Unorouter's public pricing API with SQLite caching, focused on GLM 5.3 but configurable for other models. Accessible from Windows via WSL2 localhost forwarding.

## Features

- **6 REST endpoints** for pricing data
- **SQLite caching** with configurable TTL per endpoint
- **Background refresh** via APScheduler for tracked models
- **WSL2 compatible** - binds to `0.0.0.0:7414`, accessible from Windows at `http://localhost:7414`
- **Pre-configured for GLM 5.3** with easy addition of other models

## Endpoints

| Endpoint | Source | Cache TTL | Description |
|----------|--------|-----------|-------------|
| `GET /health` | - | - | Health check |
| `GET /pricing/catalog` | `/api/pricing/catalog` | 15 min | Full model list with prices |
| `GET /pricing/catalog/{model}` | `/api/pricing/catalog/model?model={name}` | 15 min | Per-provider prices for one model |
| `GET /pricing/counts` | `/api/pricing/counts` | 5 min | Quick totals (models, vendors, free/paid) |
| `GET /pricing/vendors` | `/api/pricing/vendors` | 60 min | Vendor list with model mappings |
| `POST /pricing/refresh` | - | - | Force cache refresh for all endpoints |

## Quick Start

```bash
# Start the server
./launch.sh start

# Test all endpoints
./launch.sh test

# Check status
./launch.sh status

# View logs
./launch.sh logs

# Stop server
./launch.sh stop
```

## Windows Access

WSL2 automatically forwards `localhost:7414` from Windows to WSL. From Windows PowerShell/CMD:

```powershell
curl http://localhost:7414/health
curl http://localhost:7414/pricing/catalog/glm-5.3
curl http://localhost:7414/pricing/counts
```

**Note:** Windows Firewall may block port 7414. Allow it if needed:
```powershell
New-NetFirewallRule -DisplayName "Unorouter API" -Direction Inbound -LocalPort 7414 -Protocol TCP -Action Allow
```

## Configuration

Edit `config.yaml`:

```yaml
unorouter:
  base_url: "https://api.unorouter.com"

cache:
  default_ttl_seconds: 900      # 15 min
  catalog_ttl_seconds: 900
  model_ttl_seconds: 900
  counts_ttl_seconds: 300       # 5 min
  vendors_ttl_seconds: 3600     # 60 min

tracked_models:
  tracked_models:
    - "glm-5.3"
    # Add more models here

server:
  host: "0.0.0.0"
  port: 7414

database:
  path: "pricing_cache.db"
```

## Adding Tracked Models

1. Add to `config.yaml` under `tracked_models.tracked_models`
2. Restart server: `./launch.sh restart`

Or programmatically:
```python
from database import SessionLocal
from models import TrackedModels

db = SessionLocal()
db.add(TrackedModels(model_name="gpt-5", is_active=True))
db.commit()
```

## Project Structure

```
├── main.py              # FastAPI app with all endpoints
├── config.py            # Pydantic settings with YAML support
├── config.yaml          # Configuration file
├── database.py          # SQLAlchemy setup
├── models.py            # Database models
├── client.py            # Unorouter HTTP client
├── cache_service.py     # SQLite cache operations
├── pricing_service.py   # Business logic
├── schemas.py           # Pydantic response models
├── launch.sh            # Management script
├── pyproject.toml       # Dependencies
├── tmp/                 # Temp files (logs, PID)
└── pricing_cache.db     # SQLite database (auto-created)
```

## Dependencies

- Python 3.11+
- FastAPI, Uvicorn
- httpx (with socks support)
- SQLAlchemy
- APScheduler
- PyYAML
- Pydantic, Pydantic-Settings

Install: `pip install -e .` (or `pip install --break-system-packages -e .` on Debian)

## Response Examples

### GET /pricing/catalog/glm-5.3
```json
{
  "model_name": "glm-5.3",
  "vendor": "Zhipu",
  "vendor_id": 4,
  "type": "text",
  "tags": ["Text", "Reasoning", "Tools", "Open Weights", "1M", "Cache"],
  "is_free": false,
  "online": true,
  "input_price": 0.061152,
  "output_price": 0.1921946208,
  "original_input_price": 0.98,
  "original_output_price": 3.080042,
  "group_ratio": {
    "kdy1-2-glm-5.3": 0.4899,
    "kdy1-3-glm-5.3": 0.4899,
    "a7-l-api-4772-glm-5.3": 0.1533,
    "a7-x-api-4224-glm-5.3": 0.1469,
    "a7-4069-glm-5.3": 0.1441,
    "a7-stable-5078-glm-5.3": 0.1322,
    "a7-vovo-api-5057-glm-5.3": 0.0955,
    "a7-kultur-5206-glm-5.3": 0.0661,
    "a7-bbgt-2846-glm-5.3": 0.0624
  },
  "completion_ratio": 3.1429,
  "cache_ratio": 0.1837,
  "model_ratio": 0.49,
  "enable_groups": [...],
  "is_tiered": false,
  "uptime_24h": 94.96,
  "success_rate": 97.5,
  "avg_latency_ms": 11083
}
```

### Pricing Formula
From Unorouter docs:
- `input $/1M = model_ratio * 2 * group_ratio`
- `output = input * completion_ratio`
- `cached = input * cache_ratio`

## License

MIT