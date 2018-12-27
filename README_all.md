BNO055 USB Stick Linux driver
=============================

**TL;DR:** *"Swiss army knife"* for using `BNO055 USB Stick` in Linux from 
`Python`, `C++`, or `C`. 

**Long version**: 
`BNO055 USB Stick` comes with 
`Development Desktop 2.0` software, 
which runs in Windows only. 

If you have a `BNO055 USB Stick` and want to
use it on a Linux platform 
(e.g. Ubuntu, Raspbian, Yocto, etc.) 
this repo provides you with 
everything you need.

## Prerequisites

1. When plugged in on a Linux system, 
the `BNO055 USB Stick` should appear 
as `/dev/ttyACM*` device. 

2. Your Linux user must be a member of
`dialout` group 
(e.g. see this [thread](https://unix.stackexchange.com/questions/14354/read-write-to-a-serial-port-without-root))
to be able to read/write without root privileges.

3. `udev` is installed on the system 

## Supported Languages 

1. Python (v3.6)
2. C++ 
3. C


## Maintainer

[Konstantin Selyunin](http://selyunin.com/), 
for suggestions / questions / comments 
please contact: 
selyunin [dot] k [dot] v [at] gmail [dot] com




