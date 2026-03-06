import asyncio
import os
from dotenv import load_dotenv
import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from app.simulation.clients.coingecko import CoinGeckoClient
from app.simulation.producers.pubsub_producer import PubSubProducer

load_dotenv()


standard_retry = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=lambda retry_state: print(
        f"Retrying... {retry_state.attempt_number} | Error: {retry_state.outcome.exception()}")
)


@standard_retry
async def fetch_data(client: CoinGeckoClient):
    """
        Sip data from CoinGecko with retries
    """
    return await client.get_prices(
        coin_ids="bitcoin,ethereum",
        currencies="aud,usd"
    )


@standard_retry
def publish_to_pubsub(producer: PubSubProducer, payload: dict):
    """
        Publish message to Pub/Sub with retries
    """
    return producer.publish_message(payload)


async def run_ingestion():

    # 1. Strict Env Loading (No Hardcoding!)
    try:
        api_key = os.environ["COINGECKO_API_KEY"].strip()
        project_id = os.environ["GCP_PROJECT_ID"].strip()
        topic_id = os.environ["GCP_PUB_SUB_TOPIC"].strip()
        app_env = os.environ["ENV"].strip()
    except KeyError as e:
        print(f"❌ Missing Environment Variable: {e}")
        return

    # Setup
    client = CoinGeckoClient(api_key)
    producer = PubSubProducer(project_id, topic_id)

    while True:
        try:
            # 1. Fetch
            data = await fetch_data(client)

            # 2. Transform & Publish
            for coin, stats in data.items():
                payload = {
                    "metadata": {
                        "source": "coingecko",
                        "ingested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        "environment": app_env
                    },
                    "data": {
                        "asset": coin,
                        "price_aud": float(stats["aud"]),
                        "price_usd": float(stats["usd"]),
                        "volume_aud": float(stats["aud_24h_vol"]),
                        "volume_usd": float(stats["usd_24h_vol"]),
                        "source_timestamp": int(stats["last_updated_at"])
                    }
                }

                # 3. Publish
                msg_id = publish_to_pubsub(producer, payload)
                print(
                    f"✅ Published {coin}: {stats['aud']} AUD / {stats['usd']} USD (ID: {msg_id})")

            await asyncio.sleep(60)  # Fetch every minute
        except Exception as e:
            print(f"❌ Error: {e}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(run_ingestion())
