from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


SQLALCHEMY_DATABASE_URL = "sqlite:///./articles.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


user_scopes = Table(
    "user_scopes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("scope_id", Integer, ForeignKey("scopes.id")),
)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    scopes = relationship("Scope", secondary=user_scopes, back_populates="users")

class Scope(Base):
    __tablename__ = "scopes"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    users = relationship("User", secondary=user_scopes, back_populates="scopes")

class Article(Base):
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    is_published = Column(Boolean, default=False)
