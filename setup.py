import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bno055_usb_stick_py",
    version="0.9.5",
    author="Dr. Konstantin Selyunin",
    author_email="selyunin.k.v@gmail.com",
    license="MIT",
    description="BNO055 USB Stick Linux Python Driver",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/selyunin/bno055_usb_stick_py",
    packages=["bno055_usb_stick_py"],
    requires=["pyudev", "pyserial", "dataclasses"],
    install_requires=["pyserial", "pyudev", "dataclasses"],
    package_dir={'bno055_usb_stick_py': 'bno055_usb_stick_py'},
    package_data={"bno055_usb_stick_py": ['97-ttyacm.rules', 'bno055.json']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
    ],
)
