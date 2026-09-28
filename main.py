from contextlib import asynccontextmanager
from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import settings
from database import init_db, get_db, engine
from models import Base, TrackedModels, ModelPricingDetails
from pricing_service import PricingService
from schemas import (
    CatalogItem, ModelPricingDetailsResponse, CountsResponse,
    VendorsResponse, HealthResponse, RefreshResponse
)


scheduler = AsyncIOScheduler()


async def refresh_tracked_models():
    from database import SessionLocal
    db = SessionLocal()
    try:
        service = PricingService(db)
        await service.refresh_all()
    finally:
        await service.close()
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from database import SessionLocal
    db = SessionLocal()
    try:
        # Insert tracked models from config into database
        for model_name in settings.tracked_models.tracked_models:
            existing = db.query(TrackedModels).filter(TrackedModels.model_name == model_name).first()
            if not existing:
                db.add(TrackedModels(model_name=model_name, is_active=True))
            else:
                existing.is_active = True
        db.commit()
        
        tracked = db.query(TrackedModels).filter(TrackedModels.is_active == True).all()
        for t in tracked:
            if t.model_name not in settings.tracked_models.tracked_models:
                settings.tracked_models.tracked_models.append(t.model_name)
    finally:
        db.close()
    
    scheduler.add_job(
        refresh_tracked_models,
        IntervalTrigger(seconds=settings.cache.default_ttl_seconds),
        id="refresh_tracked_models",
        replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Unorouter Pricing API",
    description="FastAPI wrapper for Unorouter pricing with SQLite caching",
    version="0.1.0",
    lifespan=lifespan,
)


def get_pricing_service(db: Session = Depends(get_db)) -> PricingService:
    return PricingService(db)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")


@app.get("/pricing/catalog", response_model=List[CatalogItem])
async def get_catalog(
    force_refresh: bool = Query(False, description="Force cache refresh"),
    service: PricingService = Depends(get_pricing_service),
):
    return await service.get_catalog(force_refresh=force_refresh)


@app.get("/pricing/catalog/{model_name}", response_model=ModelPricingDetailsResponse)
async def get_model_prices(
    model_name: str,
    force_refresh: bool = Query(False, description="Force cache refresh"),
    service: PricingService = Depends(get_pricing_service),
):
    data = await service.get_model_prices(model_name, force_refresh=force_refresh)
    if not data:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
    return data


@app.get("/pricing/counts", response_model=CountsResponse)
async def get_counts(
    force_refresh: bool = Query(False, description="Force cache refresh"),
    service: PricingService = Depends(get_pricing_service),
):
    return await service.get_counts(force_refresh=force_refresh)


@app.get("/pricing/vendors", response_model=VendorsResponse)
async def get_vendors(
    force_refresh: bool = Query(False, description="Force cache refresh"),
    service: PricingService = Depends(get_pricing_service),
):
    return await service.get_vendors(force_refresh=force_refresh)


@app.post("/pricing/refresh", response_model=RefreshResponse)
async def refresh_cache(
    service: PricingService = Depends(get_pricing_service),
):
    await service.refresh_all()
    return RefreshResponse(success=True, message="Cache refreshed successfully")