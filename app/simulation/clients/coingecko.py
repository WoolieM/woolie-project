import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
import dataclasses


@dataclasses.dataclass
class CoinGeckoClient:
    api_key: str
    base_url: str = "https://api.coingecko.com/api/v3"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_prices(
        self,
        coin_ids: str = "bitcoin,ethereum",
        currencies: str = "aud,usd"
    ) -> dict:
        """Fetches multiple coins and currencies in one handshake."""
        headers = {
            "x-cg-demo-api-key": self.api_key,
            "accept": "application/json"
        }
        params = {
            "ids": coin_ids,
            "vs_currencies": currencies,
            "include_24hr_vol": "true",
            "include_last_updated_at": "true"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/simple/price",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
