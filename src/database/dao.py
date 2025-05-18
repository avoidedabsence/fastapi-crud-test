from typing import List

from geoalchemy2 import Geography
from loguru import logger
from sqlalchemy import cast, func, update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy_utils import Ltree

from database.models import (
    ActivityIn,
    BuildingDelete,
    BuildingIn,
    BuildingUpdate,
    OrganizationDelete,
    OrganizationIn,
    OrganizationUpdate,
)
from database.orm import ActORM, BuildORM, OrgORM, Relationship_AO
from utils.transliteration import translit_table


class Database:
    _engine = None
    _sessionmaker = None

    @classmethod
    async def init(cls, db_url: str, max_conn: int):
        cls._engine = create_async_engine(db_url, echo=False, pool_size=max_conn)
        cls._sessionmaker = async_sessionmaker(cls._engine, expire_on_commit=False)
        async with cls._engine.begin() as conn:
            """await conn.execute(text(
                "CREATE EXTENSION IF NOT EXISTS ltree;"  Генерируется в generate_test_data, при проде нужно вернуть
            ))
            await conn.run_sync(Base.metadata.create_all)"""
        logger.info(
            "[+] Database engine initialized with max {} connections;",
            max_conn,
        )
        return cls._engine

    @classmethod
    async def close(cls):
        if cls._engine:
            await cls._engine.dispose()
            logger.info("[+] Database engine successfully closed;")

    @classmethod
    async def get_organization_by_id(cls, org_id: int) -> OrgORM | None:
        async with cls._sessionmaker() as session:
            stmt = (
                select(OrgORM)
                .where(OrgORM.id == org_id)
                .options(selectinload(OrgORM.activities), joinedload(OrgORM.building))
            )

            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @classmethod
    async def get_organizations_by_bid(cls, building_id: int) -> List[OrgORM] | None:
        async with cls._sessionmaker() as session:
            stmt = (
                select(OrgORM)
                .where(OrgORM.b_id == building_id)
                .options(selectinload(OrgORM.activities), joinedload(OrgORM.building))
            )

            result = await session.execute(stmt)
            return result.scalars().all() if result else None

    @classmethod
    async def get_organizations_by_activity(
        cls,
        label: str,
        strict: bool = False,
    ) -> List[OrgORM] | None:
        async with cls._sessionmaker() as session:
            if strict:
                stmt = (
                    select(OrgORM)
                    .join(OrgORM.activities)
                    .options(
                        selectinload(OrgORM.activities),
                        joinedload(OrgORM.building),
                    )
                    .where(ActORM.label == label)
                )
            else:
                parent_path = (
                    await session.execute(
                        select(ActORM.path).where(ActORM.label == label),
                    )
                ).scalar_one_or_none()

                if parent_path is None:
                    return None

                allowed_act_ids = (
                    (
                        await session.execute(
                            select(ActORM.id).where(
                                ActORM.path.descendant_of(parent_path),
                            ),
                        )
                    )
                    .scalars()
                    .all()
                )

                stmt = (
                    select(OrgORM)
                    .join(OrgORM.activities)
                    .options(
                        selectinload(OrgORM.activities),
                        joinedload(OrgORM.building),
                    )
                    .where(ActORM.id.in_(allowed_act_ids))
                )

            result = await session.execute(stmt)
            return result.scalars().all() if result else None

    @classmethod
    async def search_for_organizations(cls, query: str) -> List[OrgORM] | None:
        async with cls._sessionmaker() as session:
            stmt = (
                select(OrgORM)
                .where(OrgORM.title.ilike(f"%{query}%"))
                .options(selectinload(OrgORM.activities), joinedload(OrgORM.building))
            )

            result = await session.execute(stmt)
            return result.scalars().all() if result else None

    @classmethod
    async def organizations_within_radius(
        cls,
        lat: float,
        lon: float,
        radius: float,
    ) -> List[OrgORM] | None:
        async with cls._sessionmaker() as session:
            stmt = (
                select(OrgORM)
                .join(BuildORM, BuildORM.id == OrgORM.b_id)
                .options(joinedload(OrgORM.building), selectinload(OrgORM.activities))
                .where(
                    func.ST_DWithin(
                        cast(
                            func.ST_SetSRID(
                                func.ST_MakePoint(BuildORM.lon, BuildORM.lat),
                                4326,
                            ),
                            Geography,
                        ),
                        cast(
                            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
                            Geography,
                        ),
                        radius,
                    ),
                )
                .options(selectinload(OrgORM.activities))
            )

            result = await session.execute(stmt)

            return result.scalars().all() if result else None

    @classmethod
    async def buildings_within_radius(
        cls,
        lat: float,
        lon: float,
        radius: float,
    ) -> List[BuildORM] | None:
        async with cls._sessionmaker() as session:
            stmt = (
                select(BuildORM)
                .where(
                    func.ST_DWithin(
                        cast(
                            func.ST_SetSRID(
                                func.ST_MakePoint(BuildORM.lon, BuildORM.lat),
                                4326,
                            ),
                            Geography,
                        ),
                        cast(
                            func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326),
                            Geography,
                        ),
                        radius,
                    ),
                )
                .options(selectinload(BuildORM.orgs))
            )

            result = await session.execute(stmt)

            return result.scalars().all() if result else None

    @classmethod
    async def create_organization(cls, org_model: OrganizationIn) -> OrgORM:
        async with cls._sessionmaker() as session:
            try:
                org_obj = OrgORM(
                    title=org_model.title,
                    phone=org_model.phone,
                    b_id=org_model.building_id,
                )

                session.add(org_obj)
                await session.commit()
                await session.refresh(org_obj)

                org_id = org_obj.id

                rels = []

                for act_id in org_model.activity_ids:
                    rels.append(Relationship_AO(org_id=org_id, act_id=act_id))

                session.add_all(rels)

                await session.commit()
                await session.refresh(
                    org_obj,
                    attribute_names=["building", "activities"],
                )

                return org_obj
            except Exception as e:
                await session.rollback()
                print(e, e.args, e.__traceback__)
                raise e

    @classmethod
    async def create_building(cls, b_model: BuildingIn) -> BuildORM:
        async with cls._sessionmaker() as session:
            try:
                build_obj = BuildORM(
                    addr=b_model.addr,
                    lat=b_model.lat,
                    lon=b_model.lon,
                )

                session.add(build_obj)
                await session.commit()
                await session.refresh(build_obj)

                build_id = build_obj.id

                rels = []

                stmt = update(OrgORM).where(OrgORM.title.in_(b_model.organizations)).values(b_id=build_id)

                await session.execute(stmt)
                await session.commit()
                await session.refresh(build_obj, attribute_names=["orgs"])

                return build_obj
            except Exception as e:
                await session.rollback()
                raise e

    @classmethod
    async def create_activity(cls, act_mod: ActivityIn) -> ActORM:
        async with cls._sessionmaker() as session:
            try:
                parent = None

                for raw_label in act_mod.labels:
                    vertice = raw_label.translate(translit_table)

                    if parent is None:
                        stmt = select(ActORM).where(
                            ActORM.label == raw_label,
                            func.nlevel(ActORM.path) == 1,
                        )
                    else:
                        stmt = select(ActORM).where(
                            ActORM.label == raw_label,
                            ActORM.path.descendant_of(parent.path),
                        )

                    result = await session.execute(stmt)

                    try:
                        if parent is not None:
                            node = result.scalars().all()
                            node = list(
                                filter(
                                    lambda x: len(parent.path) + 1 == len(x.path),
                                    result,
                                ),
                            )
                            print(node)
                            if not node:
                                raise NoResultFound
                        else:
                            node = result.scalars().one()
                    except NoResultFound:
                        node = ActORM(label=raw_label)
                        if parent is None:
                            node.path = Ltree(vertice)
                        else:
                            node.path = Ltree(f"{parent.path}.{vertice}")
                        session.add(node)
                        await session.flush()
                    print(node.path, " NODE")
                    parent = node
                await session.commit()
                return parent
            except Exception as e:
                await session.rollback()
                print(e, e.__traceback__)
                raise e

    @classmethod
    async def delete_organization(cls, org_mod: OrganizationDelete):
        async with cls._sessionmaker() as session:
            try:
                await session.delete(await session.get(OrgORM, org_mod.id))
                await session.commit()
                return True
            except Exception:
                return False

    @classmethod
    async def delete_building(cls, build_mod: BuildingDelete):
        async with cls._sessionmaker() as session:
            try:
                await session.delete(await session.get(BuildORM, build_mod.id))
                await session.commit()
                return True
            except Exception:
                return False

    @classmethod
    async def update_organization(cls, org_mod: OrganizationUpdate):
        async with cls._sessionmaker() as session:
            org_obj = (
                await session.execute(
                    select(OrgORM).where(OrgORM.id == org_mod.id).options(selectinload(OrgORM.activities)),
                )
            ).scalar_one_or_none()

            if org_obj is None:
                raise IndexError("id is invalid")

            for k, v in org_mod.dict().items():
                if k in ("activity_ids", "id") or v is None:
                    continue
                setattr(org_obj, k, v)

            if org_mod.activity_ids:
                old_ids, new_ids = (
                    set([act_obj.id for act_obj in org_obj.activities]),
                    set(org_mod.activity_ids),
                )

                to_del, to_add = list(old_ids - new_ids), list(new_ids - old_ids)

                to_del_obj = (
                    (
                        await session.execute(
                            select(Relationship_AO).where(
                                Relationship_AO.org_id == org_obj.id,
                                Relationship_AO.act_id.in_(to_del),
                            ),
                        )
                    )
                    .scalars()
                    .all()
                )

                to_add_obj = []

                for act_id in to_add:
                    to_add_obj.append(Relationship_AO(org_id=org_obj.id, act_id=act_id))

                for obj in to_del_obj:
                    await session.delete(obj)
                await session.flush()

                session.add_all(to_add_obj)

            await session.commit()
            await session.refresh(org_obj, attribute_names=["building", "activities"])

            return org_obj

    @classmethod
    async def update_building(cls, build_mod: BuildingUpdate):
        async with cls._sessionmaker() as session:
            build_obj = await session.get(BuildORM, build_mod.id)
            if not build_obj:
                raise IndexError("id is invalid")

            for k, v in build_mod.dict().items():
                if k == "id" or v is None:
                    continue
                setattr(build_obj, k, v)

            await session.commit()
            await session.refresh(build_obj, attribute_names=["orgs"])

            return build_obj
