import os
import random
from logging import Logger

import requests
from dotenv import load_dotenv
from sqlalchemy import Engine, select, create_engine, func
from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_delay, stop_after_attempt, wait_random, retry_if_exception_type, wait_fixed

from mosbot.common.db import Player, PlayerAuth
from mosbot.common.logger import get_logger


class BlacklistedError(Exception):
    ...


class LoginChecker:
    def __init__(self, logger: Logger, engine: Engine, known_logins: list[str] | None = None):
        self.logger = logger
        self.engine = engine
        self.known_logins = known_logins

    def process(self, name: str):
        available = self.check_login(name)
        self.save(name, available)

    @retry(
        stop=(stop_after_delay(10) | stop_after_attempt(5)),
        wait=wait_random(min=1, max=3)
    )
    def save(self, name: str, available: bool):
        self.logger.info(f"Saving login results for {name=} that is {available=}")
        with Session(self.engine) as session:
            try:
                player: Player = session.execute(
                    select(Player).where(Player.name == name)
                ).scalars().one()
            except (NoResultFound, MultipleResultsFound) as e:
                self.logger.error(f"Player not found with {name=}: {type(e).__name__} {e}")
                raise

            if available:
                if player.auth:
                    player.auth.email = name
                    player.auth.password = None
                else:
                    auth = PlayerAuth(player_id=player.id, email=name)
                    session.add(auth)
            else:
                if player.auth:
                    session.delete(player.auth)

            session.commit()

    @retry(
        retry=retry_if_exception_type(BlacklistedError),
        stop=stop_after_attempt(3),
        wait=wait_random(min=65, max=80)
    )
    def check_login(self, name: str) -> bool:
        known_logins = self.known_logins or self.get_random_logins(10)

        if not known_logins:
            raise Exception("Random logins not found, can't proceed.")

        random_known_login = random.choice(known_logins)
        self.logger.debug(f"Trying to login with {random_known_login}")
        response = requests.post(
            "https://www.moswar.ru/",
            data={'action': 'login', 'email': random_known_login},
            allow_redirects=False
        )
        if response.status_code == 200 and response.url == 'https://www.moswar.ru/login/':
            raise BlacklistedError()
        if response.status_code != 302:
            raise Exception(
                f"Unexpected response for known login {random_known_login}: {response.status_code=} {response.content=}"
            )
        if response.headers.get('location', None) not in ('/player/#login', "/quest/#login", "/login/"):
            raise Exception(
                f"Unexpected response for known login {random_known_login} ({response.url=}): {response.status_code=} {response.headers=}"
            )
        if response.headers.get('location', None) == "/login/":
            raise BlacklistedError()

        self.logger.debug("Bouncer not active yet")
        self.logger.debug(f"Trying to login with {name}")
        response = requests.post(
            "https://www.moswar.ru/",
            data={'action': 'login', 'email': name},
            allow_redirects=False
        )
        if response.status_code != 302:
            raise Exception(
                f"Unexpected response for '{random_known_login}': {response.status_code} {response.content}"
            )

        if response.headers.get("location", None) in ('/player/#login', "/quest/#login"):
            self.logger.debug("Accepted")
            return True
        elif response.headers.get("location", None) == "/login/":
            self.logger.debug("Rejected")
            return False
        else:
            raise Exception(
                f"Unexpected response for '{random_known_login}': {response.status_code} {response.headers}"
            )

    def get_random_logins(self, max_size) -> list[str]:
        with Session(self.engine) as session:
            logins = session.execute(
                select(PlayerAuth.email)
                .where(PlayerAuth.password == None)
                .order_by(func.random())
                .limit(max_size)
            ).scalars().all()

            return logins


if __name__ == "__main__":
    # load env from parent directory
    load_dotenv(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../.env"))

    _logger = get_logger("parser", verbose=True)
    _engine = create_engine(os.getenv("MOSBOT_DB_CS"))

    # parser = LoginChecker(_logger, _engine, ["BurnHorizon", "GALYASTACY"])
    parser = LoginChecker(_logger, _engine)

    parser.process("huh")
    parser.process("negavoid2")
