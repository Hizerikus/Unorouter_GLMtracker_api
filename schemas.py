from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class CatalogItem(BaseModel):
    model_name: str
    vendor: str
    type: str
    is_free: bool
    online: bool
    input_price: float
    output_price: float
    original_input_price: float = 0.0
    original_output_price: float = 0.0
    tags: List[str] = []
    supported_endpoint_types: List[str] = []
    uptime_24h: float = 0.0
    success_rate: float = 0.0
    avg_latency_ms: int = 0


class ModelPricingDetailsResponse(BaseModel):
    model_name: str
    vendor: str
    vendor_id: int
    type: str
    tags: List[str] = []
    is_free: bool
    online: bool
    input_price: float
    output_price: float
    original_input_price: float
    original_output_price: float
    group_ratio: Dict[str, float] = {}
    completion_ratio: float
    cache_ratio: float
    model_ratio: float
    enable_groups: List[str] = []
    is_tiered: bool
    uptime_24h: float
    success_rate: float
    avg_latency_ms: int


class CountsResponse(BaseModel):
    models: int
    free: int
    paid: int
    vendors: int


class VendorsResponse(BaseModel):
    vendor_names: List[str]
    model_vendors: List[Dict[str, Any]]


class HealthResponse(BaseModel):
    status: str
    service: str = "unorouter-pricing-api"


class RefreshResponse(BaseModel):
    success: bool
    message: str