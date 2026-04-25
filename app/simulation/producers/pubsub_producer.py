import json
from google.cloud import pubsub_v1
import dataclasses

@dataclasses.dataclass
class PubSubProducer:
    project_id: str
    topic_id: str

    def __post_init__(self):
        # This runs after project_id and topic_id are set
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(
            self.project_id, self.topic_id
        )

    def publish_message(self, data: dict):
        message_bytes = json.dumps(data).encode("utf-8")
        future = self.publisher.publish(self.topic_path, message_bytes)
        # result() blocks until the message is confirmed by GCP
        return future.result()
