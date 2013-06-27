#!/usr/bin/python
import sys
import dbus
system_bus = dbus.SystemBus()

proxy = system_bus.get_object('org.theribbles.HomeAutomation', '/sprinklers')
iface = dbus.Interface(proxy, 'org.theribbles.HomeAutomation')

command = sys.argv[1]
if command == 'status':
    print(iface.GetStatus())
elif command == 'sprinklers':
    print(iface.GetSprinklers())
elif command == 'on':
    iface.SetSprinklerOn(sys.argv[2])
elif command == 'off':
    iface.SetSprinklerOff(sys.argv[2])
elif command == 'onfor':
    iface.SetSprinklerOnDuration(sys.argv[2], int(sys.argv[3]))
