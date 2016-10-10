import usb

busses = usb.busses()
for bus in busses:
  devices = bus.devices
  for dev in devices:
    print repr(dev)
    print(usb.util.get_langids(dev.dev))
    if dev.iSerialNumber == 3:
        print(usb.util.get_string(dev.dev, dev.iSerialNumber))
    '''
    print "Device:", dev.filename
    print "  idVendor: %d (0x%04x)" % (dev.idVendor, dev.idVendor)
    print "  idProduct: %d (0x%04x)" % (dev.idProduct, dev.idProduct)
    #print "  idSerial: %d " % dev.iSerial
    print
    print "Manufacturer:", dev.iManufacturer
    print "Serial:", dev.iSerialNumber
    print "Product:", dev.iProduct
    '''