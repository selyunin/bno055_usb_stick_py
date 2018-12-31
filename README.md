# BNO055 USB Stick Python driver

[![PyPI version](https://badge.fury.io/py/bno055-usb-stick-py.svg)](https://badge.fury.io/py/bno055-usb-stick-py)

**TL;DR:** *"Swiss army knife"* for using 
[`BNO055 USB Stick`](https://eu.mouser.com/new/bosch/bosch-bno055-usb-stick/) 
under Linux from `python3`. 

`BNO055 USB Stick` comes with 
[`Development Desktop 2.0`](https://www.bosch-sensortec.com/bst/support_tools/downloads/overview_downloads) 
software package, 
which is available for Windows only. 

If you have a `BNO055 USB Stick` and want to
use it on a Linux platform 
(e.g. Ubuntu, Raspbian, Yocto, Suse, etc.) 
this repo provides you with a `python 3` driver,
capable of reading / writing registers / burst read, 
and stream data read.

## OS Prerequisites

1. When plugged in on a Linux system, 
the `BNO055 USB Stick` should appear 
as `/dev/ttyACM*` device. 
This device is a so-called
[`cdc_acm`](https://www.keil.com/pack/doc/mw/USB/html/group__usbh__cdcacm_functions.html) 
(communication device class), but let us leave 
these details for now.

2. Your Linux user must be a member of the
`dialout` group 
(e.g. see this [thread](https://unix.stackexchange.com/questions/14354/read-write-to-a-serial-port-without-root))
to be able to read/write `ttyACM*` devices 
without root privileges.

3. `udev` is installed on the system.
We do autodetect the USB stick by relying on information from
udev.

## Installation

```sh
pip install bno055-usb-stick-py
```


## Supported Python version

**python v3.6+**

## Python dependencies

**TL;DR:** install 
(i) `pyserial`, 
(ii) `pyudev`,
(iii) `dataclasses` (if using `python3.6`), and
(iv) optionally: `pyquaternion` 
and `matplotlib`, 
or use 
[`environment.yml`](./environment.yml)
to create conda environment
with dependencies resolved.

For further details regarding creating `conda` environment read [**this**](./CONDA_HOWTO.md) guide.

## Quick start

Read BNO register:

```python
from bno055_usb_stick_py import BnoUsbStick
bno_usb_stick = BnoUsbStick()
reg_addr = 0x00
reg_val = bno_usb_stick.read_register(reg_addr)
print(f"bno chip id addr: 0x{reg_addr:02X}, value: 0x{reg_val:02X}")
```

Write register:

```python
from bno055_usb_stick_py import BnoUsbStick
bno_usb_stick = BnoUsbStick()
reg_addr = 0x3F
reg_value = 0x01
bno_usb_stick.write_register(reg_addr, reg_value)
print(f"bno self test started!")
```

Burst register read:

```python
from bno055_usb_stick_py import BnoUsbStick
bno_usb_stick = BnoUsbStick()
reg_start_addr = 0x08
num_registers = 0x12
burst_read_result = bno_usb_stick.burst_read(reg_start_addr, num_registers)
print(f"bno burst read result: {burst_read_result}")
```

Get 10 packets in streaming mode (using generator):

```python
from bno055_usb_stick_py import BnoUsbStick

bno_usb_stick = BnoUsbStick()
bno_usb_stick.activate_streaming()
for packet in bno_usb_stick.recv_streaming_generator(num_packets=10):
    print(f"bno data: {packet}")
```

Get 100 packets in streaming mode (by receiving single packets):

```python
from bno055_usb_stick_py import BnoUsbStick
bno_usb_stick = BnoUsbStick()
bno_usb_stick.activate_streaming()
for _ in range(100):
    packet = bno_usb_stick.recv_streaming_packet()
    print(f"{packet}")
```

Receive infinite number of packets (in case you wait infinite time :wink: ):

```python
from bno055_usb_stick_py import BnoUsbStick
bno_usb_stick = BnoUsbStick()
bno_usb_stick.activate_streaming()
for packet in bno_usb_stick.recv_streaming_generator():
    print(f"{packet}")
```

## Bno USB Stick Data Packet

When receiving data in streaming mode, the result 
is an object of `BNO055` data class (from `bno055.py`) file.

`BNO055` data class has the following fields:

```python
from bno055_usb_stick_py import BNO055
bno_data = BNO055()
bno_data.a_raw  # raw accelerometer data (a_raw_x, a_raw_y, a_raw_z)
bno_data.g_raw  # raw gyro data (g_raw_x, g_raw_y, g_raw_z)
bno_data.m_raw  # raw magnetometer data (m_raw_x, m_raw_y, m_raw_z)
bno_data.euler_raw  # raw euler angles (heading, roll, pitch)
bno_data.quaternion_raw  # raw quaternion data (q_raw_w, q_raw_x, q_raw_y, q_raw_z)
bno_data.lin_a_raw  # raw linear acceleration data (lin_a_raw_x, lin_a_raw_y, lin_a_raw_z)
bno_data.gravity_raw  # raw gravity vector (gravity_raw_x, gravity_raw_y, gravity_raw_z)
bno_data.a  # accelerometer (a_x, a_y, a_z)
bno_data.g  # gyroscope (g_x, g_y, g_z)
bno_data.m  # magnetometer (m_x, m_y, m_z)
bno_data.euler  # euler angler (heading, roll, pitch)
bno_data.quaternion  # quaternion values (q_w, q_x, q_y, q_z)
bno_data.lin_a  # linear acceleration (lin_a_x, lin_a_y, lin_a_z)
bno_data.gravity  # gravity vector (gravity_x, gravity_y, gravity_z)
bno_data.temp  # temperature register
bno_data.calib_stat  # calibration status (addr 0x35) register
bno_data.st_result  # status result (addr 0x36) register
bno_data.int_sta  # interrupt status (addr 0x37) register
bno_data.sys_clk_status  # system clock status (addr 0x38) register
bno_data.sys_status  # system status (addr 0x39) register
```

## Prevent modem manager to capture serial device

When plugging `bno_usb_stick` on Ubuntu,
the device is unavailable for the first 10-15 seconds,
due to the fact that `ModemManager` process 
takes over and tries to use the device.

To avoid this Ubuntu-specific behavior, 
add an exception to the `udev` rules,
s.t. the `ModemManager` ignores the `bno_usb_stick`.
Run the script:

`python disable_modem_manager_bno_usb_stick.py`

The script requires root privileges. Essentially it copies 
the `97-ttyacm.rules` file to `/etc/udev/rules.d` and reloads the 
udev rules.

## Maintainer

[Dr. Konstantin Selyunin](http://selyunin.com/), 
for suggestions / questions / comments 
please contact: 
selyunin [dot] k [dot] v [at] gmail [dot] com



