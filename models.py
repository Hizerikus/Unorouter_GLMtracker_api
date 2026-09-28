from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, REAL, Integer, Text, DateTime, PrimaryKeyConstraint
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PricingCatalog(Base):
    __tablename__ = "pricing_catalog"

    model_name = Column(String, primary_key=True)
    vendor = Column(String)
    type = Column(String)
    is_free = Column(Boolean)
    online = Column(Boolean)
    input_price = Column(REAL)
    output_price = Column(REAL)
    original_input_price = Column(REAL)
    original_output_price = Column(REAL)
    tags = Column(Text)
    supported_endpoint_types = Column(Text)
    uptime_24h = Column(REAL)
    success_rate = Column(REAL)
    avg_latency_ms = Column(Integer)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class ModelPricingDetails(Base):
    __tablename__ = "model_pricing_details"

    model_name = Column(String, primary_key=True)
    vendor = Column(String)
    vendor_id = Column(Integer)
    type = Column(String)
    tags = Column(Text)
    is_free = Column(Boolean)
    online = Column(Boolean)
    input_price = Column(REAL)
    output_price = Column(REAL)
    original_input_price = Column(REAL)
    original_output_price = Column(REAL)
    group_ratio = Column(Text)  # Store as JSON string
    completion_ratio = Column(REAL)
    cache_ratio = Column(REAL)
    model_ratio = Column(REAL)
    enable_groups = Column(Text)
    is_tiered = Column(Boolean)
    uptime_24h = Column(REAL)
    success_rate = Column(REAL)
    avg_latency_ms = Column(Integer)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class CacheMeta(Base):
    __tablename__ = "cache_meta"

    key = Column(String, primary_key=True)
    fetched_at = Column(DateTime)
    ttl_seconds = Column(Integer)


class TrackedModels(Base):
    __tablename__ = "tracked_models"

    model_name = Column(String, primary_key=True)
    is_active = Column(Boolean, default=True)
    custom_ttl_seconds = Column(Integer, nullable=True)