#!/usr/bin/env python

import json
import os
import os.path
import pyudev
import serial
import time
from typing import Dict, List, Tuple


class BnoException(Exception):
    def __init__(self, message: str):
        self.message = message


class BnoUsbStick:
    """BNO055 USB Stick"""

    def __init__(self, *args, **kwargs):
        self.port = None
        self.port_name = ''
        self.bno = None
        self.bno_config_file = "bno055.json"
        self.bno_config = self.read_bno_json_config(self.bno_config_file)
        self.buffer = None
        self.payload = None
        self.bno_udev_config = self.bno_config['udev']
        self.buffer_size = 1024

    @staticmethod
    def read_bno_json_config(file):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bno_file_abspath = os.path.join(current_dir, file)
        with open(bno_file_abspath) as f:
            return json.load(f)

    def autodetect(self):
        context = pyudev.Context()
        for device in context.list_devices(subsystem='tty'):
            device_udev_values = {}
            for key, val in self.bno_udev_config.items():
                device_udev_values[key] = device.get(key)
            if device_udev_values == self.bno_udev_config:
                self.port_name = device.device_node
                return True
            else:
                raise BnoException("BNO USB Stick not detected!")

    def connect(self):
        self.port = serial.Serial()
        self.port.port = self.port_name
        for key, value in self.bno_config['serial'].items():
            setattr(self.port, key, value)
        self.port.open()

    def disconnect(self):
        self.port.close()

    def __enter__(self):
        self.connect()

    def __exit__(self):
        self.disconnect()

    def send(self, command: bytearray, params: dict = {}) -> bool:
        command_to_send = command.copy()
        if len(params) > 0:
            for entry in params:
                command_to_send[entry['idx']] = entry['val']
        bytes_sent = self.port.write(command_to_send)
        return bytes_sent == len(command_to_send)

    def recv(self, timeout=0.1):
        ok = False
        time_stamp = time.time()
        time_elapsed = 0
        while not ok and time_elapsed < timeout:
            self.buffer = self.port.read(self.buffer_size)
            ok = len(self.buffer) > 0
            time_elapsed = time.time() - time_stamp
        if ok:
            return True, self.buffer
        else:
            return False, bytes()

    def send_recv(self, packet: bytearray, params: dict = {}) -> Tuple[bool, bytes]:
        send_ok = self.send(packet, params)
        if not send_ok:
            raise BnoException("Sending packet failed!")
        recv_ok, recv_data = self.recv()
        if not recv_ok:
            raise BnoException("Receiving packet failed!")
        return True, recv_data

    def pop_bytes(self, num_bytes=2, **kwargs):
        val = int.from_bytes(self.payload[0:num_bytes], byteorder='big', **kwargs)
        self.payload = self.payload[num_bytes:]
        return val

    def decode_board_info(self):
        """getting board information"""
        self.payload = self.buffer[5:-2]
        _cmd = self.pop_bytes(num_bytes=1, signed=False)
        shuttle_id = self.pop_bytes(signed=False)
        hardware_id = self.pop_bytes(signed=False)
        software_id = self.pop_bytes(signed=False)
        board_type = self.pop_bytes(num_bytes=1, signed=False)
        info_str = f"SHUTTLE_ID: {shuttle_id};\t\tHARDWARE_ID: {hardware_id};" + \
                   f"\t\tSOFTWARE_ID: {software_id};\t\tBOARD_TYPE: {board_type}"
        print(info_str)

    def query_board_info(self):
        command = bytearray(self.bno_config['board_information']['command'])
        params = self.bno_config['board_information']['params']
        ok, resp = self.send_recv(command, params)
        if not ok:
            raise BnoException("Command sent failed!")
        self.decode_board_info()

    def decode_register_read(self):

        return None

    def read_register(self, reg_addr):
        command = self.bno_config['read_register']['command']
        params = self.bno_config['read_register']['params']
        reg_addr_entry = next(filter(lambda x: x['description'] == 'reg_addr', params))
        reg_entry_idx = params.index(reg_addr_entry)
        params[reg_entry_idx]['val'] = reg_addr
        ok, resp = self.send_recv(command, params)
        if not ok:
            raise BnoException("Command sent failed!")
        return self.decode_register_read()


if __name__ == "__main__":
    # example client code
    bno_usb_stick = BnoUsbStick()
    bno_usb_stick.autodetect()
    bno_usb_stick.connect()
    bno_usb_stick.query_board_info()
    bno_usb_stick.read_register(0x01)
