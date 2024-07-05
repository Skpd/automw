import os
import boto3
from dotenv import load_dotenv

from mosbot.common.logger import get_logger

if __name__ == '__main__':
    load_dotenv(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../.env"))
    logger = get_logger("queue")

    sqsResource = boto3.resource('sqs', region_name="eu-central-1")
    queue = sqsResource.get_queue_by_name(QueueName=os.getenv("PARSE_PLAYERS_SQS_QUEUE_NAME"))

    entries = []
    batch_limit = 10
    for sub_batch_start in range(1, 7387900, 10):
        entries.append({
            'Id': f'batch-entry-{sub_batch_start}',
            'MessageBody': '["--id", ' + ','.join(f'"{sub_batch_start + i}"' for i in range(10)) + ']',
        })
        if len(entries) == batch_limit:
            logger.info(f"Sending batch ending with {sub_batch_start + 9}")
            response = queue.send_messages(Entries=entries)
            entries = []
    if entries:
        logger.info(f"Sending last batch")
        response = queue.send_messages(Entries=entries)
        entries = []
