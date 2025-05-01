import logging

logger = logging.getLogger(__name__)


import re
from typing import Any

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import as_declarative

from definitions.custom_scripts.schemas import add_table_schema_to_model
from tests.structure.STG import *

__version__ = "1.0.0"  # Не менять, работает автоматика


@as_declarative()
class Base:
    """Base class for all database entities"""

    @classmethod
    @declared_attr  # type: ignore
    def __tablename__(cls) -> str:
        """Generate database table name automatically.
        Convert CamelCase class name to snake_case db table name.
        """
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()

    @classmethod
    @declared_attr  # type: ignore
    def __table_args__(cls) -> dict[str, Any]:
        schema = f'{cls.__module__.split(".")[-2].upper()}_{cls.__module__.split(".")[-1].upper()}'
        add_table_schema_to_model(schema, Base.metadata)  # type: ignore

        return {"schema": schema, "comment": cls.__doc__, "info": {"sensitive": False}}

    def __repr__(self) -> str:
        attrs = []
        for c in self.__table__.columns:  # type: ignore
            attrs.append(f"{c.name}={getattr(self, c.name)}")
        return "{}({})".format(self.__class__.__name__, ", ".join(attrs))


class SensitiveBase(Base):
    """Base class for all sensitive entities"""

    @classmethod
    @declared_attr  # type: ignore
    def __table_args__(cls) -> dict[str, Any]:
        schema = f'{cls.__module__.split(".")[-2].upper()}_{cls.__module__.split(".")[-1].upper()}'
        add_table_schema_to_model(schema, Base.metadata)  # type: ignore

        return {"schema": schema, "comment": cls.__doc__, "info": {"sensitive": True}}

    __abstract__ = True
    __mapper_args__ = {"concrete": True}
