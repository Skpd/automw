import argparse
import json
import logging
import os
import sys

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine

from mosbot.common.logger import get_logger
from mosbot.parse.login_checker import LoginChecker


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
        logger = get_logger("logins")
    except Exception as e:
        print(f'Error initializing logger: {type(e).__name__} {e}')
        sys.exit(2)

    logger.info(f"Received {args=}")

    parser = argparse.ArgumentParser(description='Check password-less logins.')
    parser.add_argument('-n', '--name', help="Player name to check.", required=True, nargs='+', action='store', type=str)
    parser.add_argument('--known-logins', help="Logins to disable bouncer.", required=False, nargs='+')
    parser.add_argument('-v', '--verbose', help="Verbose logging.", required=False, default=False, action='store_true')

    try:
        args = parser.parse_args(args)
    except Exception as e:
        logger.critical(f'Error parsing args: {type(e).__name__} {e}')
        sys.exit(1)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug enabled")

    ip = requests.get("https://checkip.amazonaws.com").text.strip()
    logger.info(f"Starting on {ip}")

    try:
        logger.debug("Connecting to the DB")
        engine = create_engine(os.getenv("MOSBOT_DB_CS"))
        logger.debug("Connected to the DB")
    except Exception as e:
        logger.critical(f'Error initializing DB: {type(e).__name__} {e}')
        sys.exit(2)

    parser = LoginChecker(logger, engine, args.known_logins)

    for name in args.name:
        # unquote name
        if name[0] == "'" and name[-1] == "'":
            name = name[1:-1]
        logger.info(f"Processing {name}")
        try:
            parser.process(name)
        except Exception as e:
            logger.error(f"Processing {name=} failed: {type(e).__name__} {e}")


if __name__ == '__main__':
    main()
