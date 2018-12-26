Python driver for BNO055 USB Stick
==================================

**TL;DR:** install 
(i) `pyserial`, 
(ii) `pyudev`,
(iii) `numpy`, and
(iv) `pyquaternion`
(optionally `matplotlib` for visualization).

**Long Version:**
In order to get all the dependencies in place 
for the python packages we use the `conda` environment
in this project.

[Miniconda](https://conda.io/miniconda.html) (for `python-3.6`)
is a cross-platform package manager that allows managing
dependencies and creates a corresponding python *environment*. 

0) Install [miniconda](https://conda.io/miniconda.html)

1) Create the `bno055-usb-stick` environment:
`
conda env create -f environment.yml
`

2) Update the `bno055-usb-stick` environment:
`
conda-env update -n bno055-usb-stick -f environment.yml
`

3) Activate the `bno055-usb-stick` environment:

Mac and Linux:
`
source activate bno055-usb-stick
`

4) Remove the `bno055-usb-stick` environment 
(delete the corresponding python packages):
`
conda env remove --name bno055-usb-stick
`

# Prevent modem manager to capture serial device

When plugging `bno_usb_stick` on Ubuntu, we observed
that the device was unavailable for the first 10 seconds
or so, due to the fact that `ModemManager` process first
tries to use the device.

What we need, is to add an exception to the `udev` rules,
s.t. the `ModemManager` ignores the `bno_usb_stick`.
To do so, run the script:

`python disable_modem_manager_bno_usb_stick.py`

The script requires root priviledges. Essentially it copies 
the `97-ttyacm.rules` file to `/etc/udev/rules.d` and reloads the 
udev rules.