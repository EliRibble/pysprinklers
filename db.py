import sqlalchemy
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

engine = sqlalchemy.create_engine('mysql+mysqldb://sprinklers_user:let_sprinklers_user_in@localhost/sprinklers')
Base = declarative_base()

class Sprinkler(Base):
    __tablename__ = 'sprinklers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    port = Column(String(1))
    pin  = Column(Integer)
    description = Column(String(500))

Base.metadata.create_all(engine)
