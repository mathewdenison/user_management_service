import json
import logging
from google.cloud import pubsub_v1
from google.cloud import logging as cloud_logging
from dotenv import load_dotenv
import os

load_dotenv()

# Setup Google Cloud Logging
client = cloud_logging.Client()
client.setup_logging()

# Setup Google Cloud Pub/Sub
publisher = pubsub_v1.PublisherClient()
subscriber = pubsub_v1.SubscriberClient()

# GCP Pub/Sub topic and subscription names (replace with actual values)
topic_name = os.getenv('PUBSUB_TOPIC')
subscription_name = os.getenv('PUBSUB_SUBSCRIPTION')

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Function to send messages to GCP Pub/Sub
def send_message_to_topic(topic_name, data, method):
    try:
        # Delay mapping
        delay_seconds = {
            'POST': 0,
            'PUT': 5,
            'PATCH': 5,
            'DELETE': 15,
        }.get(method.upper(), 0)

        # Log the intent with context
        type_info = data.get('type') if isinstance(data, dict) else None
        if type_info:
            logger.info(f"Sending message of type '{type_info}' to topic '{topic_name}'")

        logger.info(f"Topic: {topic_name}, Method: {method}, Payload: {str(data)[:300]}")

        future = publisher.publish(
            f'projects/{os.getenv("GCP_PROJECT_ID")}/topics/{topic_name}',
            data=json.dumps(data).encode('utf-8'),
            method=str(method),
            delay_seconds=str(delay_seconds)
        )

        message_id = future.result()
        logger.info(f"Message sent to {topic_name}. Message ID: {message_id}")
        return message_id

    except Exception as e:
        logger.exception(f"Error sending message to Pub/Sub topic {topic_name}: {e}")
        return None

# Function to receive messages from the Pub/Sub subscription
def receive_messages_from_subscription(subscription_name):
    subscription_path = subscriber.subscription_path(
        os.getenv("GCP_PROJECT_ID"), subscription_name
    )
    response = subscriber.pull(subscription_path, max_messages=10, return_immediately=True)
    messages = response.received_messages
    logger.info(f"Received {len(messages)} messages from subscription.")
    return messages

# Function to acknowledge message after processing
def acknowledge_message(subscription_name, ack_id):
    subscription_path = subscriber.subscription_path(
        os.getenv("GCP_PROJECT_ID"), subscription_name
    )
    subscriber.acknowledge(subscription_path, [ack_id])

# Function to process and delete messages from the Pub/Sub queue
def consume_message_from_subscription(subscription_name):
    messages = receive_messages_from_subscription(subscription_name)
    for message in messages:
        msg_body = json.loads(message.message.data.decode("utf-8"))
        acknowledge_message(subscription_name, message.ack_id)
