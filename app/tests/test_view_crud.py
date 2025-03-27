import pytest
from sqlalchemy import select

from app.database.base import Base, engine, async_session_maker
from app.models.users import Role


@pytest.fixture(scope="module")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session = async_session_maker()
    yield session
    await session.rollback()
    await session.close()


@pytest.fixture(scope="module")
def valid_role():
    return Role(role_name="Developer")


class TestRole:
    async def test_author_valid(self, db_session, valid_role):
        async with db_session() as session:
            await session.add(valid_role)
            session.commit()
            obj = await session.execute(select(Role).filter_by(role_name="Developer"))
            result = obj.scalars().first()
            assert result.role_name == "Developer"
