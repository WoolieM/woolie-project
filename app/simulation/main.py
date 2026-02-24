import asyncio
import os
from dotenv import load_dotenv
from app.simulation.clients.coingecko import CoinGeckoClient
from app.simulation.producers.pubsub_producer import PubSubProducer

load_dotenv()


async def run_ingestion():
    # Setup
    client = CoinGeckoClient(os.getenv("COINGECKO_API_KEY"))
    producer = PubSubProducer(
        os.getenv("GCP_PROJECT_ID"), "bitcoin-price-topic")

    while True:
        try:
            # 1. Fetch
            data = await client.get_bitcoin_price()

            # 2. Transform (Minor)
            payload = {
                "asset": "BTC",
                "price_aud": data["bitcoin"]["aud"],
                "timestamp": data["bitcoin"]["last_updated_at"]
            }

            # 3. Publish
            msg_id = producer.publish_message(payload)
            print(f"✅ Published: {payload['price_aud']} AUD (ID: {msg_id})")

            await asyncio.sleep(60)  # Fetch every minute
        except Exception as e:
            print(f"❌ Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_ingestion())
