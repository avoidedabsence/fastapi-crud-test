from sqlalchemy import text
from sqlalchemy_utils import Ltree

from database.dao import Database
from database.orm import ActORM, Base, BuildORM, OrgORM, Relationship_AO
from utils.transliteration import translit_table

# NOTE: Placeholder for real data, overwrites all previous data stored in docker-mounted
# volume for Postgres


async def create_test_data():
    async with Database._engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS ltree;"))

        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with Database._sessionmaker() as session:
        builds = [
            BuildORM(addr=f"ул. Пушкина, дом {i}", lat=55.0 + i, lon=37.0 + i)
            for i in range(1, 6)
        ]
        session.add_all(builds)
        await session.flush()

        activities = [
            ActORM(
                label="Образование",
                path=Ltree("Образование".translate(translit_table)),
            ),
            ActORM(
                label="Среднее образование",
                path=Ltree("Образование.Среднее_образование".translate(translit_table)),
            ),
            ActORM(
                label="Высшее образование",
                path=Ltree("Образование.Высшее_образование".translate(translit_table)),
            ),
            ActORM(label="Медицина", path=Ltree("Медицина".translate(translit_table))),
            ActORM(
                label="Поликлиника",
                path=Ltree("Медицина.Поликлиника".translate(translit_table)),
            ),
            ActORM(
                label="Больница",
                path=Ltree("Медицина.Больница".translate(translit_table)),
            ),
        ]
        session.add_all(activities)
        await session.flush()

        orgs = []
        for i in range(10):
            org = OrgORM(
                title=f"Организация #{i + 1}",
                b_id=builds[i % len(builds)].id,
                phone=["2-222-222", "3-333-333", "8-923-666-13-13"],
            )
            orgs.append(org)
        session.add_all(orgs)
        await session.flush()

        rels = []
        for i, org in enumerate(orgs):
            rels.append(
                Relationship_AO(
                    org_id=org.id,
                    act_id=activities[i % len(activities)].id,
                ),
            )
            rels.append(
                Relationship_AO(
                    org_id=org.id,
                    act_id=activities[(i + 1) % len(activities)].id,
                ),
            )
        session.add_all(rels)

        await session.commit()
