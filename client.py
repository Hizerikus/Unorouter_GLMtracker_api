import httpx
from typing import Optional, Dict, Any, List
from config import settings


class UnorouterClient:
    def __init__(self):
        self.base_url = settings.unorouter.base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def get_catalog(self) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/pricing/catalog"
        response = await self.client.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("models", [])

    async def get_model_prices(self, model_name: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/pricing/catalog/model"
        params = {"model": model_name}
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def get_counts(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/pricing/counts"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_vendors(self) -> Dict[str, Any]:
        url = f"{self.base_url}/api/pricing/vendors"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()