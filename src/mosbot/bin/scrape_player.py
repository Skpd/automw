import argparse
import json
import logging
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine

from mosbot.common.logger import get_logger
from mosbot.parse.player_info import PlayerInfoParser


def handler(event, context):
    print(f"Received {event=}")

    if 'Records' in event:
        response = []
        for record in event['Records']:
            data = json.loads(record['body'])
            res = main(data)
            response.append(res)
    else:
        return main(event)


def main(args=None):
    # load env from parent directory
    load_dotenv(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../.env"))

    try:
        logger = get_logger("parser")
    except Exception as e:
        print(f'Error initializing logger: {type(e).__name__} {e}')
        sys.exit(2)

    logger.info("APP started with")
    logger.info(f"Received {args=}")

    parser = argparse.ArgumentParser(description='Scrape player info pages.')
    parser.add_argument('-i', '--id', help="Page ID to scrape. Single int or range.", required=True)
    parser.add_argument('-v', '--verbose', help="Verbose logging.", required=False, default=False, action='store_true')

    try:
        args = parser.parse_args(args)
    except Exception as e:
        logger.critical(f'Error parsing args: {type(e).__name__} {e}')
        sys.exit(1)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug enabled")

    pages = list(map(int, map(str.strip, args.id.split('-'))))
    if len(pages) == 1:
        pages.append(pages[0])

    logger.debug(f"Will parse pages in range {pages}")

    try:
        logger.debug("Connecting to the DB")
        engine = create_engine(os.getenv("MOSBOT_MYSQL"))
        logger.debug("Connected to the DB")
    except Exception as e:
        logger.critical(f'Error initializing DB: {type(e).__name__} {e}')
        sys.exit(2)

    total = parsed = empty = error = 0
    for page_id in range(pages[0], pages[1] + 1):
        logger.debug(f"Parsing page {page_id}")
        total += 1
        try:
            parser = PlayerInfoParser(logger, engine)
            result = parser.process(page_id)
            if result:
                parsed += 1
            else:
                empty += 1
        except Exception as e:
            logger.exception(f'Error processing page {page_id}: {type(e).__name__} {e}')
            error += 1
            continue

    return {
        "range": f"{pages[0]} - {pages[1]}",
        "total": total,
        "parsed": parsed,
        "empty": empty,
        "error": error
    }


if __name__ == '__main__':
    main()
