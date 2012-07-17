#!/usr/bin/env python
from Phidgets.PhidgetException import *
from Phidgets.Events.Events import *
from Phidgets.Devices.InterfaceKit import *
import datetime
import time
import sys
import signal

def attachHandler(args):
	#print(dir(args))
	#print(args.__class__.__name__)
	pass

def print_now():
	now = datetime.datetime.now()
	print( now.strftime("%Y-%m-%d %H:%M") )

def all_off(interface_kit):
	for i in range(interface_kit.getOutputCount()):
		interface_kit.setOutputState(i, False)
	print("All valves off")

CURRENT_SCHEDULES = {
	0: {
		0: 45,
		2: 45,
		3: 45,
	},
	1: {
		8:  40,
		9:  40,
		10: 45,
		11: 45,
		12: 45,
	},
}
	
SPRAY_TIME_MULTIPLIER = 60
def run_schedule(schedule, interface_kit):
	for valve, spray_time in schedule.items():
		print("Valve {0} for {1}".format(valve, spray_time * SPRAY_TIME_MULTIPLIER))
		interface_kit.setOutputState(valve, True)
		time.sleep(spray_time * SPRAY_TIME_MULTIPLIER)
		interface_kit.setOutputState(valve, False)
	

def main():
	if len(sys.argv) < 2:
		print("Please specify --all-off or --run-zone <number>")
		sys.exit(1)
	

	interface_kit = InterfaceKit()
	#interface_kit.setOnAttachHandler(attachHandler)
	interface_kit.openPhidget()
	try:
		interface_kit.waitForAttach(1000)

		# Set up signal handlers for exiting
		def shutdown(signum, frame):
			all_off(interface_kit)
			sys.exit(4)
		for sig in (signal.SIGABRT, signal.SIGILL, signal.SIGINT, signal.SIGTERM):
			signal.signal(sig, shutdown)

		if sys.argv[1] == '--all-off':
			all_off(interface_kit)
			sys.exit(0)
		elif sys.argv[1] == '--run-zone':
			if len(sys.argv) < 3:
				print("Please spcify a zone number")
				sys.exit(2)
			else:
				zone_number = int(sys.argv[2])
				interface_kit.setOutputState(zone_number, True)
				print("Valve {0} ON".format(zone_number))
				if len(sys.argv) == 4:
					min_to_run = int(sys.argv[3])
					print("Running for {0} minutes".format(min_to_run))
					time.sleep(min_to_run * 60)
					interface_kit.setOutputState(zone_number, False)
				sys.exit(0)
		elif sys.argv[1] == '--run':
			for section, schedule in CURRENT_SCHEDULES.items():
				run_schedule(schedule, interface_kit)	
	except RuntimeError as e:
		print("Runtime error: %s" % e.message)
	except PhidgetException as e:
		print("Phidgetexception: {0}".format(e))
	finally:
		interface_kit.closePhidget()
	sys.exit(3)

if __name__ == '__main__':
	main()
