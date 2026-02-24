import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import dataclasses


@dataclasses.dataclass
class CoinGeckoClient:
    api_key: str
    base_url: str = "https://api.coingecko.com/api/v3"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_bitcoin_price(self):
        headers = {"x-cg-demo-api-key": self.api_key,
                   "accept": "application/json"}
        params = {"ids": "bitcoin", "vs_currencies": "aud",
                  "include_last_updated_at": "true"}

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/simple/price", headers=headers, params=params)
            response.raise_for_status()
            return response.json()
