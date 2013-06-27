#!/usr/bin/python
import traceback
import time
import serial
import serial.serialutil
import sys
import re
import os
import pprint
import code
import functools
import pprint
import argparse

def init_ubw(device):
    ubw = serial.Serial(device)

    if not ubw.isOpen():
        raise Exception("Failed to open %s", device)

    # Reset the device just so we have a clean slate
    handle_command(ubw, 'R')
    return ubw

def handle_command(ubw, command):
    print(command)
    attempts = 0
    while attempts < 3:
        try:
            ubw.write(command + '\n')
            response = ubw.readline()
            response = response.replace('\r\n', '')
            return response
        except (IOError, serial.serialutil.SerialException), e:
            traceback.print_exc()
            attempts += 1
            time.sleep(3)
    raise Exception("Failed to handle command to %s '%s' after 3 attempts", ubw, command)
    
def _to_bit_array(val):
    val = int(val)
    return [bool(val & (1<<y)) for y in range(8)]

def all_off(ubw):
    return handle_command(ubw, 'O,0,0,0')

def read_ports(ubw):
    response = handle_command(ubw, 'I')
    A, B, C = read_ports.pattern.match(response).groups()
    return {
        'A': _to_bit_array(A),
        'B': _to_bit_array(B),
        'C': _to_bit_array(C)}
read_ports.pattern = re.compile('I,(?P<A>\d{3}),(?P<B>\d{3}),(?P<C>\d{3})')

def read_pin(ubw, port, pin):
    response = handle_command(ubw, 'PI,B,0')
    match = read_pin.pattern.match(response)
    return bool(int(match.group('value')))
read_pin.pattern = re.compile('PI,(?P<value>[01])')

def _get_pin(pin):
    if pin in (0,1,2,3,4,5,6,7):
        return pin
    else:
        for config in SETUP.values():
            if pin in config:
                return config[pin]
        raise Exception('Unrecognized pin %s', pin)
    
def set_pin(ubw, port, pin, value):
    assert port in ('A', 'B', 'C')
    assert value in (True, False)
    pin = _get_pin(pin)
    print("Set {0}{1} output to {2}".format(port, pin, 1 if value else 0))
    return handle_command(ubw, 'PO,{port},{pin},{value}'.format(**{
        'port'  : port,
        'pin'   : pin,
        'value' : 1 if value else 0}))

def _find_device():
    for tty in os.listdir('/dev'):
        if 'ACM' in tty:
            return '/dev/' + tty
    return None

def _is_finished(progress):
    for config in SCHEDULE.values():
        if _get_next(config, progress) is not None:
            return False
    return True

def _get_next(config, progress):
    for valve, time in config['valves'].items():
        if valve not in progress:
            progress[valve] = 0
            return valve
        elif progress[valve] < time:
            return valve
    return None

SETUP = {
    'A': {
        'backyard-south-grass': 1,
        'backyard-west-grass': 2,
        'backyard-east-grass': 3,
    },
    'B': {
        'front-parking-strip': 0,
        'front-east-grass': 1,
        'front-center-grass': 2,
        'front-center-and-west-grass': 3,
        'front-flower-garden': 4,
    }
}

DEFAULT_TIME = 40
SCHEDULE = {
    'front': {
        'port': 'B',
        'valves': {
            'front-east-grass'              : DEFAULT_TIME,
            'front-center-grass'            : DEFAULT_TIME,
            #'front-center-and-west-grass'   : DEFAULT_TIME,
            #'front-flower-garden'           : DEFAULT_TIME,
            'front-parking-strip'           : DEFAULT_TIME,
        }
    },
    'back': {
        'port': 'A',
        'valves': {
            #'backyard-south-grass'          : DEFAULT_TIME,
            #'backyard-west-grass'           : DEFAULT_TIME,
            'backyard-east-grass'           : DEFAULT_TIME,
        }
    }
}

def main():
    device = _find_device()
    if device is None:
        print("Unable to find ACM device in /dev")
        return 1
    print("Using {0}".format(device))

    ubw = init_ubw(device)

    print(handle_command(ubw, 'V'))
    print("Set all port directions to output: {0}".format(handle_command(ubw, 'C,0,0,0,0')))
    front = SCHEDULE['front']
    back = SCHEDULE['back']
    progress = {}
    chunk_size = min(10, DEFAULT_TIME)
    try:
        while not _is_finished(progress):
            try:
                current_front = _get_next(front, progress)
                current_back = _get_next(back, progress)
                print("Front: {0}\tBack: {1}".format(current_front, current_back))
                all_off(ubw)
                if current_front is not None:
                    set_pin(ubw, SCHEDULE['front']['port'], current_front, True)
                if current_back is not None:
                    set_pin(ubw, SCHEDULE['back']['port'], current_back, True)
                time.sleep(chunk_size * 60)
                if current_front is not None:
                    progress[current_front] += chunk_size
                if current_back is not None:
                    progress[current_back] += chunk_size
            except (IOError, serial.serialutil.SerialException), e:
                traceback.print_exc()
                print("Progess before failure:")
                pprint.pprint(progress)
                time.sleep(5)
                device = _find_device()
                print("Now using {0}".format(device))
                if device is None:
                    raise Exception("Cannot get a device anymore")
                ubw = init_ubw(device)
                print(handle_command(ubw, 'V'))
                print("Set all port directions to output: {0}".format(handle_command(ubw, 'C,0,0,0,0')))
                all_off(ubw)
    finally:
        print('ALL OFF:{0}'.format(all_off(ubw)))

if __name__ == '__main__':
    sys.exit(main())
