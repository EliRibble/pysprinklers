#!/usr/bin/env python
from Phidgets.PhidgetException import *
from Phidgets.Events.Events import *
from Phidgets.Devices.InterfaceKit import *

def attachHandler(args):
	print(dir(args))
	print(args.__class__.__name__)

def main():
	try:
		interface_kit = InterfaceKit()
		interface_kit.setOnAttachHandler(attachHandler)
		interface_kit.openPhidget()
		interface_kit.waitForAttach(1000)
		print(interface_kit.getOutputCount())
	except RuntimeError as e:
		print("Runtime error: %s" % e.message)
	except PhidgetException as e:
		print("Phidgetexception: {0}".format(e))

if __name__ == '__main__':
	main()
