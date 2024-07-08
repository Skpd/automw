import logging
import re
from dataclasses import dataclass
import os
from time import time

from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, select, Engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from tenacity import retry, stop_after_delay, stop_after_attempt, wait_random

from mosbot.common.db import PlayerPage, Player
from mosbot.common.logger import get_logger


@dataclass
class PlayerInfo:
    player_id: int
    fraction: str
    name: str
    level: int
    coolness: int
    hp_current: int
    hp_max: int

    health: int
    strength: int
    dexterity: int
    resistance: int
    intuition: int
    attention: int
    charism: int  # intentional typo to have 1-1 match with the source

    respect: int
    referrals: int
    wins: int
    stolen: int
    blocked: bool

    clan_id: int = None


class PlayerInfoParser:
    def __init__(self, logger: logging.Logger, engine: Engine):
        self.logger = logger
        self.engine = engine

    def get_contents(self, url) -> bytes:
        start_time = time()
        response = requests.get(url)
        end_time = time()

        self.logger.info(f"Processed {url=} in {end_time - start_time}")

        if response.status_code != 200:
            self.logger.error(f"Unexpected code {response.status_code}: {response.text}")
            raise Exception("Failed to get contents")

        return response.content

    def parse_player(self, contents: bytes) -> PlayerInfo | None:
        start_time = time()
        soup = BeautifulSoup(contents, 'html.parser')
        end_time = time()
        self.logger.info(f"Loaded HTML contents in {end_time - start_time}")

        start_time = time()
        player_info = soup.select_one("#pers-player-info")
        if not player_info:
            return None

        coolness = int(player_info.select_one(".cool-1 > .cool-1").text)
        fraction = player_info.select_one(".user i").attrs.get("class", "")[0]
        clan = player_info.select('.user a[href^="/clan/"]')
        clan_id = int(clan[0].attrs.get("href", "")[6:-1]) if clan else None
        player_id = int(player_info.select_one('.user a[href^="/player/"]').get("href", "")[8:-1])
        name = player_info.select_one('.user a[href^="/player/"]').text
        level = int(player_info.select_one('.user .level').text[1:-1])
        hp_current = int(player_info.select_one('.life > .currenthp').text)
        hp_max = int(player_info.select_one('.life > .maxhp').text)

        player_statistics = player_info.select_one(".pers-statistics")
        respect = int(re.sub("[^0-9]", "", player_statistics.select_one(".numbers li:nth-child(1)").text))
        referrals = int(re.sub("[^0-9]", "", player_statistics.select_one(".numbers li:nth-child(2)").text))
        wins = int(re.sub("[^0-9]", "", player_statistics.select_one(".numbers li:nth-child(3)").text))
        stolen = int(re.sub("[^0-9]", "", player_statistics.select_one(".numbers li:nth-child(4)").text))

        stats = player_info.select("#stats-accordion .stats .stat .num")
        health = int(stats[0].text)
        strength = int(stats[1].text)
        dexterity = int(stats[2].text)
        resistance = int(stats[3].text)
        intuition = int(stats[4].text)
        attention = int(stats[5].text)
        charism = int(stats[6].text)

        blocked = True if player_info.select_one(".blocked") else False

        result = PlayerInfo(
            player_id=player_id,
            fraction=fraction,
            name=name,
            level=level,
            coolness=coolness,
            hp_current=hp_current,
            hp_max=hp_max,
            health=health,
            strength=strength,
            dexterity=dexterity,
            resistance=resistance,
            intuition=intuition,
            attention=attention,
            charism=charism,
            respect=respect,
            referrals=referrals,
            wins=wins,
            stolen=stolen,
            blocked=blocked,
            clan_id=clan_id
        )
        end_time = time()
        self.logger.info(f"Parsed items in {end_time - start_time}")
        return result

    @retry(
        stop=(stop_after_delay(10) | stop_after_attempt(5)),
        wait=wait_random(min=1, max=3)
    )
    def save_results(self, page_id, status, incoming_player: PlayerInfo | None) -> None:
        self.logger.info(f"Saving results for {page_id=} with {status=} and {incoming_player=}")
        with Session(self.engine) as session:
            try:
                player = session.execute(
                    select(Player).where(Player.id == page_id)
                ).scalars().one()
            except NoResultFound:
                if incoming_player:
                    self.logger.info(f"Player {page_id=} not found, creating one")
                    player = Player(id=page_id)
                else:
                    self.logger.info(f"Player {page_id=} not found, and we don't need it")
                    player = None
            except MultipleResultsFound:
                self.logger.error(f"Unexpected number of pages found for {page_id=}")
                raise

            try:
                page = session.execute(
                    select(PlayerPage).where(PlayerPage.id == page_id)
                ).scalars().one()
            except NoResultFound:
                self.logger.info(f"Page {page_id=} not found, creating one")
                page = PlayerPage(id=page_id)
            except MultipleResultsFound:
                self.logger.error(f"Unexpected number of pages found for {page_id=}")
                raise

            self.logger.info(f"{type(player)} {player=}")

            if incoming_player:
                player.fraction = incoming_player.fraction
                player.name = incoming_player.name
                player.level = incoming_player.level
                player.coolness = incoming_player.coolness
                player.hp_current = incoming_player.hp_current
                player.hp_max = incoming_player.hp_max
                player.health = incoming_player.health
                player.strength = incoming_player.strength
                player.dexterity = incoming_player.dexterity
                player.resistance = incoming_player.resistance
                player.intuition = incoming_player.intuition
                player.attention = incoming_player.attention
                player.charism = incoming_player.charism
                player.respect = incoming_player.respect
                player.referrals = incoming_player.referrals
                player.wins = incoming_player.wins
                player.stolen = incoming_player.stolen
                player.blocked = incoming_player.blocked
                player.clan_id = incoming_player.clan_id

            page.status = status
            page.player = player

            session.add(page)
            if player:
                session.add(player)

            session.commit()

    def process(self, page_id) -> PlayerInfo | None:
        try:
            contents = self.get_contents(f"https://www.moswar.ru/player/{page_id}/")
        except Exception as e:
            self.save_results(page_id, "get_error", None)
            raise e

        try:
            player = self.parse_player(contents)
        except Exception as e:
            self.save_results(page_id, "parse_error", None)
            raise e

        self.save_results(page_id, "ok", player)
        return player


if __name__ == "__main__":
    # load env from parent directory
    load_dotenv(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.env"))

    logger = get_logger("parser")
    _engine = create_engine(os.getenv("MOSBOT_DB_CS"), echo=True)

    parser = PlayerInfoParser(logger, _engine)

    parser.process(7387684)
    parser.process(6531)
    parser.process(100500)
