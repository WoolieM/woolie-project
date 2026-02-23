import asyncio
import os
import httpx
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# 1. Load your .env from the project root
load_dotenv()

# 2. Setup your credentials from the .env file
API_KEY = os.getenv("COINGECKO_API_KEY")
BASE_URL = "https://api.coingecko.com/api/v3"

# 3. Add Senior-level Retry Logic (stops after 3 fails)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def get_bitcoin_price():
    # Per the CoinGecko email: Use the header for the demo key
    headers = {
        "x-cg-demo-api-key": API_KEY,
        "accept": "application/json"
    }

    # Parameters for the Sydney Bubble (AUD)
    params = {
        "ids": "bitcoin",
        "vs_currencies": "aud",
        "include_last_updated_at": "true"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/simple/price", headers=headers, params=params)

        # This will raise an error if the API is down or the key is wrong
        response.raise_for_status()

        data = response.json()
        print(f"Success! BTC Price: ${data['bitcoin']['aud']} AUD")
        return data

if __name__ == "__main__":
    asyncio.run(get_bitcoin_price())
