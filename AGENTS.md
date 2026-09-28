# Unorouter Pricing API - Agent Reference

This document provides all information needed for agents to interact with the Unorouter Pricing API wrapper.

## Base URL
```
http://localhost:7414
```
(WSL2 forwards Windows `localhost:7414` to this service)

## Endpoints

### 1. Health Check
```
GET /health
```
**Response:**
```json
{"status": "ok", "service": "unorouter-pricing-api"}
```

### 2. Full Model Catalog
```
GET /pricing/catalog
Query params: force_refresh=false
```
**Response:** Array of 230+ model objects
```json
[
  {
    "model_name": "glm-5.3",
    "vendor": "Zhipu",
    "type": "text",
    "is_free": false,
    "online": true,
    "input_price": 0.061152,
    "output_price": 0.1921946208,
    "original_input_price": 0.98,
    "original_output_price": 3.080042,
    "tags": ["Text", "Reasoning", "Tools", "Open Weights", "1M", "Cache"],
    "supported_endpoint_types": ["openai"],
    "uptime_24h": 94.96,
    "success_rate": 97.5,
    "avg_latency_ms": 11083
  },
  ...
]
```

### 3. Single Model Pricing (with Provider Groups)
```
GET /pricing/catalog/{model_name}
Query params: force_refresh=false
```
**Response:** Detailed pricing with all provider groups
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
  "enable_groups": ["kdy1-2-glm-5.3", "kdy1-3-glm-5.3", ...],
  "is_tiered": false,
  "uptime_24h": 94.96,
  "success_rate": 97.5,
  "avg_latency_ms": 11083
}
```

### 4. Quick Counts
```
GET /pricing/counts
Query params: force_refresh=false
```
**Response:**
```json
{
  "models": 234,
  "free": 111,
  "paid": 123,
  "vendors": 41
}
```

### 5. Vendors
```
GET /pricing/vendors
Query params: force_refresh=false
```
**Response:**
```json
{
  "vendor_names": ["Zhipu", "OpenAI", "Anthropic", "Google", ...],
  "model_vendors": [
    {"model_name": "glm-5.3", "vendor": "Zhipu", "chat": true, "is_free": false, "tag": "Text", "release_ts": 1787086655000},
    ...
  ]
}
```

### 6. Force Refresh
```
POST /pricing/refresh
```
**Response:**
```json
{"success": true, "message": "Cache refreshed successfully"}
```

## Cache Behavior

| Endpoint | Default TTL | Config Key |
|----------|-------------|------------|
| /pricing/catalog | 900s (15 min) | catalog_ttl_seconds |
| /pricing/catalog/{model} | 900s (15 min) | model_ttl_seconds |
| /pricing/counts | 300s (5 min) | counts_ttl_seconds |
| /pricing/vendors | 3600s (60 min) | vendors_ttl_seconds |

Use `?force_refresh=true` to bypass cache.

## Common Tasks for Agents

### Get GLM 5.3 Current Prices
```bash
curl -s http://localhost:7414/pricing/catalog/glm-5.3 | jq '.input_price, .output_price, .group_ratio'
```

### Calculate Actual Provider Prices
```python
# Pricing formula from Unorouter:
# input $/1M = model_ratio * 2 * group_ratio
# output = input * completion_ratio
# cached = input * cache_ratio

model_ratio = 0.49
completion_ratio = 3.1429
cache_ratio = 0.1837

for provider, group_ratio in group_ratios.items():
    input_price = model_ratio * 2 * group_ratio
    output_price = input_price * completion_ratio
    cache_price = input_price * cache_ratio
    print(f"{provider}: input=${input_price:.6f}/1M, output=${output_price:.6f}/1M, cache=${cache_price:.6f}/1M")
```

### Find Cheapest Provider for GLM 5.3
```bash
curl -s http://localhost:7414/pricing/catalog/glm-5.3 | jq -r '.group_ratio | to_entries[] | "\(.key) \(.value)"' | sort -k2 -n | head -5
```

### Check if Model Exists
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:7414/pricing/catalog/glm-5.3
# Returns 200 if exists, 404 if not
```

### Get All Free Models
```bash
curl -s http://localhost:7414/pricing/catalog | jq '.[] | select(.is_free==true) | {model_name, vendor, input_price, output_price}'
```

### Get Models by Vendor
```bash
curl -s http://localhost:7414/pricing/catalog | jq '.[] | select(.vendor=="Zhipu") | {model_name, input_price, output_price, is_free}'
```

### Monitor Cache Status
```bash
curl -s http://localhost:7414/pricing/counts
# Check fetched_at timestamps in database:
sqlite3 pricing_cache.db "SELECT key, fetched_at, ttl_seconds FROM cache_meta;"
```

## Error Handling

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 404 | Model not found (for `/catalog/{model}`) |
| 500 | Internal error (check logs) |

## Background Refresh

- APScheduler runs every 15 minutes (configurable via `default_ttl_seconds`)
- Only refreshes active tracked models
- Configure tracked models in `config.yaml` or via database

## Database Schema (SQLite)

```sql
-- Cached pricing catalog
pricing_catalog (model_name PK, vendor, type, is_free, online, input_price, output_price, original_input_price, original_output_price, tags, supported_endpoint_types, uptime_24h, success_rate, avg_latency_ms, fetched_at)

-- Per-model provider prices
model_pricing_details (model_name PK, vendor, vendor_id, type, tags, is_free, online, input_price, output_price, original_input_price, original_output_price, group_ratio JSON, completion_ratio, cache_ratio, model_ratio, enable_groups, is_tiered, uptime_24h, success_rate, avg_latency_ms, fetched_at)

-- Cache metadata
cache_meta (key PK, fetched_at, ttl_seconds)

-- Tracked models
tracked_models (model_name PK, is_active, custom_ttl_seconds)
```

## Python Client Example

```python
import httpx

BASE = "http://localhost:7414"

async def get_model_price(model: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/pricing/catalog/{model}")
        r.raise_for_status()
        return r.json()

async def get_catalog():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE}/pricing/catalog")
        r.raise_for_status()
        return r.json()

# Usage
import asyncio
data = asyncio.run(get_model_price("glm-5.3"))
print(f"Input: ${data['input_price']}/1M tokens")
print(f"Output: ${data['output_price']}/1M tokens")
```