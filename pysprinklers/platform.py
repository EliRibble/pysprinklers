import boto.ses
import db
import functools
import logging
import time
import threading
import ubw
import glib

LOGGER = logging.getLogger('platform')

DATETIME_PATTERN = '%Y-%m-%d %H:%M:%S'
configuration = None
def configure(config):
    global configuration
    configuration = config

def get_sprinklers():
    with db.session_scope() as session:
        sprinklers = db.get_sprinklers(session)
        data = [{
            'id'    : sprinkler.id,
            'name'  : sprinkler.name,
            'port'  : sprinkler.port,
            'pin'   : sprinkler.pin,
            'description'   : sprinkler.description
        } for sprinkler in sprinklers]
    return data

def _get_last_ran(session, sprinkler_id):
    last = db.get_last_ran(session, sprinkler_id)
    return {
        'at'        : last.at.strftime(DATETIME_PATTERN),
        'duration'  : last.duration.seconds,
    }

def get_status():
    with db.session_scope() as session:
        sprinklers = db.get_sprinklers(session)
        states = ubw.get_status()
        statuses = {}
        for sprinkler in sprinklers:
            status = {
                'state'     : 'on' if states[sprinkler.port][sprinkler.pin] else 'off',
                'last_ran'  : _get_last_ran(session, sprinkler.id)
            }
            statuses[sprinkler.name] = status
    return statuses

def get_history(sprinkler_id):
    with db.session_scope() as session:
        sprinkler = db.get_sprinkler(session, sprinkler_id)
        runs = db.get_runs(session, sprinkler.id)
        return [{
            'at'        : run.at.strftime(DATETIME_PATTERN),
            'duration'  : "{0} minutes".format(run.duration // 60),
        } for run in runs]
    
def set_sprinkler_state(sprinkler_id, on):
    with db.session_scope() as session:
        sprinkler = db.get_sprinkler(session, sprinkler_id)
        _set_sprinkler_state(session, sprinkler, on)

def _set_sprinkler_state(session, sprinkler, state):
    attempts = 0
    direction = 'on' if state else 'off'
    LOGGER.info("Set %s to %s", sprinkler, direction)
    try:
        while True:
            try:
                ubw.set_pin(sprinkler.port, sprinkler.pin, state)
                db.create_state_change_record(session, sprinkler, state)
                return
            except ubw.UBWUnavailable, e:
                LOGGER.warning("Failed to attach to a UBW. Waiting 3 seconds to try again")
                time.sleep(3)
                attempts += 1
                if attempts > 20:
                    _send_failure_email(sprinkler, attempts, direction)
    except Exception, e:
        logging.exception("Major failure while trying to control %s and turn it %s: %s", sprinkler, direction, e)
        _send_failure_email(sprinkler, attempts, direction)
        
def _call_later(callback, name, seconds):
    if configuration['server-type'] == 'dbus':
        def wrapped_callback(name, callback):
            glib.source_remove(_call_later.timers[name])
            callback()
        _call_later.timers[name] = glib.timeout_add_seconds(seconds, functools.partial(wrapped_callback, name, callback))
    else:
        def wrapped_callback(name, callback):
            del _call_later.timers[name]
            callback()
        timer = threading.Timer(seconds, functools.partial(wrapped_callback, name, callback))
        _timers[sprinkler.id] = timer
        timer.start()
        
_call_later.timers = {}

def set_sprinkler_on_duration(sprinkler_id, seconds):
    with db.session_scope() as session:
        sprinkler = db.get_sprinkler(session, sprinkler_id)
        _set_sprinkler_state(session, sprinkler, True)
        LOGGER.info("%s will go off in %d seconds", sprinkler, seconds)
        callback = functools.partial(_go_off, sprinkler.id)
        _call_later(callback, sprinkler.id, seconds)

def _go_off(sprinkler_id):
    with db.session_scope() as session:
        sprinkler = db.get_sprinkler(session, sprinkler_id)
        LOGGER.debug("Setting %s off now", sprinkler)
        _set_sprinkler_state(session, sprinkler, False)

def _send_failure_email(sprinkler, attempts, direction):
    ses = boto.ses.connection.SESConnection()
    ses.send_email(
        source          = 'automation@theribbles.org',
        subject         = 'Failed to turn sprinkler {0} {1}'.format(sprinkler.name, direction),
        body            = 'Sorry, I could not manage to control sprinkler {0} after {1} attempts. I was trying to turn it {2}'.format(sprinkler, attempts, direction),
        to_addresses    = 'junk@theribbles.org')

