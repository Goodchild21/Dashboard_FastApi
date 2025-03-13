import os
import sys

import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))
sys.path.append(BASE_DIR)


class Base(DeclarativeBase):
    metadata: sqlalchemy.MetaData = sqlalchemy.MetaData()


DATABASE_URL = os.environ["DATABASE_URL"]


engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


def init_models():
    from ..models.groups import Group, Permission, UserGroupLink  # noqa: F401
    from ..models.upload import Upload  # noqa: F401
    from ..models.users import Role, User, UserActivity  # noqa: F401
