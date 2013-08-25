import datetime
import sqlalchemy
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, exc, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.pool import Pool
from contextlib import contextmanager

engine = sqlalchemy.create_engine('mysql+mysqldb://sprinklers_user:let_sprinklers_user_in@localhost/sprinklers')
Base = declarative_base()

@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except:
        # optional - dispose the whole pool
        # instead of invalidating one at a time
        # connection_proxy._pool.dispose()

        # raise DisconnectionError - pool will try
        # connecting again up to three times before raising.
        raise exc.DisconnectionError()
    cursor.close()

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

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def create_state_change_record(session, sprinkler, state):
    session.add(SprinklerStateChange(
        state=state,
        at=datetime.datetime.utcnow(),
        sprinkler=sprinkler))

def get_sprinkler(session, sprinkler_id):
    try:
        i = int(sprinkler_id)
        sprinkler = session.query(Sprinkler).filter_by(id=i).one()
    except (ValueError, IndexError):
        try:
            sprinkler = session.query(Sprinkler).filter_by(name=sprinkler_id).one()
        except IndexError:
            raise DBException("No sprinkler with id '%s'", sprinkler_id)

    return sprinkler

def get_sprinklers(session):
    sprinklers = session.query(Sprinkler).order_by(Sprinkler.id).all()
    return sprinklers

class SprinklerRun(object):
    def __init__(self, on, off):
        self.on = on.at
        self.off = off.at

    def __repr__(self):
        return "Run at {0} for {1}".format(self.at, self.duration)

    @property
    def duration(self):
        return self.off - self.on

    @property
    def at(self):
        return self.on

def get_last_ran(session, sprinkler_id):
    last_on = session.query(SprinklerStateChange).order_by(sqlalchemy.desc(SprinklerStateChange.at)).filter_by(sprinkler_id=sprinkler_id, state=True).first()
    last_off = session.query(SprinklerStateChange).order_by(sqlalchemy.desc(SprinklerStateChange.at)).filter_by(sprinkler_id=sprinkler_id, state=False).first()
    return SprinklerRun(last_on, last_off)

def get_runs(session, sprinkler_id, count=10):
    runs = []
    on = None
    off = None
    for state_change in session.query(SprinklerStateChange).order_by(sqlalchemy.desc(SprinklerStateChange.at)).filter_by(sprinkler_id=sprinkler_id)[:count*2]:
        if state_change.state:
            on = state_change
        else:
            off = state_change
        if on is not None and off is not None:
            runs.append(SprinklerRun(on, off))
            on = None
            off = None
    return runs
