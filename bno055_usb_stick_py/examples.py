from bno055_usb_stick_py import BnoUsbStick


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


if __name__ == '__main__':
    example_register_read()
    example_register_write()
    example_burst_read()
    example_streaming_generator()
    example_streaming_single()
