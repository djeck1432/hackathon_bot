from uuid import uuid4

from sqlalchemy import UUID, Column, MetaData, String
from sqlalchemy.orm import DeclarativeBase, Mapped


class Base(DeclarativeBase):
    """
    Base class for ORM models.

    :ivar id: The unique identifier of the entity.
    """

    id: Mapped[UUID] = Column(UUID, default=uuid4, primary_key=True)
    metadata = MetaData()


class Repository(Base):
    """
    Represents a GitHub repository in the tracker system.

    Attributes:
        __tablename__ (str): The name of the database table for SQLAlchemy ORM.
        name (Column): The name of the repository, indexed and unique, used to identify it.
        author (Column): The author or owner of the repository, indexed for faster querying.
        link (Column): The URL link to the repository, indexed for quick access.

    Methods:
        __str__() -> str: Returns a string representation of the repository in the format 'author/name'.
    """

    __tablename__ = "tracker_repository"

    name = Column(String, index=True, nullable=False, unique=True)
    author = Column(String, index=True, nullable=False)
    link = Column(String, index=True, nullable=False)

    def __str__(self) -> str:
        """
        Returns a string representation of the repository in the format 'author/name'.
        :return: str
        """
        return f"{self.author}/{self.name}"
