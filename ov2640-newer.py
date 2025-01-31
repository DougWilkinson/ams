# ov2640.py

# from ov2640_constants import *
# from ov2640_lores_constants import *
# from ov2640_hires_constants import *
import machine
import time
import ubinascii
import uos
import gc
from core import info, error

SENSORADDR = 0x30

settings = {'OV2640_640x480_JPEG': [255, 1, 17, 1, 18, 0, 23, 17, 24, 117, 50, 54, 25, 1, 26, 151, 3, 15, 55, 64, 79, 187, 80, 156, 90, 87, 109, 128, 61, 52, 57, 2, 53, 136, 34, 10, 55, 64, 52, 160, 6, 2, 13, 183, 14, 1, 255, 0, 224, 4, 192, 200, 193, 150, 134, 61, 80, 137, 81, 144, 82, 44, 83, 0, 84, 0, 85, 136, 87, 0, 90, 160, 91, 120, 92, 0, 211, 4, 224, 0, 255, 255], 
               'OV2640_1600x1200_JPEG': [255, 1, 17, 1, 18, 0, 23, 17, 24, 117, 50, 54, 25, 1, 26, 151, 3, 15, 55, 64, 79, 187, 80, 156, 90, 87, 109, 128, 61, 52, 57, 2, 53, 136, 34, 10, 55, 64, 52, 160, 6, 2, 13, 183, 14, 1, 255, 0, 224, 4, 192, 200, 193, 150, 134, 61, 80, 0, 81, 144, 82, 44, 83, 0, 84, 0, 85, 136, 87, 0, 90, 144, 91, 44, 92, 5, 211, 2, 224, 0, 255, 255], 
               'OV2640_352x288_JPEG': [255, 1, 18, 64, 23, 17, 24, 67, 25, 0, 26, 75, 50, 9, 79, 202, 80, 168, 90, 35, 109, 0, 57, 18, 53, 218, 34, 26, 55, 195, 35, 0, 52, 192, 54, 26, 6, 136, 7, 192, 13, 135, 14, 65, 76, 0, 255, 0, 224, 4, 192, 100, 193, 75, 134, 53, 80, 137, 81, 200, 82, 150, 83, 0, 84, 0, 85, 0, 87, 0, 90, 88, 91, 72, 92, 0, 224, 0, 255, 255], 
               'OV2640_320x240_JPEG': [255, 1, 18, 64, 23, 17, 24, 67, 25, 0, 26, 75, 50, 9, 79, 202, 80, 168, 90, 35, 109, 0, 57, 18, 53, 218, 34, 26, 55, 195, 35, 0, 52, 192, 54, 26, 6, 136, 7, 192, 13, 135, 14, 65, 76, 0, 255, 0, 224, 4, 192, 100, 193, 75, 134, 53, 80, 137, 81, 200, 82, 150, 83, 0, 84, 0, 85, 0, 87, 0, 90, 80, 91, 60, 92, 0, 224, 0, 255, 255], 
               'OV2640_1024x768_JPEG': [255, 1, 17, 1, 18, 0, 23, 17, 24, 117, 50, 54, 25, 1, 26, 151, 3, 15, 55, 64, 79, 187, 80, 156, 90, 87, 109, 128, 61, 52, 57, 2, 53, 136, 34, 10, 55, 64, 52, 160, 6, 2, 13, 183, 14, 1, 255, 0, 192, 200, 193, 150, 140, 0, 134, 61, 80, 0, 81, 144, 82, 44, 83, 0, 84, 0, 85, 136, 90, 0, 91, 192, 92, 1, 211, 2, 255, 255], 
               'OV2640_1280x1024_JPEG': [255, 1, 17, 1, 18, 0, 23, 17, 24, 117, 50, 54, 25, 1, 26, 151, 3, 15, 55, 64, 79, 187, 80, 156, 90, 87, 109, 128, 61, 52, 57, 2, 53, 136, 34, 10, 55, 64, 52, 160, 6, 2, 13, 183, 14, 1, 255, 0, 224, 4, 192, 200, 193, 150, 134, 61, 80, 0, 81, 144, 82, 44, 83, 0, 84, 0, 85, 136, 87, 0, 90, 64, 91, 240, 92, 1, 211, 2, 224, 0, 255, 255],
               'OV2640_JPEG_INIT': [255, 0, 44, 255, 46, 223, 255, 1, 60, 50, 17, 4, 9, 2, 4, 40, 19, 229, 20, 72, 44, 12, 51, 120, 58, 51, 59, 251, 62, 0, 67, 17, 22, 16, 57, 146, 53, 218, 34, 26, 55, 195, 35, 0, 52, 192, 54, 26, 6, 136, 7, 192, 13, 135, 14, 65, 76, 0, 72, 0, 91, 0, 66, 3, 74, 129, 33, 153, 36, 64, 37, 56, 38, 130, 92, 0, 99, 0, 97, 112, 98, 128, 124, 5, 32, 128, 40, 48, 108, 0, 109, 128, 110, 0, 112, 2, 113, 148, 115, 193, 18, 64, 23, 17, 24, 67, 25, 0, 26, 75, 50, 9, 55, 192, 79, 96, 80, 168, 109, 0, 61, 56, 70, 63, 79, 96, 12, 60, 255, 0, 229, 127, 249, 192, 65, 36, 224, 20, 118, 255, 51, 160, 66, 32, 67, 24, 76, 0, 135, 213, 136, 63, 215, 3, 217, 16, 211, 130, 200, 8, 201, 128, 124, 0, 125, 0, 124, 3, 125, 72, 125, 72, 124, 8, 125, 32, 125, 16, 125, 14, 144, 0, 145, 14, 145, 26, 145, 49, 145, 90, 145, 105, 145, 117, 145, 126, 145, 136, 145, 143, 145, 150, 145, 163, 145, 175, 145, 196, 145, 215, 145, 232, 145, 32, 146, 0, 147, 6, 147, 227, 147, 5, 147, 5, 147, 0, 147, 4, 147, 0, 147, 0, 147, 0, 147, 0, 147, 0, 147, 0, 147, 0, 150, 0, 151, 8, 151, 25, 151, 2, 151, 12, 151, 36, 151, 48, 151, 40, 151, 38, 151, 2, 151, 152, 151, 128, 151, 0, 151, 0, 195, 237, 164, 0, 168, 0, 197, 17, 198, 81, 191, 128, 199, 16, 182, 102, 184, 165, 183, 100, 185, 124, 179, 175, 180, 151, 181, 255, 176, 197, 177, 148, 178, 15, 196, 92, 192, 100, 193, 75, 140, 0, 134, 61, 80, 0, 81, 200, 82, 150, 83, 0, 84, 0, 85, 0, 90, 200, 91, 150, 92, 0, 211, 0, 195, 237, 127, 0, 218, 0, 229, 31, 225, 103, 224, 0, 221, 127, 5, 0, 18, 64, 211, 4, 192, 22, 193, 18, 140, 0, 134, 61, 80, 0, 81, 44, 82, 36, 83, 0, 84, 0, 85, 0, 90, 44, 91, 36, 92, 0, 255, 255], 
               'OV2640_YUV422': [255, 0, 5, 0, 218, 16, 215, 3, 223, 0, 51, 128, 60, 64, 225, 119, 0, 0, 255, 255], 
               'OV2640_JPEG': [224, 20, 225, 119, 229, 31, 215, 3, 218, 16, 224, 0, 255, 1, 4, 8, 255, 255]
            }

