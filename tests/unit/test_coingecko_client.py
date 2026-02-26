import pytest
import httpx
from app.simulation.clients.coingecko import CoinGeckoClient


@pytest.mark.asyncio
async def test_get_prices_success(mocker):
    """Test fetching multiple coins, currencies, and volumes using the Client class."""

    # 1. Setup: Create mock data reflecting your new requirements
    # BTC and ETH in both AUD and USD with 24h volumes
    mock_data = {
        "bitcoin": {
            "aud": 105000.0,
            "aud_24h_vol": 50000000.0,
            "usd": 68000.0,
            "usd_24h_vol": 35000000.0,
            "last_updated_at": 1772111752
        },
        "ethereum": {
            "aud": 3500.0,
            "aud_24h_vol": 15000000.0,
            "usd": 2300.0,
            "usd_24h_vol": 10000000.0,
            "last_updated_at": 1772111752
        }
    }

    # 2. Mock the async response
    mock_res = httpx.Response(
        status_code=200,
        json=mock_data,
        request=httpx.Request(
            "GET", "https://api.coingecko.com/api/v3/simple/price")
    )

    # 3. Patch the 'get' call
    mock_get = mocker.patch("httpx.AsyncClient.get", return_value=mock_res)

    # 4. Execution: Using the new method name and a fake key
    client = CoinGeckoClient(api_key="fake_key_123")
    result = await client.get_prices(coin_ids="bitcoin,ethereum", currencies="aud,usd")

    # 5. Assertions: Verify the "Joints" of the data
    assert result["bitcoin"]["aud"] == 105000.0
    assert result["ethereum"]["usd"] == 2300.0
    assert "aud_24h_vol" in result["bitcoin"]
    assert result["bitcoin"]["last_updated_at"] == 1772111752

    # 6. Senior Move: Verify the Parameters sent to the API
    # This ensures your 'get_prices' logic correctly formats the strings
    args, kwargs = mock_get.call_args
    sent_params = kwargs.get("params")

    assert sent_params["ids"] == "bitcoin,ethereum"
    assert sent_params["vs_currencies"] == "aud,usd"
    assert sent_params["include_24hr_vol"] == "true"
