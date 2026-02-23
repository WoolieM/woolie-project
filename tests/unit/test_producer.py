import pytest
import httpx
from app.simulation.producer import get_bitcoin_price


@pytest.mark.asyncio
async def test_get_bitcoin_price_success(mocker):
    """Test that we can correctly parse a successful CoinGecko response."""

    # 1. Setup: Create a real-looking dictionary
    mock_data = {
        "bitcoin": {
            "aud": 100000.0,
            "last_updated_at": 1700000000
        }
    }

    # 2. Senior Move: Create a mock response object
    # We use a real Response object so raise_for_status() works correctly
    mock_res = httpx.Response(
        status_code=200,
        json=mock_data,
        request=httpx.Request(
            "GET", "https://api.coingecko.com/api/v3/simple/price")
    )

    # 3. Mock the 'get' call to return our mock response
    # Since 'client.get' is async, we use 'return_value' with our response
    mocker.patch("httpx.AsyncClient.get", return_value=mock_res)

    # 4. Execution
    result = await get_bitcoin_price()

    # 5. Assertion
    assert result["bitcoin"]["aud"] == 100000.0
    assert "last_updated_at" in result["bitcoin"]
