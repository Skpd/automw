import enum
from os import getenv
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, Boolean, Enum
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class FractionEnum(enum.Enum):
    npc = 'npc'
    arrived = 'arrived'
    resident = 'resident'


class BaseModel(DeclarativeBase):
    pass


class Player(BaseModel):
    __tablename__ = "player"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)

    fraction: Mapped[int] = mapped_column(Enum(FractionEnum))
    name: Mapped[str] = mapped_column(String(50))
    level: Mapped[int] = mapped_column(Integer)
    coolness: Mapped[int] = mapped_column(Integer)
    hp_current: Mapped[int] = mapped_column(Integer)
    hp_max: Mapped[int] = mapped_column(Integer)

    health: Mapped[int] = mapped_column(Integer)
    strength: Mapped[int] = mapped_column(Integer)
    dexterity: Mapped[int] = mapped_column(Integer)
    resistance: Mapped[int] = mapped_column(Integer)
    intuition: Mapped[int] = mapped_column(Integer)
    attention: Mapped[int] = mapped_column(Integer)
    charism: Mapped[int] = mapped_column(Integer)

    respect: Mapped[int] = mapped_column(Integer)
    referrals: Mapped[int] = mapped_column(Integer)
    wins: Mapped[int] = mapped_column(Integer)
    stolen: Mapped[int] = mapped_column(Integer)
    blocked: Mapped[bool] = mapped_column(Boolean)

    clan_id: Mapped[Optional[int]] = mapped_column(Integer)

    def __repr__(self) -> str:
        return f"Player(id={self.id!r})"


class PlayerPage(BaseModel):
    __tablename__ = "player_page"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    status: Mapped[str] = mapped_column(String(30))
    player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("player.id"))
    player: Mapped["Player"] = relationship()

    def __repr__(self) -> str:
        return f"PlayerPage(id={self.id!r}, status={self.status!r}), player_id={self.player_id}"


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    engine = create_engine(getenv("MOSBOT_DB_CS"), echo=True)
    BaseModel.metadata.create_all(engine)
