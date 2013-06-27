import datetime
import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base

engine = sqlalchemy.create_engine('mysql+mysqldb://sprinklers_user:let_sprinklers_user_in@localhost/sprinklers')
Base = declarative_base()

class Sprinkler(Base):
    __tablename__ = 'sprinklers'
    
    id          = Column(Integer, primary_key=True)
    name        = Column(String(100))
    port        = Column(String(1))
    pin         = Column(Integer)
    description = Column(String(500))

    def __repr__(self):
        return "Sprinkler {0} ({1}-{2}{3})".format(self.name, self.id, self.port, self.pin)

class SprinklerStateChange(Base):
    __tablename__ = 'sprinkler_state_change'

    id              = Column(Integer, primary_key=True)
    state           = Column(Boolean)
    at              = Column(DateTime)
    sprinkler_id    = Column(Integer, ForeignKey('sprinklers.id'))
    sprinkler       = relationship('Sprinkler', backref=backref('events', order_by=at))

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def create_state_change_record(sprinkler, state):
    session = Session()
    session.add(SprinklerStateChange(
        state=state,
        at=datetime.datetime.utcnow(),
        sprinkler=sprinkler))
    session.commit()
    session.close()
