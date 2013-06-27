#!/usr/bin/python
import dbus
system_bus = dbus.SystemBus()

proxy = system_bus.get_object('org.theribbles.HomeAutomation', '/sprinklers')
iface = dbus.Interface(proxy, 'org.theribbles.HomeAutomation')
print(iface.GetStatus())
print(iface.GetSprinklers())
