TARGET_EGG_INFO=bno055_usb_stick_py.egg-info
DIST=dist
BUILD=build

all:
	python3 setup.py sdist bdist_wheel

clean:
	rm  -rf ${TARGET_EGG_INFO} ${DIST} ${BUILD}
