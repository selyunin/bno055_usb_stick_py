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
