import datetime
import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base

engine = sqlalchemy.create_engine('mysql+mysqldb://sprinklers_user:let_sprinklers_user_in@localhost/sprinklers')
Base = declarative_base()

class DBException(Exception):
    pass

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

class Schedule(Base):
    __tablename__ = 'schedule'
    
    id          = Column(Integer, primary_key=True)
    name        = Column(String(100))
    
class ScheduleEntry(Base):
    __tablename__ = 'schedule_entry'

    id              = Column(Integer, primary_key=True)
    index           = Column(Integer)
    group           = Column(Integer)

    schedule_id     = Column(Integer, ForeignKey('schedule.id'))
    schedule        = relationship('Schedule', backref=backref('entries', order_by=index))

    sprinkler_id    = Column(Integer, ForeignKey('sprinklers.id'))
    sprinkler       = relationship('Sprinkler', backref=backref('schedule_entries', order_by=id))

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

def get_sprinkler(sprinkler_id):
    session = Session()
    try:
        i = int(sprinkler_id)
        sprinkler = session.query(Sprinkler).filter_by(id=i).one()
    except (ValueError, IndexError):
        try:
            sprinkler = session.query(Sprinkler).filter_by(name=sprinkler_id).one()
        except IndexError:
            raise DBException("No sprinkler with id '%s'", sprinkler_id)

    session.close()
    return sprinkler

def get_sprinklers():
    session = Session()
    sprinklers = session.query(Sprinkler).order_by(Sprinkler.id).all()
    session.close()
    return sprinklers
