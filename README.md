# Python-based Teensy Makefile
My scripts for compiling and uploading to teensies. Your mileage may vary.

## Prequisites

This makefile requires the following programs and binaries to be installed on your system for operation:

- [Arduino Software IDE](https://www.arduino.cc/en/Main/Software)
- [Teensyduino](http://www.pjrc.com/teensy/teensyduino.html)
- [Arduino Builder](https://github.com/arduino/arduino-builder)
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
