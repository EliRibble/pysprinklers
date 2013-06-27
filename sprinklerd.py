import logging
import pyudev
import pyudev.glib
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import ubw
import db

print(pyudev.__version__)

LOGGER = logging.getLogger()


class SprinklersApi(dbus.service.Object):
    def __init__(self):
        self.name = 'org.theribbles.HomeAutomation'
        self.path = '/sprinklers'
        self.bus_name = dbus.service.BusName(self.name, bus=dbus.SystemBus())
        dbus.service.Object.__init__(self, self.bus_name, self.path)

    @dbus.service.method('org.theribbles.HomeAutomation', out_signature='s')
    def GetStatus(self):
        try:
            LOGGER.debug("Got status request")
            states = ubw.get_status()
            return str(states)
        except Exception, e:
            LOGGER.exception("Failed to get status")
            return 'Failed'

    @dbus.service.method('org.theribbles.HomeAutomation')
    def GetSprinklers(self):
        session = db.Session()
        sprinklers = session.query(db.Sprinkler)
        return str([{
            'id'    : sprinkler.id,
            'name'  : sprinkler.name,
            'port'  : sprinkler.port,
            'pin'   : sprinkler.pin,
            'description'   : sprinkler.description
        } for sprinkler in sprinklers])

def _setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
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
