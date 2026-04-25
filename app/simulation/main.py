import asyncio
import os
import sys
import click
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


async def run_ingestion(minutes: int):

    # 1. Strict Env Loading (No Hardcoding!)
    try:
        api_key = os.environ["COINGECKO_API_KEY"].strip()
        project_id = os.environ["GCP_PROJECT_ID"].strip()
        topic_id = os.environ["GCP_PUB_SUB_TOPIC"].strip()
        app_env = os.environ["ENV"].strip()
    except KeyError as e:
        print(f"❌ Missing Environment Variable: {e}")
        # Exit with error code so Cloud Run marks the job as Failed
        sys.exit(1)

    # Setup
    client = CoinGeckoClient(api_key)
    producer = PubSubProducer(project_id, topic_id)

    print(f"🚀 Starting ingestion loop for {minutes} minutes...")

    for i in range(minutes):
        try:
            print(f"⏱️  Iteration {i + 1}/{minutes}")
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

            # Only sleep if this isn't the last iteration
            if i < minutes - 1:
                await asyncio.sleep(60)
        except Exception as e:
            print(f"❌ Error: {e}")
            # Instead of just sleeping, consider if the error is "Fatal"
            # For a Cloud Job, sometimes it's better to 'raise' the error
            # so Google Cloud logs it as a 'Failed' execution rather than 'Success'.
            if i < minutes - 1:
                await asyncio.sleep(10)
            else:
                # Raise on the final attempt to ensure the job fails loudly in GCP
                raise

@click.command()
@click.option('--minutes', default=5, help='Number of minutes to run the simulation')
def main(minutes):
    """Runs the simulation for a specific number of minutes."""
    asyncio.run(run_ingestion(minutes))

if __name__ == "__main__":
    main()
