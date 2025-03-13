from datetime import datetime

from fastapi_users.db import SQLAlchemyBaseUserTableUUID

from sqlalchemy import UUID, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import ForeignKey

from app.models.base import Base, BaseSQLModel
from app.models.groups import Group
from app.models.upload import Upload


class User(SQLAlchemyBaseUserTableUUID, Base):
    # Наследуется на базе SQLAlchemyBaseUserTableUUID из fastapi_users.db
    __tablename__ = "users"
    created: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Создание роли пользователя по дефолту
    role_id: Mapped[UUID] = mapped_column(
        ForeignKey("roles.id"), nullable=True, default=None
    )
    # Роль указана в кавычках, чтобы избежать ошибки типов.
    role: Mapped["Role"] = relationship(
        "Role",
        uselist=False,
        back_populates="user",
    )
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_profiles.id"), nullable=True, default=None
    )
    # Профиль 1 к 1 с моделью пользователя
    profile: Mapped["UserProfile"] = relationship(
        "UserProfile",
        uselist=False,
        back_populates="user",
        cascade="all, delete",
    )
    # Указание на активацию пользователя в приложении
    activity: Mapped["UserActivity"] = relationship(
        "UserActivity", back_populates="user"
    )
    # Загрузка файлов
    uploads: Mapped["Upload"] = relationship(
        "Upload",
        back_populates="user",
        cascade="all, delete",
    )
    # Создание связи с group_user_link
    groups: Mapped["Group"] = relationship(
        "Group",
        secondary="group_users",
        back_populates="users",
        uselist=True,
    )

    # Строчное представление объекта
    def __repr__(self):
        return f"User(id={self.id!r}, name={self.email!r})"


class UserProfile(BaseSQLModel):
    __tablename__ = "user_profiles"
    first_name: Mapped[str] = mapped_column(String(length=120), index=True)
    last_name: Mapped[str] = mapped_column(String(length=120), index=True)
    gender: Mapped[str | None] = mapped_column(String(length=10), nullable=True)
    date_of_birth: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    city: Mapped[str | None] = mapped_column(String(length=50), nullable=True)
    country: Mapped[str | None] = mapped_column(String(length=50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(length=20), nullable=True)
    company: Mapped[str | None] = mapped_column(String(length=100), nullable=True)
    user: Mapped["User"] = relationship("User", back_populates="profile")


class Role(BaseSQLModel):
    # Роль представляет собой набор разрешений и привилегий, предоставленных пользователю.
    __tablename__ = "roles"
    role_name: Mapped[str] = mapped_column(
        String(length=200), nullable=False, unique=True
    )
    role_desc: Mapped[str | None] = mapped_column(String(length=1024), nullable=True)
    user: Mapped["User"] = relationship("User", back_populates="role")


class UserActivity(BaseSQLModel):
    # Отслеживает действия пользователей, такие как входы в систему, регистрации и другие события.
    __tablename__ = "user_activity"
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), default=None)
    activity_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    activity_type: Mapped[str] = mapped_column(String(length=200), nullable=False)
    activity_desc: Mapped[str | None] = mapped_column(
        String(length=1024), nullable=True
    )
    user: Mapped["User"] = relationship("User", back_populates="activity")
    # user: Mapped["User"] = relationship("User", back_populates="activity")
