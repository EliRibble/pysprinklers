import logging
import re
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
import sys

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
            statuses[sprinkler.name] = 'on' if states[sprinkler.port][sprinkler.pin] else 'off'
        session.close()
        return str(statuses)
                

    @dbus.service.method('org.theribbles.HomeAutomation')
    def GetSprinklers(self):
        session = db.Session()
        sprinklers = db.get_sprinklers(session)
        return str([{
            'id'    : sprinkler.id,
            'name'  : sprinkler.name,
            'port'  : sprinkler.port,
            'pin'   : sprinkler.pin,
            'description'   : sprinkler.description
        } for sprinkler in sprinklers])

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
        LOGGER.debug("Setting %s off now", sprinkler_id)
        glib.source_remove(self.timeouts[sprinkler_id])
        del self.timeouts[sprinkler_id]
        self._set_sprinkler_state(session, sprinkler, False)

    def _set_sprinkler_state(self, sprinkler, state):
        LOGGER.info("Set %s to %s", sprinkler, 'on' if state else 'off')
        ubw.set_pin(sprinkler.port, sprinkler.pin, state)
        db.create_state_change_record(sprinkler, state)
        
    @dbus.service.method('org.theribbles.HomeAutomation', in_signature='ss')
    def SetSprinklerOnDuration(self, sprinkler_id, time):
        session = db.Session()
        seconds = _time_specifier_to_seconds(time)
        sprinkler = db.get_sprinkler(session, sprinkler_id)
        self._set_sprinkler_state(session, sprinkler, True)
        LOGGER.info("Sprinkler will go off in %d seconds (%s)", seconds, time)
        callback = functools.partial(self._go_off, sprinkler.id)
        timeout_id = glib.timeout_add_seconds(time, callback)
        self.timeouts[sprinkler.id] = timeout_id

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


def _device_added_callback(observer, device, *args, **kwargs):
    LOGGER.info("Got device added callback with args: %s", args)
    LOGGER.info("Got device added callback with kwargs: %s", kwargs)
    LOGGER.debug("Device: {0}".format(device))

def _device_changed_callback(observer, device, *args, **kwargs):
    LOGGER.info("Got device changed callback with args: %s", args)
    LOGGER.info("Got device changed callback with args: %s", kwargs)
    LOGGER.debug("Device: {0}".format(device))
   
def _device_removed_callback(observer, device, *args, **kwargs):
    LOGGER.info("Got device removed callback with args: %s", args)
    LOGGER.info("Got device removed callback with args: %s", kwargs)
    LOGGER.debug("Device: {0}".format(device))

def _device_moved_callback(observer, device, *args, **kwargs):
    LOGGER.info("Got device moved callback with args: %s", args)
    LOGGER.info("Got device moved callback with args: %s", kwargs)
    LOGGER.debug("Device: {0}".format(device))

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
