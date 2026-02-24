import pytest
import httpx
from app.simulation.clients.coingecko import CoinGeckoClient


@pytest.mark.asyncio
async def test_get_bitcoin_price_success(mocker):
    # 1. Setup mock data
    mock_data = {"bitcoin": {"aud": 105000.0, "last_updated_at": 1700000000}}

    # 2. Mock the async response
    mock_res = httpx.Response(
        status_code=200,
        json=mock_data,
        request=httpx.Request(
            "GET", "https://api.coingecko.com/api/v3/simple/price")
    )

    # 3. Patch the 'get' call
    mocker.patch("httpx.AsyncClient.get", return_value=mock_res)

    # 4. Execution
    client = CoinGeckoClient(api_key="fake_key")
    result = await client.get_bitcoin_price()

    # 5. Assertion
    assert result["bitcoin"]["aud"] == 105000.0
    assert result["bitcoin"]["last_updated_at"] == 1700000000