class OV2640(object):
    def __init__(self, cspin=10, sda=8, scl=9, mosi=12, miso=13, resolution="OV2640_320x240_JPEG", polarity=0, phase=0):
        self.standby = False

        self.hspi = machine.SPI(1, baudrate=2000000, polarity=polarity, phase=phase, sck=machine.Pin(14), mosi=machine.Pin(mosi), miso=machine.Pin(miso))
        self.i2c = machine.SoftI2C(scl=machine.Pin(scl), sda=machine.Pin(sda), freq=1000000)
    
        # first init spi assuming the hardware spi is connected
        self.hspi.init()

        # chip select -- active low
        self.cspin = machine.Pin(cspin, machine.Pin.OUT)
        self.cspin.on()

        # init the i2c interface
        addrs = self.i2c.scan()
        info('i2c scan: {}'.format(addrs) )
        for a in addrs:
            print('0x%x' % a)
   
        # select register set table 13
        self.i2c.writeto_mem(SENSORADDR, 0xff, b'\x01')
        # initiate system reset bit 7 (bits 4,5,6=0 sets full UXGA resolution)
        self.i2c.writeto_mem(SENSORADDR, 0x12, b'\x80')
        time.sleep_ms(100)


        # init registers
        cam_write_register_set(self.i2c, SENSORADDR, "OV2640_JPEG_INIT")
        cam_write_register_set(self.i2c, SENSORADDR, "OV2640_YUV422")
        cam_write_register_set(self.i2c, SENSORADDR, "OV2640_JPEG")
   
        # select register set (table 13 in datasheet)
        self.i2c.writeto_mem(SENSORADDR, 0xff, b'\x01')
        self.i2c.writeto_mem(SENSORADDR, 0x15, b'\x00')
        self.set_resolution(resolution)
   
        # test the SPI bus
        cam_spi_write(b'\x00', b'\x55', self.hspi, self.cspin)
        res = cam_spi_read(b'\x00', self.hspi, self.cspin)
        if (res == b'\x55'):
            info("SPI register test passed")
        else:
            error("SPI register test failed")
    
        # Check camera type
        self.i2c.writeto_mem(SENSORADDR, 0xff, b'\x01')
        parta = self.i2c.readfrom_mem(SENSORADDR, 0x0a, 1)
        partb = self.i2c.readfrom_mem(SENSORADDR, 0x0b, 1)

        if ((parta != b'\x26') or (partb != b'\x42')):
            error("camera model not detected as ov2640 {}{}".format(ubinascii.hexlify(parta), ubinascii.hexlify(partb)))    
        else:
            info("ov2640 camera model detected")

    # get image using burst read and return image in byte array
    def set_resolution(self, resolution):
        cam_write_register_set(self.i2c, SENSORADDR, resolution)

    def get_image(self, max_buffer=100000):
        # bit 0 - clear FIFO write done flag
        cam_spi_write(b'\x04', b'\x01', self.hspi, self.cspin)
    
        # bit 1 - start capture then read status
        cam_spi_write(b'\x04', b'\x02', self.hspi, self.cspin)
        time.sleep_ms(10)
    
        # read status
        res = cam_spi_read(b'\x41', self.hspi, self.cspin)
        cnt = 0
        #if (res == b'\x00'):
        #    print("initiate capture may have failed, return byte: %s" % ubinascii.hexlify(res))

        # read the image from the camera fifo
        while True:
            res = cam_spi_read(b'\x41', self.hspi, self.cspin)
            mask = b'\x08'
            if (res[0] & mask[0]):
                break
            #print("continuing, res register %s" % ubinascii.hexlify(res))
            time.sleep_ms(10)
            cnt += 1
        #print("slept in loop %d times" % cnt)
   
        # read the fifo size
        b1 = cam_spi_read(b'\x44', self.hspi, self.cspin)
        b2 = cam_spi_read(b'\x43', self.hspi, self.cspin)
        b3 = cam_spi_read(b'\x42', self.hspi, self.cspin)
        fifo_size = b1[0] << 16 | b2[0] << 8 | b3[0] 
        print("ov2640_captured: %d bytes" % fifo_size)
        gc.collect()
    
        fifo = cam_spi_burst_read(fifo_size, self.hspi, self.cspin)

        for i in range(len(fifo) - 2, -1, -1):
            if fifo[i:i + 2] == b'\xff\xd9':
                break
        return b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + fifo[1:i+2]

        # Capture to file using slow single byte read
    def capture_to_file(self, fn, overwrite):
        # bit 0 - clear FIFO write done flag
        cam_spi_write(b'\x04', b'\x01', self.hspi, self.cspin)
    
        # bit 1 - start capture then read status
        cam_spi_write(b'\x04', b'\x02', self.hspi, self.cspin)
        time.sleep_ms(10)
    
        # read status
        res = cam_spi_read(b'\x41', self.hspi, self.cspin)
        cnt = 0
        #if (res == b'\x00'):
        #    print("initiate capture may have failed, return byte: %s" % ubinascii.hexlify(res))

        # read the image from the camera fifo
        while True:
            res = cam_spi_read(b'\x41', self.hspi, self.cspin)
            mask = b'\x08'
            if (res[0] & mask[0]):
                break
            #print("continuing, res register %s" % ubinascii.hexlify(res))
            time.sleep_ms(10)
            cnt += 1
        #print("slept in loop %d times" % cnt)
   
        # read the fifo size
        b1 = cam_spi_read(b'\x44', self.hspi, self.cspin)
        b2 = cam_spi_read(b'\x43', self.hspi, self.cspin)
        b3 = cam_spi_read(b'\x42', self.hspi, self.cspin)
        val = b1[0] << 16 | b2[0] << 8 | b3[0] 
        print("ov2640_capture: %d bytes in fifo" % val)
        gc.collect()
    
        bytebuf = [ 0, 0 ]
        picbuf = [ b'\x00' ] * PICBUFSIZE
        l = 0
        bp = 0
        if (overwrite == True):
            #print("deleting old file %s" % fn)
            try:
                uos.remove(fn)
            except OSError:
                pass
        while ((bytebuf[0] != b'\xd9') or (bytebuf[1] != b'\xff')):
            bytebuf[1] = bytebuf[0]
            if (bp > (len(picbuf) - 1)):
                #print("appending buffer to %s" % fn)
                appendbuf(fn, picbuf, bp)
                bp = 0
    
            bytebuf[0] = cam_spi_read(b'\x3d', self.hspi, self.cspin)
            l += 1
            #print("read so far: %d, next byte: %s" % (l, ubinascii.hexlify(bytebuf[0])))
            picbuf[bp] = bytebuf[0]
            bp += 1
        if (bp > 0):
            #print("appending final buffer to %s" % fn)
            appendbuf(fn, picbuf, bp)
        print("read %d bytes from fifo, camera said %d were available" % (l, val))
        return (l)

    # XXX these need some work
    def standby(self):
        # register set select
        self.i2c.writeto_mem(SENSORADDR, 0xff, b'\x01')
        # standby mode
        self.i2c.writeto_mem(SENSORADDR, 0x09, b'\x10')
        self.standby = True

    def wake(self):
        # register set select
        self.i2c.writeto_mem(SENSORADDR, 0xff, b'\x01')
        # standby mode
        self.i2c.writeto_mem(SENSORADDR, 0x09, b'\x00')
        self.standby = False

