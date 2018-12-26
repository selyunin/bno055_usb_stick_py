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
        if kwargs.get('port') is not None:
            self.port_name = kwargs.get('port')
        else:
            self.autodetect()
        self.connect()

    @staticmethod
    def read_bno_json_config(file):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bno_file_abspath = os.path.join(current_dir, file)
        with open(bno_file_abspath) as f:
            return json.load(f)

    @staticmethod
    def find_entry_idx(params, description):
        reg_addr_entry = next(filter(lambda x: x['description'] == description, params))
        return params.index(reg_addr_entry)

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
        if self.port is None or not self.port.is_open:
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

    def pop_bytes(self, num_bytes=2, byteorder='big', **kwargs):
        val = int.from_bytes(self.payload[0:num_bytes], byteorder=byteorder, **kwargs)
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
        """ask for board information, hw / sw id"""
        command = bytearray(self.bno_config['board_information']['command'])
        params = self.bno_config['board_information']['params']
        ok, resp = self.send_recv(command, params)
        if not ok:
            raise BnoException("Command sent failed!")
        self.decode_board_info()

    def check_packet(self, packet: bytes) -> bool:
        """check start and stop packet bytes"""
        assert packet[0] == 0xAA, f"Invalid start byte, expected 0xAA, got {packet[0]}"
        assert packet[-2] == 0x0D, f"Invalid stop byte, expected 0x0D, got{packet[-2]}"
        assert packet[-1] == 0x0A, f"Invalid stop byte, expected 0x0A, got{packet[-1]}"
        return True

    def decode_register_read(self):
        """extract payload, the received packet is stored in buffer"""
        self.check_packet(self.buffer)
        error_status = self.buffer[3]
        response_code = self.buffer[4]
        if (response_code == 66 or response_code == 65) and (error_status == 0 or error_status == 2):
            return self.buffer[11]
        else:
            return None

    def read_register(self, reg_addr):
        """read single register of the BNO"""
        command = self.bno_config['read_register']['command']
        params = self.bno_config['read_register']['params']
        entry_idx = self.find_entry_idx(params, 'reg_addr')
        params[entry_idx]['val'] = reg_addr
        ok, _ = self.send_recv(command, params)
        if not ok:
            raise BnoException("Command sent failed!")
        return self.decode_register_read()

    def decode_register_write(self, reg_addr, reg_value):
        """check that register response is OK"""
        self.check_packet(self.buffer)
        error_status = self.buffer[3]
        response_code = self.buffer[4]
        if (response_code == 66 or response_code == 65) and (error_status == 0 or error_status == 2):
            if self.buffer[7] == reg_addr and self.buffer[11] == reg_value:
                return True
        return False

    def write_register(self, reg_addr, reg_value):
        """writing single register of the BNO"""
        command = self.bno_config['write_register']['command']
        params = self.bno_config['write_register']['params']
        reg_addr_entry_idx = self.find_entry_idx(params, 'reg_addr')
        params[reg_addr_entry_idx]['val'] = reg_addr
        reg_value_entry_idx = self.find_entry_idx(params, 'reg_val')
        params[reg_value_entry_idx]['val'] = reg_value
        ok, _ = self.send_recv(command, params)
        if not ok:
            raise BnoException("Command sent failed!")
        return self.decode_register_write(reg_addr, reg_value)


def test_register_content(bno: BnoUsbStick, reg_address: int, expected_value: int, err_message: str):
    """check whether register content match expected value"""
    reg_value = bno.read_register(reg_address)
    if reg_value != expected_value:
        raise BnoException("Expected: {:02X}, Got{:02X}\n{}".format(expected_value, reg_value, err_message))
    return reg_value


def check_bno_chip_id(bno: BnoUsbStick):
    """BNO chip ID, fixed value 0xA0"""
    reg_addr = 0x00
    expected_value = 0xA0
    reg_value = test_register_content(bno, reg_addr, expected_value, "Reading BNO Chip ID failed!")
    print("Reading BNO Chip ID successful, got 0x{:02X}".format(reg_value))


if __name__ == "__main__":
    # example client code
    bno_usb_stick = BnoUsbStick()
    bno_usb_stick.query_board_info()
    print(f"r_00: 0x{bno_usb_stick.read_register(0x00):02X}")
    print(f"r_01: 0x{bno_usb_stick.read_register(0x01):02X}")
    print(f"r_02: 0x{bno_usb_stick.read_register(0x02):02X}")
    print(f"r_03: 0x{bno_usb_stick.read_register(0x03):02X}")
    print(f"r_04: 0x{bno_usb_stick.read_register(0x04):02X}")
    check_bno_chip_id(bno_usb_stick)
    print(bno_usb_stick.write_register(0x3D, 0x0C))
