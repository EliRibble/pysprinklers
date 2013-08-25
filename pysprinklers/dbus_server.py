import boto.ses
import db
import dbus
import dbus.service
import dbus.mainloop.glib
import functools
import json
import glib
import gobject
import logging
import re
import time
import ubw

from pysprinklers import platform

LOGGER = logging.getLogger('dbus-server')
class SprinklersApi(dbus.service.Object):
    def __init__(self):
        self.name = 'org.theribbles.HomeAutomation'
        self.path = '/sprinklers'
        self.bus_name = dbus.service.BusName(self.name, bus=dbus.SystemBus())
        dbus.service.Object.__init__(self, self.bus_name, self.path)

    @dbus.service.method('org.theribbles.HomeAutomation', out_signature='s')
    def GetStatus(self):
        statuses = platform.get_status()
        return json.dumps(statuses)

    @dbus.service.method('org.theribbles.HomeAutomation')
    def GetSprinklers(self):
        sprinklers = platform.get_sprinklers()
        return json.dumps(sprinklers, sort_keys=True)

    @dbus.service.method('org.theribbles.HomeAutomation', in_signature='s', out_signature='s')
    def GetHistory(sel, sprinkler_id):
        history = platform.get_history(sprinkler_id)
        return json.dumps(history, sort_keys=True)

    @dbus.service.method('org.theribbles.HomeAutomation', in_signature='s')
    def SetSprinklerOn(self, sprinkler_id):
        platform.set_sprinkler_state(sprinkler_id, True)

    @dbus.service.method('org.theribbles.HomeAutomation', in_signature='s')
    def SetSprinklerOff(self, sprinkler_id):
        platform.set_sprinkler_state(sprinkler_id, False)

    @dbus.service.method('org.theribbles.HomeAutomation', in_signature='ss')
    def SetSprinklerOnDuration(self, sprinkler_id, time):
        seconds = _time_specifier_to_seconds(time)
        platform.set_sprinkler_on_duration(sprinkler_id, seconds)

    @dbus.service.method('org.theribbles.HomeAutomation')
    def TestFailureEmail(self):
        class FakeSprinkler(object):
            def __init__(self, name):
                self.name = name
        platform.send_failure_email(FakeSprinkler('fake'), 1, 'on')
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
    
def _setup_dbus():
    dbus_loop = dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    # To make threading.Timer work
    dbus.mainloop.glib.threads_init()
    dbus_server = SprinklersApi()
    dbus.set_default_main_loop(dbus_loop)

def run(config):
    _setup_dbus()
    platform.configure(config)

    mainloop = gobject.MainLoop()
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print('Exiting due to keyboard interrupt')
