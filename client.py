#!/usr/bin/python
import sys
import dbus
system_bus = dbus.SystemBus()

proxy = system_bus.get_object('org.theribbles.HomeAutomation', '/sprinklers')
iface = dbus.Interface(proxy, 'org.theribbles.HomeAutomation')

if len(sys.argv) < 2:
    print("Commands: status, sprinklers, on, off, onfor, testemail")
    sys.exit(1)
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
    iface.SetSprinklerOnDuration(sys.argv[2], sys.argv[3])
elif command == 'testemail':
    iface.TestFailureEmail()
else:
    print("Unrecognized command {0}".format(command))
