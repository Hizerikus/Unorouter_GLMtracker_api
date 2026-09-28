import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from models import PricingCatalog, ModelPricingDetails, CacheMeta, TrackedModels
from config import settings


class CacheService:
    def __init__(self, db: Session):
        self.db = db

    def is_cache_valid(self, key: str, ttl_seconds: int) -> bool:
        meta = self.db.query(CacheMeta).filter(CacheMeta.key == key).first()
        if not meta:
            return False
        elapsed = (datetime.utcnow() - meta.fetched_at).total_seconds()
        return elapsed < ttl_seconds

    def update_cache_meta(self, key: str, ttl_seconds: int):
        meta = self.db.query(CacheMeta).filter(CacheMeta.key == key).first()
        if meta:
            meta.fetched_at = datetime.utcnow()
            meta.ttl_seconds = ttl_seconds
        else:
            meta = CacheMeta(key=key, fetched_at=datetime.utcnow(), ttl_seconds=ttl_seconds)
            self.db.add(meta)
        self.db.commit()

    def save_catalog(self, data: List[Dict[str, Any]]):
        self.db.query(PricingCatalog).delete()
        for item in data:
            catalog = PricingCatalog(
                model_name=item.get("model_name", ""),
                vendor=item.get("vendor", ""),
                type=item.get("type", ""),
                is_free=item.get("is_free", False),
                online=item.get("online", False),
                input_price=item.get("input_price", 0.0),
                output_price=item.get("output_price", 0.0),
                original_input_price=item.get("original_input_price", 0.0),
                original_output_price=item.get("original_output_price", 0.0),
                tags=",".join(item.get("tags", [])) if item.get("tags") else "",
                supported_endpoint_types=",".join(item.get("supported_endpoint_types", [])) if item.get("supported_endpoint_types") else "",
                uptime_24h=item.get("uptime_24h", 0.0),
                success_rate=item.get("success_rate", 0.0),
                avg_latency_ms=item.get("avg_latency_ms", 0),
            )
            self.db.add(catalog)
        self.db.commit()
        self.update_cache_meta("catalog", settings.cache.catalog_ttl_seconds)

    def get_catalog(self) -> List[PricingCatalog]:
        return self.db.query(PricingCatalog).all()

    def save_model_prices(self, model_name: str, data: Dict[str, Any]):
        self.db.query(ModelPricingDetails).filter(ModelPricingDetails.model_name == model_name).delete()
        
        group_ratio = data.get("group_ratio", {})
        if isinstance(group_ratio, dict):
            group_ratio_str = json.dumps(group_ratio)
            group_ratio_val = list(group_ratio.values())[0] if group_ratio else 0.0
        else:
            group_ratio_str = json.dumps(group_ratio) if group_ratio else "{}"
            group_ratio_val = float(group_ratio) if group_ratio else 0.0
        
        enable_groups = data.get("enable_groups", [])
        if isinstance(enable_groups, list):
            enable_groups_str = ",".join(enable_groups)
        else:
            enable_groups_str = str(enable_groups)
        
        details = ModelPricingDetails(
            model_name=model_name,
            vendor=data.get("vendor", ""),
            vendor_id=data.get("vendor_id", 0),
            type=data.get("type", ""),
            tags=",".join(data.get("tags", [])) if data.get("tags") else "",
            is_free=data.get("is_free", False),
            online=data.get("online", False),
            input_price=data.get("input_price", 0.0),
            output_price=data.get("output_price", 0.0),
            original_input_price=data.get("original_input_price", 0.0),
            original_output_price=data.get("original_output_price", 0.0),
            group_ratio=group_ratio_str,
            completion_ratio=data.get("completion_ratio", 0.0),
            cache_ratio=data.get("cache_ratio", 0.0),
            model_ratio=data.get("model_ratio", 0.0),
            enable_groups=enable_groups_str,
            is_tiered=data.get("is_tiered", False),
            uptime_24h=data.get("uptime_24h", 0.0),
            success_rate=data.get("success_rate", 0.0),
            avg_latency_ms=data.get("avg_latency_ms", 0),
        )
        self.db.add(details)
        self.db.commit()
        self.update_cache_meta(f"model:{model_name}", settings.cache.model_ttl_seconds)

    def get_model_prices(self, model_name: str) -> Optional[ModelPricingDetails]:
        return self.db.query(ModelPricingDetails).filter(ModelPricingDetails.model_name == model_name).first()

    def save_counts(self, data: Dict[str, Any]):
        self.update_cache_meta("counts", settings.cache.counts_ttl_seconds)

    def save_vendors(self, data: Dict[str, Any]):
        self.update_cache_meta("vendors", settings.cache.vendors_ttl_seconds)

    def get_tracked_models(self) -> List[str]:
        models = self.db.query(TrackedModels).filter(TrackedModels.is_active == True).all()
        return [m.model_name for m in models]

    def add_tracked_model(self, model_name: str, custom_ttl: Optional[int] = None):
        tracked = TrackedModels(model_name=model_name, custom_ttl_seconds=custom_ttl)
        self.db.merge(tracked)
        self.db.commit()

    def remove_tracked_model(self, model_name: str):
        self.db.query(TrackedModels).filter(TrackedModels.model_name == model_name).delete()
        self.db.commit()