#!/usr/bin/env python

import json
import pyudev
import serial
from typing import Dict, List


class BnoException(Exception):
    def __init__(self, message: str):
        self.message = message


class BnoUsbStick:
    """BNO055 USB Stick"""

    def __init__(self):
        self.port = None
        self.port_name = ''
        self.bno = None
        self.bno_config_file = "bno055.json"
        self.buffer = None
        with open(self.bno_config_file) as f:
            self.bno_config = json.load(f)
        self.bno_udev_config = self.bno_config['udev']

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
        if params is not {}:
            assert "indices" in params, "Parameter indices are not present"
            assert "values" in params, "Parameter values are not present"
            assert len(params["indices"]) == len(params["values"]), "Indices and values have different size"
            for index in params["indices"]:
                command_to_send[index] = params["values"][index]
        bytes_sent = self.port.write(command_to_send)
        return bytes_sent == len(command_to_send)

    def receive(self):
        pass

    def query_board_info(self):
        command = bytearray(self.bno_config['board_information']['command'])
        ok = self.send(command)
        if not ok:
            raise BnoException("Command sent failed!")


if __name__ == "__main__":
    # example client
    bno_usb_stick = BnoUsbStick()
    bno_usb_stick.autodetect()
    bno_usb_stick.connect()
