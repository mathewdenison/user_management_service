import json

import boto3
import logging
from watchtower import CloudWatchLogHandler
from dotenv import load_dotenv
import os

load_dotenv()

log_group = os.getenv('LOG_GROUP_ASSOCIATE')
stream_name = os.getenv('STREAM_NAME_ASSOCIATE')

cw_handler = CloudWatchLogHandler(log_group=log_group, stream_name=stream_name)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(cw_handler)
logger.propagate = False

"""FIXME change this to be a environment variable or k8 secret"""
QUEUE_URL = "https://sqs.us-east-2.amazonaws.com/050451366043/Hopkins_EP_Queue"
sqs_client = boto3.client("sqs", region_name="us-east-2")


def send_message_to_queue(queue_name, data, method):

    # Retrieve the Queue URL from the queue name
    response = sqs_client.get_queue_url(QueueName=queue_name)
    queue_url = response['QueueUrl']

    delay_seconds = {
        'POST': 0,
        'PUT': 5,
        'PATCH': 5,
        'DELETE': 15,
    }[method]

    attributes = {
        'method': {
            'DataType': 'String',
            'StringValue': method,
        },
        'delay_seconds': {
            'DataType': 'Number',
            'StringValue': str(delay_seconds),
        },
    }

    response = sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(data),
        DelaySeconds=delay_seconds,
        MessageAttributes=attributes
    )

    return response


def delete_message_from_queue(receipt_handle):
    sqs_client.delete_message(
        QueueUrl=QUEUE_URL,
        ReceiptHandle=receipt_handle
    )

def receive_messages_from_queue():
    """Receive messages from the SQS queue."""
    response = sqs_client.receive_message(
        QueueUrl=QUEUE_URL,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=10
    )
    messages = response.get("Messages", [])
    logger.info(f"Received {len(messages)} messages from queue.")
    return messages


def consume_message_from_queue(queue_url):
    messages = receive_messages_from_queue(queue_url)
    for message in messages:
        msg_body = json.loads(message['Body'])
        delete_message_from_queue(message['ReceiptHandle'])
    return
