from typing import List

from sqlalchemy import ForeignKey, Sequence, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy_utils import Ltree, LtreeType


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Relationship_AO(Base):
    __tablename__ = "rel_ao"

    org_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    act_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"),
        primary_key=True,
    )


class ActORM(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Sequence("activities_id_seq"), primary_key=True)
    label: Mapped[str] = mapped_column(nullable=False)
    path: Mapped[Ltree] = mapped_column(LtreeType, nullable=False, index=True)

    orgs: Mapped[List["OrgORM"]] = relationship(
        secondary="rel_ao",
        back_populates="activities",
    )


class BuildORM(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Sequence("buildings_id_seq"), primary_key=True)
    addr: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    lat: Mapped[float] = mapped_column(nullable=False)
    lon: Mapped[float] = mapped_column(nullable=False)

    orgs: Mapped[List["OrgORM"]] = relationship(
        back_populates="building",
        cascade="all, delete-orphan",
    )


class OrgORM(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Sequence("organizations_id_seq"), primary_key=True)
    title: Mapped[str] = mapped_column(unique=True, nullable=False)
    phone: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(JSONB),
        nullable=False,
    )

    b_id: Mapped[int] = mapped_column(
        ForeignKey("buildings.id", ondelete="CASCADE", onupdate="RESTRICT"),
        nullable=False,
    )

    building: Mapped["BuildORM"] = relationship(back_populates="orgs")

    activities: Mapped[List["ActORM"]] = relationship(
        secondary="rel_ao",
        back_populates="orgs",
    )
