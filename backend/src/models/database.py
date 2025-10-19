from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from config import Config
from src.models.schemas import Base

class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or Config.DATABASE_URL
        self.engine = create_engine(
            self.database_url,
            connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(bind=self.engine)
        
    def drop_tables(self):
        """Drop all tables in the database"""
        Base.metadata.drop_all(bind=self.engine)
        
    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def get_session_direct(self) -> Session:
        """Get a session without context manager (manual cleanup required)"""
        return self.SessionLocal()


# Global database manager instance
db_manager = DatabaseManager()


def init_db():
    """Initialize the database"""
    db_manager.create_tables()
    print("✅ Database initialized successfully!")


def get_db() -> Session:
    """Dependency for getting database sessions"""
    db = db_manager.get_session_direct()
    try:
        yield db
    finally:
        db.close()