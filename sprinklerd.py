import argparse
import dbus_server
import logging
import pyudev
import pyudev.glib
import sys
import ubw

LOGGER = logging.getLogger()

class SprinklerException(Exception):
    pass

def _setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_formatter = logging.Formatter('[%(levelname)-8s] %(asctime)s %(name)s: %(message)s')
    stream_handler.setFormatter(stream_formatter)
    root.addHandler(stream_handler)

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

CONFIG_OPTIONS = {
    'server-type'   : 'web',
}

def _create_config(args):
    configuration = CONFIG_OPTIONS.copy()
    if args.config is not None:
        import ConfigParser
        config_file = ConfigParser.SafeConfigParser()
        config_file.read(args.config)
        for prop, default in CONFIG_OPTIONS.items():
            try:
                configuration[prop] = config_file.get('pysprinklers', prop)
            except (ConfigParser.NoSectionError, ConfigParser.NoOptionError), e:
                configuration[prop] = default

    for key in CONFIG_OPTIONS.keys():
        arg_key = key.replace('-', '_')
        value = getattr(args, arg_key, None)
        if value is not None:
            configuration[key] = value

    return configuration

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help="The config file to use for settings")
    for config in CONFIG_OPTIONS.keys():
        parser.add_argument('--' + config)
    args = parser.parse_args()

    config = _create_config(args)
    _setup_logging()

    logging.info("Starting sprinklerd")

    _link_udev()

    if config['server-type'] == 'dbus':
        LOGGER.info("Enabling DBUS server")
        dbus_server.run(config)

    elif config['server-type'] == 'web':
        LOGGER.info("Enabling Web server")

if __name__ == '__main__':
    main()
