#!/usr/bin/env python
from Phidgets.PhidgetException import *
from Phidgets.Events.Events import *
from Phidgets.Devices.InterfaceKit import *
import datetime
import time
import sys

def attachHandler(args):
	#print(dir(args))
	#print(args.__class__.__name__)
	pass

def print_now():
	now = datetime.datetime.now()
	print( now.strftime("%Y-%m-%d %H:%M") )

def main():
	try:
		interface_kit = InterfaceKit()
		interface_kit.setOnAttachHandler(attachHandler)
		interface_kit.openPhidget()
		interface_kit.waitForAttach(1000)
		if len(sys.argv) > 2:
			input_num = int(sys.argv[1])
			state = int(sys.argv[2]) == 1
			interface_kit.setOutputState(input_num, state)
		else:
			print("Moving through sprinklers...")
			for i in range(interface_kit.getOutputCount()):
				print_now()
				print( "Sprinkler {0} ON".format(i) )
				interface_kit.setOutputState(i, True)
				time.sleep( 60 * 40 )
				print_now()
				interface_kit.setOutputState(i, False)
			
	except RuntimeError as e:
		print("Runtime error: %s" % e.message)
	except PhidgetException as e:
		print("Phidgetexception: {0}".format(e))
	finally:
		interface_kit.closePhidget()

if __name__ == '__main__':
	main()
