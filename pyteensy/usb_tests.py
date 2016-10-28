import usb

busses = usb.busses()
for bus in busses:
  devices = bus.devices
  for dev in devices:
    print(repr(dev))
    print(usb.util.get_langids(dev.dev))
    if dev.iSerialNumber == 3:
        print(usb.util.get_string(dev.dev, dev.iSerialNumber))
