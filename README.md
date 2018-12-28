# BNO055 USB Stick Python driver

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
pip install bno055_usb_stick_py
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
or use `environment.yml` to create conda environment
with dependencies resolved.

For further details regarding creating `conda` senvironment read [**this**](./CONDA_HOWTO.md) guide.

## Quick start

Read register:

```python
from bno055_usb_stick import BnoUsbStick

bno_usb_stick = BnoUsbStick()
reg_val = bno_usb_stick.read_register(0x00)
print(f"bno chip id addr: {0x00}, value: {reg_val}")
```

Get 10 packets in streaming mode:

```python
from bno055_usb_stick import BnoUsbStick

bno_usb_stick = BnoUsbStick()
bno_usb_stick.activate_streaming()
for packet in bno_usb_stick.recv_streaming_generator(num_packets=10):
    print(f"bno data: {packet}")
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