def cam_write_register_set(i, addr, set_name):
    set = settings[set_name]
    for el in range(0, len(set), 2):
        raddr = set[el]
        val = bytes(set[el+1] )
        if (raddr == 0xff and val == b'\xff'):
            return
        #print("writing byte %s to addr %x register addr %x" % \
        #   (ubinascii.hexlify(val), addr, raddr))
        i.writeto_mem(addr, raddr, val)

def appendbuf(fn, picbuf, howmany):
    try:
        f = open(fn, 'ab')
        c = 1
        for by in picbuf:
            if (c > howmany):
                break
            c += 1
            f.write(bytes([by[0]]))
        f.close()
    except OSError:
        print("error writing file")
    print("write %d bytes from buffer" % howmany)

def cam_spi_write(address, value, hspi, cspin):
    cspin.off()
    modebit = b'\x80'
    d = bytes([address[0] | modebit[0], value[0]])
    #print("bytes %s" % ubinascii.hexlify(d))
    #print (ubd.hex())
    hspi.write(d)
    cspin.on()

def cam_spi_burst_read(fifo_size, hspi, cspin):
    buf = bytearray(fifo_size)
    cspin.off()
    address=b'\x3c'
    maskbits = b'\x7f'
    burst_read = bytes([address[0] & maskbits[0]])
    hspi.write(burst_read)
    hspi.readinto(buf)
    cspin.on()
    return buf

def cam_spi_read(address, hspi, cspin):
    cspin.off()
    maskbits = b'\x7f'
    wbuf = bytes([address[0] & maskbits[0]])
    hspi.write(wbuf)
    buf = hspi.read(1)
    cspin.on()
    return (buf)

# cam driver code
# https://github.com/kanflo/esparducam/blob/master/arducam/arducam.c
# register info
# https://github.com/ArduCAM/Sensor-Regsiter-Decoder/blob/master/OV2640_JPEG_INIT.csv
