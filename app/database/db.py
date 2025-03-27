from typing import Annotated, AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.password import PasswordHelper
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import async_session_maker
from app.models.users import User


async def create_db_and_tables():
    async with async_session_maker() as session:
        password_helper = PasswordHelper()
        # Проверка того, что суперпользователь уже создан для данной электронной почты
        select_stmt = select(User).where(User.email == "superuser@admin.com")

        # Запрос к базе данных для выполнения входа
        query = await session.execute(select_stmt)
        user = User(
            email="superuser@admin.com",
            hashed_password=password_helper.hash("password123"),
            is_superuser=True,
            is_active=True,
        )
        if not query.scalars().first():
            logger.info(
                f"Суперпользователь создан... email: {user.email}"
            )
            session.add(user)
            await session.commit()
        else:
            logger.info(
                f"Вход под учетной записью суперпользователя... email: {user.email}"
            )


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


CurrentAsyncSession = Annotated[AsyncSession, Depends(get_async_session)]
