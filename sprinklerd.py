import sys
import logging
import re
import time
import functools
import pyudev
import pyudev.glib
import glib
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import ubw
import db
import boto.ses

LOGGER = logging.getLogger()

class SprinklerException(Exception):
    pass

class SprinklersApi(dbus.service.Object):
    def __init__(self):
        self.name = 'org.theribbles.HomeAutomation'
        self.path = '/sprinklers'
        self.timeouts = {}
        self.bus_name = dbus.service.BusName(self.name, bus=dbus.SystemBus())
        dbus.service.Object.__init__(self, self.bus_name, self.path)

    @dbus.service.method('org.theribbles.HomeAutomation', out_signature='s')
    def GetStatus(self):
        session = db.Session()
        sprinklers = db.get_sprinklers(session)
        states = ubw.get_status()
        statuses = {}
        for sprinkler in sprinklers:
            status = {
                'state'     : 'on' if states[sprinkler.port][sprinkler.pin] else 'off',
                'last_ran'  : db.get_last_ran(session, sprinkler.id)
            }
            statuses[sprinkler.name] = status
        session.close()
        return str(statuses)
                

    @dbus.service.method('org.theribbles.HomeAutomation')
    def GetSprinklers(self):
        session = db.Session()
        sprinklers = db.get_sprinklers(session)
        data = str([{
            'id'    : sprinkler.id,
            'name'  : sprinkler.name,
            'port'  : sprinkler.port,
            'pin'   : sprinkler.pin,
            'description'   : sprinkler.description
        } for sprinkler in sprinklers])
        session.close()
        return data

    @dbus.service.method('org.theribbles.HomeAutomation', in_signature='s')
    def SetSprinklerOn(self, sprinkler_id):
        session = db.Session()
        sprinkler = db.get_sprinkler(session, sprinkler_id)
        self._set_sprinkler_state(session, sprinkler, True)
        session.close()

    @dbus.service.method('org.theribbles.HomeAutomation', in_signature='s')
    def SetSprinklerOff(self, sprinkler_id):
        session = db.Session()
        sprinkler = db.get_sprinkler(session, sprinkler_id)
        self._set_sprinkler_state(session, sprinkler, False)
        session.close()

    def _go_off(self, sprinkler_id):
        session = db.Session()
        sprinkler = db.get_sprinkler(session, sprinkler_id)
        LOGGER.debug("Setting %s off now", sprinkler)
        glib.source_remove(self.timeouts[sprinkler_id])
        del self.timeouts[sprinkler_id]
        self._set_sprinkler_state(session, sprinkler, False)
        session.close()

    def _set_sprinkler_state(self, session, sprinkler, state):
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
        except Exception:
            _send_failure_email(sprinkler, attempts, direction)
            
        
    @dbus.service.method('org.theribbles.HomeAutomation', in_signature='ss')
    def SetSprinklerOnDuration(self, sprinkler_id, time):
        session = db.Session()
        seconds = _time_specifier_to_seconds(time)
        sprinkler = db.get_sprinkler(session, sprinkler_id)
        self._set_sprinkler_state(session, sprinkler, True)
        LOGGER.info("%s will go off in %d seconds (%s)", sprinkler, seconds, time)
        callback = functools.partial(self._go_off, sprinkler.id)
        timeout_id = glib.timeout_add_seconds(seconds, callback)
        self.timeouts[sprinkler.id] = timeout_id
        session.close()

    @dbus.service.method('org.theribbles.HomeAutomation')
    def TestFailureEmail(self):
        class FakeSprinkler(object):
            def __init__(self, name):
                self.name = name
        _send_failure_email(FakeSprinkler('fake'), 1, 'on')
        LOGGER.info("Test failure email sent")

def _time_specifier_to_seconds(specifier):
    match = _time_specifier_to_seconds.pattern.match(specifier)
    if not match:
        raise Exception("Bad time specifier: %s", specifier)
    unit = match.group('unit')
    if unit == 's':
        return int(match.group('amount'))
    elif unit == 'm':
        return int(match.group('amount')) * 60
    
_time_specifier_to_seconds.pattern = re.compile('(?P<amount>\d+)(?P<unit>m|s)$')
    
def _setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_formatter = logging.Formatter('[%(levelname)-8s] %(asctime)s %(name)s: %(message)s')
    stream_handler.setFormatter(stream_formatter)
    root.addHandler(stream_handler)

def _send_failure_email(sprinkler, attempts, direction):
    ses = boto.ses.connection.SESConnection()
    ses.send_email(
        source          = 'automation@theribbles.org',
        subject         = 'Failed to turn sprinkler {0} {1}'.format(sprinkler.name, direction),
        body            = 'Sorry, I could not manage to control sprinkler {0} after {1} attempts. I was trying to turn it {2}'.format(sprinkler, attempts, direction),
        to_addresses    = 'junk@theribbles.org')

def _device_added_callback(observer, device):
    LOGGER.debug("Added device: {0}".format(device.device_path))
    if 'ACM' in device.device_path:
        ubw.init()

def _device_changed_callback(observer, device):
    LOGGER.debug("Changed device: {0}".format(device.device_path))
   
def _device_removed_callback(observer, device):
    LOGGER.debug("Removed device: {0}".format(device.device_path))

def _device_moved_callback(observer, device):
    LOGGER.debug("Moved device: {0}".format(device.device_path))

def _link_udev():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    observer = pyudev.glib.GUDevMonitorObserver(monitor)
    observer.connect('device-added', _device_added_callback)
    observer.connect('device-changed', _device_changed_callback)
    observer.connect('device-removed', _device_removed_callback)
    observer.connect('device-moved', _device_moved_callback)
    monitor.enable_receiving()

def _setup_dbus():
    dbus_loop = dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    dbus_server = SprinklersApi()
    dbus.set_default_main_loop(dbus_loop)

def main():
    _setup_logging()

    logging.info("Starting sprinklerd")

    _link_udev()

    _setup_dbus()

    mainloop = gobject.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print('Exiting due to keyboard interrupt')
        return

if __name__ == '__main__':
    main()
