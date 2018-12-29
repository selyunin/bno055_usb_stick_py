#!/usr/bin/env python

import json
import os
import os.path
import re

import pyudev
import serial
import time
from typing import Tuple

from bno055_usb_stick_py.bno055 import BNO055


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

    def __del__(self):
        if self.port is not None and self.port.is_open:
            self.deactivate_streaming()
        self.disconnect()

    @staticmethod
    def read_bno_json_config(file):
        if not file:
            raise BnoException("BNO JSON config file not specified!")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        bno_file_abspath = os.path.join(current_dir, file)
        with open(bno_file_abspath) as f:
            config = json.load(f)
        for section in config:
            if section in ['bno055_page_0', 'bno055_page_1']:
                for reg_name, reg_addr in config[section].items():
                    config[section][reg_name] = int(reg_addr, 16)
            if section in ['start_streaming', 'stop_streaming']:
                for idx, command in enumerate(config[section]):
                    config[section][idx] = bytes([int(el, 16) for el in command])
        return config

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
        if self.port is not None and self.port.is_open:
            self.port.close()

    def __enter__(self):
        self.connect()

    def __exit__(self):
        self.deactivate_streaming()
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
        """
        chop `num_bytes` from self.payload and interpret chopped chunk as integer
        :param num_bytes: number of bytes to chop from beginning of bytes object
        :param byteorder: little or big Endian interpretation of chopped bytes
        :param kwargs: e.g. signed flag, or smth,
        :return: interpreted integer
        """
        val = int.from_bytes(self.payload[0:num_bytes], byteorder=byteorder, **kwargs)
        self.payload = self.payload[num_bytes:]
        return val

    def decode_board_info(self):
        """getting board information, received buffer stored in self.buffer"""
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
        """ask for board information, shuttle /hw / sw id"""
        command = bytearray(self.bno_config['board_information']['command'])
        params = self.bno_config['board_information']['params']
        ok, resp = self.send_recv(command, params)
        if not ok:
            raise BnoException("Command sent failed!")
        self.decode_board_info()

    def check_packet(self, packet: bytes) -> bool:
        """check start and stop packet bytes, error byte, and status"""
        assert packet[0] == 0xAA, f"Invalid start byte, expected 0xAA, got {packet[0]}"
        assert packet[-2] == 0x0D, f"Invalid stop byte, expected 0x0D, got{packet[-2]}"
        assert packet[-1] == 0x0A, f"Invalid stop byte, expected 0x0A, got{packet[-1]}"
        error_status = packet[3]
        assert error_status == 0 or error_status == 2, f"Invalid error status flag, got {error_status}"
        response_code = packet[4]
        assert response_code == 66 or response_code == 65, f"Invalid response code, got {response_code}"
        return True

    def decode_register_read(self):
        """extract payload, the received packet is stored in buffer"""
        check_ok = self.check_packet(self.buffer)
        if check_ok:
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

    def get_addr_str(self, addr: int) -> str:
        config_map = self.bno_config['bno055_page_0']
        for key, val in config_map.items():
            if val == addr:
                return key
        else:
            return ''

    def decode_burst_read(self, start_reg_addr, num_bytes):
        """

        :param start_reg_addr:
        :param num_bytes:
        :return:
        """
        self.check_packet(self.buffer)
        self.payload = self.buffer[11:-2]
        reg_name = self.get_addr_str(start_reg_addr)
        bytes_processed = 0
        register_content = []
        register_names = []
        while bytes_processed < num_bytes:
            if 'LSB' in reg_name:
                val = self.pop_bytes(2, byteorder='little', signed=True)
                bytes_processed += 2
            else:
                val = self.pop_bytes(1)
                bytes_processed += 1
            reg_name_split = re.compile('((_MSB)|(_LSB))?_ADDR').split(reg_name)[0]
            register_content.append(val)
            register_names.append(reg_name_split)
            reg_name = self.get_addr_str(start_reg_addr + bytes_processed)
        return register_content, register_names

    def check_streaming_packet(self):
        """
        Check that streaming packet has length 0x38, start byte 0xAA,
        and stop bytes 0x0D,0x0A
        :return: True if everything is OK
        :raises: BnoException if packet length, start, or stop bytes are not met
        """
        if len(self.buffer) != 0x38:
            raise BnoException(f"Streaming packet length does not match, expected: 0x38, got {len(self.buffer)}")
        start_byte = 0xAA
        stop_bytes = bytes([13, 10])
        packet_start_idx = self.buffer.find(start_byte)
        packet_stop_idx = self.buffer[packet_start_idx + 1:].find(stop_bytes)
        if packet_start_idx == -1:
            raise BnoException("Start byte of streaming packet not found")
        if packet_stop_idx == -1:
            raise BnoException("Stop bytes of streaming packet not found")
        return True

    def recv_streaming_packet(self):
        """
        Receive and decode single streaming packet.
        :return: BNO055 dataclass
        """
        ok, _ = self.recv()
        self.check_streaming_packet()
        return self.decode_streaming()

    def recv_streaming_generator(self, num_packets=-1):
        """
        Receive and decode `num_packets` streaming packets.
        :param num_packets: number of packets to receive / decode.
        If -1 (default), receive forever
        :return:
        """
        packets_received = 0
        while num_packets == -1 or packets_received < num_packets:
            yield self.recv_streaming_packet()
            packets_received += 1

    def decode_streaming(self):
        self.payload = self.buffer[5:-2]
        a_x = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        a_y = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        a_z = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)

        m_x = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        m_y = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        m_z = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)

        g_x = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        g_y = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        g_z = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)

        yaw = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        roll = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        pitch = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)

        q_w = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        q_x = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        q_y = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        q_z = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)

        lin_a_x = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        lin_a_y = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        lin_a_z = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)

        gravity_x = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        gravity_y = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)
        gravity_z = self.pop_bytes(num_bytes=2, byteorder='little', signed=True)

        temp = self.pop_bytes(num_bytes=1, byteorder='little', signed=True)
        calib_stat = self.pop_bytes(num_bytes=1, byteorder='little', signed=False)
        st_result = self.pop_bytes(num_bytes=1, byteorder='little', signed=False)
        int_sta = self.pop_bytes(num_bytes=1, byteorder='little', signed=False)
        sys_clk_status = self.pop_bytes(num_bytes=1, byteorder='little', signed=False)
        sys_status = self.pop_bytes(num_bytes=1, byteorder='little', signed=False)

        bno_data = BNO055()
        bno_data.a_raw = (a_x, a_y, a_z)
        bno_data.g_raw = (g_x, g_y, g_z)
        bno_data.m_raw = (m_x, m_y, m_z)
        bno_data.euler_raw = (yaw, roll, pitch)
        bno_data.quaternion_raw = (q_w, q_x, q_y, q_z)
        bno_data.lin_a_raw = (lin_a_x, lin_a_y, lin_a_z)
        bno_data.gravity_raw = (gravity_x, gravity_y, gravity_z)
        bno_data.temp = temp
        bno_data.calib_stat = calib_stat
        bno_data.st_result = st_result
        bno_data.int_sta = int_sta
        bno_data.sys_clk_status = sys_clk_status
        bno_data.sys_status = sys_status
        bno_data.apply_resolution()
        return bno_data

    def burst_read(self, start_reg_addr, num_bytes):
        num_bytes_msb = (num_bytes >> 8) & 0xFF
        num_bytes_lsb = num_bytes & 0xFF
        command = self.bno_config['burst_read']['command']
        params = self.bno_config['burst_read']['params']
        reg_addr_entry_idx = self.find_entry_idx(params, 'start_reg_addr')
        params[reg_addr_entry_idx]['val'] = start_reg_addr
        msb_entry_idx = self.find_entry_idx(params, 'num_bytes_msb')
        params[msb_entry_idx]['val'] = num_bytes_msb
        lsb_entry_idx = self.find_entry_idx(params, 'num_bytes_lsb')
        params[lsb_entry_idx]['val'] = num_bytes_lsb
        ok, _ = self.send_recv(command, params)
        if not ok:
            raise BnoException("Command sent failed!")
        return self.decode_burst_read(start_reg_addr, num_bytes)

    def activate_streaming(self):
        commands_sequence = self.bno_config['start_streaming']
        for command in commands_sequence:
            params = {}
            ok, _ = self.send_recv(bytearray(command), params)

    def deactivate_streaming(self):
        commands_sequence = self.bno_config['stop_streaming']
        for command in commands_sequence:
            params = {}
            ok, _ = self.send_recv(bytearray(command), params)
        while len(self.buffer) > 0:
            self.recv()


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
    print(bno_usb_stick.burst_read(0x00, 30))
    bno_usb_stick.activate_streaming()
    print(bno_usb_stick.recv_streaming_packet())
    print('generator\n================')
    for packet in bno_usb_stick.recv_streaming_generator(num_packets=10):
        print(packet)
