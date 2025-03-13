import uuid
from typing import Generic, Type, TypeVar

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.database.base import Base
from app.database.db import CurrentAsyncSession

ModelType = TypeVar("ModelType", bound=Base)
PydanticCreateModelType = TypeVar("PydanticCreateModelType", bound=BaseModel)
PydanticUpdateModelType = TypeVar("PydanticUpdateModelType", bound=BaseModel)
IdentifierType = TypeVar("IdentifierType")


class BaseCRUD(Generic[ModelType, PydanticCreateModelType, PydanticUpdateModelType]):
    def __init__(
        self,
        db_model: Type[ModelType],
        pydantic_create_model: Type[PydanticCreateModelType],
        pydantic_update_model: Type[PydanticUpdateModelType],
    ):
        self.db_model = db_model
        self.pydantic_create_model = pydantic_create_model
        self.pydantic_update_model = pydantic_update_model

    async def create(
        self,
        item: PydanticCreateModelType,
        db: CurrentAsyncSession,
    ) -> ModelType:
        db_item = self.db_model(**item.dict())
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item

    async def read_all(self, db: CurrentAsyncSession, skip: int, limit: int):
        # Запрос модели базы данных с использованием SQLAlchemy select()
        stmt = select(self.db_model).offset(skip).limit(limit)
        query = await db.execute(stmt)
        # Добавление исключения, которое будет вызвано в случае, если запись не существует
        if not query:
            raise HTTPException(status_code=404, detail="Запись не найдена")
        return query.scalars().all()

    # Чтение одной записи из модели базы данных
    async def read(self, db: CurrentAsyncSession, id: uuid.UUID) -> ModelType | None:
        stmt = select(self.db_model).where(self.db_model.id == id)
        query = await db.execute(stmt)
        if not query:
            raise HTTPException(status_code=404, detail=f"Запись {id} не найдена")
        return query.scalar_one_or_none()

    # Добавление функции для обновления записи
    async def update(
        self, db: CurrentAsyncSession, id: uuid.UUID, item: PydanticUpdateModelType
    ) -> ModelType | None:
        stmt = select(self.db_model).where(self.db_model.id == id)
        query = await db.execute(stmt)
        if not query:
            raise HTTPException(status_code=404, detail=f"Запись {id} не найдена")
        db_item = query.scalar_one()
        if db_item:
            for key, value in item.dict().items():
                setattr(db_item, key, value)
            await db.commit()
            await db.refresh(db_item)
            return db_item

    # Добавление модели для удаления записи
    async def delete(
        self,
        db: CurrentAsyncSession,
        id: uuid.UUID,
    ):
        stmt = select(self.db_model).where(self.db_model.id == id)
        query = await db.execute(stmt)
        if not query:
            raise HTTPException(status_code=404, detail=f"Запись {id} не найдена")
        db_item = query.scalar_one()
        if db_item:
            await db.delete(db_item)
            await db.commit()
            return db_item
