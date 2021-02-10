from bno055_usb_stick_py import BnoUsbStick

# Author: Dr. Konstantin Selyunin
# License: MIT


def example_register_read():
    bno_usb_stick = BnoUsbStick()
    reg_addr = 0x00
    reg_val = bno_usb_stick.read_register(reg_addr)
    print(f"bno chip id addr: 0x{reg_addr:02X}, value: 0x{reg_val:02X}")


def example_register_write():
    bno_usb_stick = BnoUsbStick()
    reg_addr = 0x3F
    reg_value = 0x01
    bno_usb_stick.write_register(reg_addr, reg_value)
    print(f"bno self test started!")


def example_burst_read():
    bno_usb_stick = BnoUsbStick()
    reg_start_addr = 0x08
    num_registers = 0x12
    burst_read_result = bno_usb_stick.burst_read(reg_start_addr, num_registers)
    print(f"bno burst read result: {burst_read_result}")


def example_streaming_generator():
    bno_usb_stick = BnoUsbStick()
    bno_usb_stick.activate_streaming()
    for packet in bno_usb_stick.recv_streaming_generator(num_packets=10):
        print(f"bno data: {packet}")


def example_streaming_single():
    bno_usb_stick = BnoUsbStick()
    bno_usb_stick.activate_streaming()
    for _ in range(100):
        packet = bno_usb_stick.recv_streaming_packet()
        print(f"{packet}")


def example_reset():
    from time import sleep
    bno_usb_stick = BnoUsbStick()
    # 1. read current operation mode
    opr_mode_addr = 0x3D
    mode = bno_usb_stick.read_register(opr_mode_addr) & 0x0F
    print(f"Initial operation mode: {mode:04b}")
    # 2. change operation mode to NDOF, p.22, Table 3-5 of the datasheet
    ndof_mode = 0b00001100
    bno_usb_stick.write_register(opr_mode_addr, ndof_mode)
    sleep(0.1)
    # 3. read back the mode register, double check if mode is written
    mode = bno_usb_stick.read_register(opr_mode_addr) & 0x0F
    print(f"Changed operation mode: {mode:04b}")
    # 4. set RST_SYS bit of SYS_TRIGGER register (i.e. initiate a reset)
    sys_trigger_addr = 0x3F
    reset_val = 1 << 5
    bno_usb_stick.write_register(sys_trigger_addr, reset_val)
    sleep(1.0)
    # 5. read back the operation mode, check if chip is reset
    mode = bno_usb_stick.read_register(opr_mode_addr) & 0x0F
    print(f"Mode upon reset is: {mode:04b}")


if __name__ == '__main__':
    example_register_read()
    example_register_write()
    example_burst_read()
    example_streaming_generator()
    example_streaming_single()
    example_reset()