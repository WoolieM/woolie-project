import os
import json
import uuid
import time
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def run_smoke_test():
    print("🕵️  Starting Pub/Sub Smoke Test...")

    # 1. Configuration
    project_id = os.getenv("GCP_PROJECT_ID")
    topic_id = os.getenv("GCP_PUB_SUB_TOPIC")
    # Default to the subscription name defined in your Terraform
    subscription_id = os.getenv("GCP_PUB_SUB_SUBSCRIPTION", "bitcoin-price-sub")

    # Strip whitespace to prevent errors from .env file formatting
    if project_id: project_id = project_id.strip()
    if topic_id: topic_id = topic_id.strip()
    if subscription_id: subscription_id = subscription_id.strip()

    if not project_id or not topic_id:
        print("❌ Error: Missing GCP_PROJECT_ID or GCP_PUB_SUB_TOPIC environment variables.")
        return

    print(f"🔧 Config: Project='{project_id}', Topic='{topic_id}', Sub='{subscription_id}'")

    # 2. Initialize Clients
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()

    topic_path = publisher.topic_path(project_id, topic_id)
    subscription_path = subscriber.subscription_path(project_id, subscription_id)

    # 3. Publish a Unique Smoke Test Message
    unique_id = str(uuid.uuid4())
    payload = {
        "smoke_test": True,
        "id": unique_id,
        "timestamp": time.time(),
        "message": "Hello from the smoke test!"
    }
    data = json.dumps(payload).encode("utf-8")

    print(f"\n📤 Publishing message with ID: {unique_id}...")
    try:
        future = publisher.publish(topic_path, data)
        msg_id = future.result()
        print(f"✅ Published successfully (Pub/Sub Msg ID: {msg_id})")
    except Exception as e:
        print(f"❌ Failed to publish: {e}")
        return

    # 4. Listen for the Message
    print(f"\n📥 Listening for message on {subscription_id}...")
    
    received_event = False

    def callback(message):
        nonlocal received_event
        try:
            data_str = message.data.decode("utf-8")
            data_json = json.loads(data_str)

            # Check if it's OUR smoke test message
            if data_json.get("id") == unique_id:
                print(f"✅ Received our smoke test message!")
                print(f"   Content: {data_json}")
                message.ack()
                received_event = True
                streaming_pull_future.cancel() # Stop listening
            else:
                # Nack unrelated messages so they stay in the queue for the real app
                message.nack() 
        except Exception:
            message.nack()

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

    # 5. Wait (Block) until received or timeout
    with subscriber:
        try:
            # Wait up to 20 seconds
            streaming_pull_future.result(timeout=20)
        except (TimeoutError, Exception):
            # If we cancelled it (success) or timed out (failure)
            if received_event:
                print("\n🎉 SMOKE TEST PASSED: Full cycle complete.")
            else:
                print("\n❌ SMOKE TEST FAILED: Timed out waiting for message.")

if __name__ == "__main__":
    run_smoke_test()
