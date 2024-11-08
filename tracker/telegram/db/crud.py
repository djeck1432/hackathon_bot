from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .database import SQLALCHEMY_DATABASE_URL
from .models import Base, Repository


class DBConnector:
    """
    Provides database connection and operations management using SQLAlchemy
    in an Aiogram application context.

    Methods:
    - get_all_repositories() Returns a list of all repositories in the database
    """

    def __init__(self, db_url: str = SQLALCHEMY_DATABASE_URL) -> None:
        """
        Initialize the database connection and session factory.
        :param db_url: str = None
        """
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def get_all_repositories(self, model: Base = Repository) -> list[Base]:
        """
        Returns a list of all repositories in the database
        :param model: Base = Repository
        :return: list[Base]
        """
        db = self.Session()
        try:
            return db.query(model).all()

        finally:
            db.close()
