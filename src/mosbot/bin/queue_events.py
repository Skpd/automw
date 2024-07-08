import argparse
import logging
import os
import sys

import boto3
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from mosbot.common.db import PlayerPage
from mosbot.common.logger import get_logger

if __name__ == '__main__':
    load_dotenv(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../.env"))
    logger = get_logger("queue")

    parser = argparse.ArgumentParser(description='Queue scrape events.')
    parser.add_argument('-v', '--verbose', help="Verbose logging.", required=False, default=False, action='store_true')
    parser.add_argument('-s', '--start', help="Range start", required=True, type=int)
    parser.add_argument('-e', '--end', help="Range end.", required=True, type=int)
    parser.add_argument('-i', '--ignore-existing', help="Ignore pages that already exists.", required=False, default=True)
    parser.add_argument('-b', '--batch-size', help="Pages per function call.", required=False, default=10, type=int)

    try:
        args = parser.parse_args()
    except Exception as e:
        logger.critical(f'Error parsing args: {type(e).__name__} {e}')
        sys.exit(1)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug enabled")

    sqsResource = boto3.resource('sqs', region_name="eu-central-1")
    queue = sqsResource.get_queue_by_name(QueueName=os.getenv("PARSE_PLAYERS_SQS_QUEUE_NAME"))

    range_start = args.start
    range_end = args.end

    if args.ignore_existing:
        _engine = create_engine(os.getenv("MOSBOT_DB_CS"), echo=True)
        with Session(_engine) as session:
            parsed_ids = set(session.execute(
                select(PlayerPage.id).where(PlayerPage.id >= range_start).where(PlayerPage.id <= range_end)
            ).scalars().all())
    else:
        parsed_ids = []

    entries = []
    sub_batch = []
    batch_limit = 10
    sub_batch_limit = args.batch_size
    # for sub_batch_start in range(range_start, range_end, 10):
    for _id in range(range_start, range_end, 1):
        if _id in parsed_ids:
            continue
        sub_batch.append(_id)
        if len(sub_batch) == sub_batch_limit:
            entries.append({
                'Id': f'batch-entry-{_id}',
                'MessageBody': f'["--id", ' + ','.join(f'"{x}"' for x in sub_batch) + ']',
            })
            sub_batch = []
        if len(entries) == batch_limit:
            # logger.info(f"Sending batch ending with {sub_batch_start + 9}")
            logger.info(f"Sending batch ending with {_id}")
            response = queue.send_messages(Entries=entries)
            entries = []
            sub_batch = []
    if sub_batch:
        entries.append({
            'Id': f'batch-entry-last',
            'MessageBody': f'["--id", ' + ','.join(f'"{x}"' for x in sub_batch) + ']',
        })
        sub_batch = []
    if entries:
        logger.info(f"Sending last batch")
        response = queue.send_messages(Entries=entries)
        entries = []
