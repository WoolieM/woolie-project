import json
from app.simulation.producers.pubsub_producer import PubSubProducer


def test_publish_message_success(mocker):
    # 1. Mock the Publisher Client
    mock_client = mocker.patch("google.cloud.pubsub_v1.PublisherClient")
    mock_publisher = mock_client.return_value

    # 2. Setup a mock "Future" for the async publish call
    mock_future = mocker.Mock()
    mock_future.result.return_value = "msg-98765"
    mock_publisher.publish.return_value = mock_future

    # 3. Execution
    producer = PubSubProducer(
        project_id="woolie-project", topic_id="btc-topic")
    test_data = {"price": 105000.0}
    msg_id = producer.publish_message(test_data)

    # 4. Assertion
    assert msg_id == "msg-98765"

    # Verify that topic_path was called with the correct project and topic IDs
    mock_publisher.topic_path.assert_called_once_with(
        "woolie-project", "btc-topic")

    # Verify the specific "handshake" (Topic path and encoded bytes)
    expected_bytes = json.dumps(test_data).encode("utf-8")
    mock_publisher.publish.assert_called_once_with(
        producer.topic_path,
        expected_bytes
    )
