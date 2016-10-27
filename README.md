# Python-based Teensy Makefile
My scripts for compiling and uploading to teensies. Your mileage may vary.

## Prequisites

This makefile requires the following programs and binaries to be installed on your system for operation:

For arduino code compilation:
- [Arduino Software IDE](https://www.arduino.cc/en/Main/Software)
- [Teensyduino beta](https://forum.pjrc.com/threads/38599-Teensyduino-1-31-Beta-2-Available)

For C/C++ code and MicroPython:
- gcc-arm-embedded

For MicroPython code compilation:
- [MicroPython](https://github.com/micropython/micropython)

For all code:
- [TyQt](https://github.com/Koromix/ty)

## Installation

Once all pre-requisites have been installed, clone this repository and run the setup script

```
sudo python setup.py install
```

## Usage

There are two ways to use this library either as a script:

```
pyteensy --upload my_project
```

or use the utilities from within python:

```python
from pyteensy import list_devices

latest_hex = find_hexes()
teensies = list_devices()

for teensy in teensies:
   upload_latest(teensy, latest_hex)
```

## Troubleshooting

If you get an error message like:

```
/bin/sh: tyc: not found
```

Make sure the directories are in your **PATH** environment variable, without
 using the tilda (~) shortcut. Python cannot handle these shortcuts. You
 must set your environment variables as:

```sh
PATH=$PATH:$HOME"/arduino-builder/"
PATH=$PATH:$HOME"/ty/build/linux"
```
