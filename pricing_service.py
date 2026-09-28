from typing import List, Dict, Any, Optional
import json
from sqlalchemy.orm import Session

from client import UnorouterClient
from cache_service import CacheService
from models import PricingCatalog, ModelPricingDetails
from config import settings


class PricingService:
    def __init__(self, db: Session):
        self.db = db
        self.client = UnorouterClient()
        self.cache = CacheService(db)

    async def get_catalog(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        if not force_refresh and self.cache.is_cache_valid("catalog", settings.cache.catalog_ttl_seconds):
            catalog = self.cache.get_catalog()
            return [self._catalog_to_dict(c) for c in catalog]

        data = await self.client.get_catalog()
        self.cache.save_catalog(data)
        return data

    async def get_model_prices(self, model_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        cache_key = f"model:{model_name}"
        if not force_refresh and self.cache.is_cache_valid(cache_key, settings.cache.model_ttl_seconds):
            details = self.cache.get_model_prices(model_name)
            if details:
                return self._model_details_to_dict(details)

        data = await self.client.get_model_prices(model_name)
        self.cache.save_model_prices(model_name, data)
        return data

    async def get_counts(self, force_refresh: bool = False) -> Dict[str, Any]:
        if not force_refresh and self.cache.is_cache_valid("counts", settings.cache.counts_ttl_seconds):
            pass

        data = await self.client.get_counts()
        self.cache.save_counts(data)
        return data

    async def get_vendors(self, force_refresh: bool = False) -> Dict[str, Any]:
        if not force_refresh and self.cache.is_cache_valid("vendors", settings.cache.vendors_ttl_seconds):
            pass

        data = await self.client.get_vendors()
        self.cache.save_vendors(data)
        return data

    async def refresh_all(self):
        await self.get_catalog(force_refresh=True)
        for model_name in self.cache.get_tracked_models():
            await self.get_model_prices(model_name, force_refresh=True)
        await self.get_counts(force_refresh=True)
        await self.get_vendors(force_refresh=True)

    async def close(self):
        await self.client.close()

    def _catalog_to_dict(self, c: PricingCatalog) -> Dict[str, Any]:
        return {
            "model_name": c.model_name,
            "vendor": c.vendor,
            "type": c.type,
            "is_free": c.is_free,
            "online": c.online,
            "input_price": c.input_price,
            "output_price": c.output_price,
            "original_input_price": c.original_input_price,
            "original_output_price": c.original_output_price,
            "tags": c.tags.split(",") if c.tags else [],
            "supported_endpoint_types": c.supported_endpoint_types.split(",") if c.supported_endpoint_types else [],
            "uptime_24h": c.uptime_24h,
            "success_rate": c.success_rate,
            "avg_latency_ms": c.avg_latency_ms,
        }

    def _model_details_to_dict(self, d: ModelPricingDetails) -> Dict[str, Any]:
        group_ratio = {}
        try:
            if d.group_ratio:
                group_ratio = json.loads(d.group_ratio)
        except (json.JSONDecodeError, TypeError):
            group_ratio = {}
        
        return {
            "model_name": d.model_name,
            "vendor": d.vendor,
            "vendor_id": d.vendor_id,
            "type": d.type,
            "tags": d.tags.split(",") if d.tags else [],
            "is_free": d.is_free,
            "online": d.online,
            "input_price": d.input_price,
            "output_price": d.output_price,
            "original_input_price": d.original_input_price,
            "original_output_price": d.original_output_price,
            "group_ratio": group_ratio,
            "completion_ratio": d.completion_ratio,
            "cache_ratio": d.cache_ratio,
            "model_ratio": d.model_ratio,
            "enable_groups": d.enable_groups.split(",") if d.enable_groups else [],
            "is_tiered": d.is_tiered,
            "uptime_24h": d.uptime_24h,
            "success_rate": d.success_rate,
            "avg_latency_ms": d.avg_latency_ms,
        }