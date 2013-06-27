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
import logging

LOGGER = logging.getLogger('ubw')

class UBWException(Exception):
    pass

class UBW(object):
    def __init__(self, device_name, device):
        self.device_name = device_name
        self.device = device

    def __repr__(self):
        return "UBW on {0}".format(self.device_name)

def _get_device():
    device_name = _find_device()
    LOGGER.debug("Got device %s", device_name)
    device = serial.Serial(device_name)
    if not device.isOpen():
        raise UBWException("Failed to open serial connection")
    ubw = UBW(device_name, device)
    _handle_commands(ubw, ['C,0,0,0,0'])
    return UBW(device_name, device)
    
def _handle_commands(ubw, commands, retry=True):
    LOGGER.debug("Handling commands '%s'", commands)
    attempts = 0
    try:
        ubw.device.write('\n'.join(commands)+ '\n')
        responses = [ubw.device.readline() for command in commands]
        responses = [response.replace('\r\n', '') for response in responses]
        return responses
    except (IOError, serial.serialutil.SerialException), e:
        LOGGER.warning('Serial exception detected, attempting to re-init ubw')
        attempts += 1
        time.sleep(3)
        ubw = _get_device()
        if not retry:
            return _handle_commands(ubw, commands, retry=False)
    raise Exception("Failed to handle command to %s '%s' after 3 attempts", ubw, command)
    
def _handle_command(ubw, command):
    return _handle_commands(ubw, [command])[0]

def _to_bit_array(val):
    val = int(val)
    return [bool(val & (1<<y)) for y in range(8)]

def _all_off(ubw):
    return _handle_command(ubw, 'O,0,0,0')

def _get_pin_states(ubw):
    response = _handle_command(ubw, 'I')
    A, B, C = _get_pin_states.pattern.match(response).groups()
    return {
        'A': _to_bit_array(A),
        'B': _to_bit_array(B),
        'C': _to_bit_array(C)}
_get_pin_states.pattern = re.compile('I,(?P<A>\d{3}),(?P<B>\d{3}),(?P<C>\d{3})')

def get_status():
    ubw = _get_device()
    return _get_pin_states(ubw)

def set_pin(port, pin, state):
    ubw = _get_device()
    assert port in ('A', 'B', 'C')
    assert state in (True, False)
    pin = _get_pin(pin)
    LOGGER.debug("Set %s%s output to %s", port, pin, 1 if state else 0)
    return _handle_command(ubw, 'PO,{port},{pin},{state}'.format(**{
        'port'  : port,
        'pin'   : pin,
        'state' : 1 if state else 0}))

def read_pin(ubw, port, pin):
    response = _handle_command(ubw, 'PI,B,0')
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
    
def _find_device():
    for tty in os.listdir('/dev'):
        if 'ACM' in tty:
            return '/dev/' + tty
    raise UBWException("Failed to find any devices like /dev/ACMx")

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

def main():
    device = _find_device()
    if device is None:
        print("Unable to find ACM device in /dev")
        return 1
    print("Using {0}".format(device))

    ubw = init_ubw(device)

    print(_handle_command(ubw, 'V'))
    print("Set all port directions to output: {0}".format(_handle_command(ubw, 'C,0,0,0,0')))
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
                print(_handle_command(ubw, 'V'))
                print("Set all port directions to output: {0}".format(_handle_command(ubw, 'C,0,0,0,0')))
                all_off(ubw)
    finally:
        print('ALL OFF:{0}'.format(all_off(ubw)))

if __name__ == '__main__':
    sys.exit(main())
