#!/opt/local/bin/python

from blockext import *
import serial
import sys


class Lego:
    def __init__(self):
        self.ready = 0
        self.redspeed = [0, 0, 0, 0]
        self.bluespeed = [0, 0, 0, 0]
        self.openserial()

    def openserial(self):
        try:
            self.ser = serial.Serial('/dev/tty.usbserial-A7006nEi', 9600)
        except:
            print 'Cannot open serial port'
            self.ser = None
            return
        self.ready = 1

    def closeserial(self):
        if self.ser:
            self.ready = 0
            self.ser.close()
            self.ser = None

    def _on_reset(self):
        self.closeserial()
        self.openserial()
        for i in range(1,5):
            data = self.createSpeedAdjBinary('r', i, 's')
            self.ser.write(chr(data).encode())
            self.redspeed[i-1] = 0
            data = self.createSpeedAdjBinary('b', i, 's')
            self.ser.write(chr(data).encode())
            self.bluespeed[i-1] = 0

    def createSimpleBinary(self, colour, channel, direction):
        mychannel = int(channel) -1
        data = 0
        if colour == 'r':
            data = 0x40
        data = data | (mychannel << 4)
        if direction == 'f':
            data = data | 0x04
        elif direction == 'b':
            data = data | 0x08
        data = data | 0x03
        return data

    def createSpeedAdjBinary(self, colour, channel, direction):
        mychannel = int(channel) -1
        data = 0
        if colour == 'r':
            data = 0x40
        data = data | (mychannel << 4)
        if direction == 'c':
            data = data | 0x01
        elif direction == 'a':
            data = data | 0x02
        data = data | 0x0c
        return data


    def motor_dir(self, colour, channel, direction):
        if (colour == 'red') or (colour == 'blue'):
            if (direction == 'forwards') or (direction == 'backwards'):
                if (channel == '1') or (channel == '2') or (channel == '3') or (channel == '4'):
                    bindata = self.createSimpleBinary(colour[0], channel, direction[0])
                    self.ser.write(chr(bindata).encode())

    def motor_speed_adj(self, colour, channel, direction):
        if (colour == 'red') or (colour == 'blue'):
            if (direction == 'clockwise') or (direction == 'anticlockwise') or (direction == 'stop'):
                if (channel == '1') or (channel == '2') or (channel == '3') or (channel == '4'):
                    bindata = self.createSpeedAdjBinary(colour[0], channel, direction[0])
                    self.ser.write(chr(bindata).encode())

    def motor_stop(self, colour, channel):
        if (colour == 'red') or (colour == 'blue'):
            if (channel == '1') or (channel == '2') or (channel == '3') or (channel == '4'):
                self.motor_speed_adj(colour, channel, 'stop')
                if colour == 'red':
                    self.redspeed[int(channel) - 1] = 0
                elif colour == 'blue':
                    self.bluespeed[int(channel) - 1] = 0

    def motor_speed(self, colour, channel, speed):
        if (colour == 'red') or (colour == 'blue'):
            if (channel == '1') or (channel == '2') or (channel == '3') or (channel == '4'):
                if isinstance(speed, int) and (speed > -8) and (speed < 8):
                    myspeed = int(speed)
                    if colour == 'red':
                        speeddelta = myspeed - self.redspeed[int(channel) - 1]
                    else:
                        speeddelta = myspeed - self.bluespeed[int(channel) - 1]
                    while speeddelta != 0:
                        if speeddelta > 0:
                            bindata = self.createSpeedAdjBinary(colour[0], channel, 'c')
                            speeddelta = speeddelta - 1
                        else:
                            bindata = self.createSpeedAdjBinary(colour[0], channel, 'a')
                            speeddelta = speeddelta + 1
                        self.ser.write(chr(bindata).encode())
                    if colour == 'red':
                        self.redspeed[int(channel) - 1] = myspeed
                    else:
                        self.bluespeed[int(channel) - 1] = myspeed

    def motors_ready(self):
        if self.ready:
            return True
        else:
            return False

descriptor = Descriptor(
    name = "Lego",
    port = 5000,
    blocks = [
        Block('motor_dir', 'command', '%m.motor motor on channel %m.channel %m.direction',
            defaults=['blue', '1', 'forwards']),
        Block('motor_speed', 'command', '%m.motor motor on channel %m.channel speed %n',
            defaults=['blue', '1', '1']),
        Block('motor_stop', 'command', '%m.motor motor on channel %m.channel stop',
            defaults=['blue', '1']),
        Block('motors_ready', 'predicate', 'motors ready?'),
    ],
    menus = dict(
        channel = ["1", "2", "3", "4"],
        motor = ["blue", "red"],
        direction = ["forwards", "backwards"],
        speeddir = ["clockwise", "anticlockwise", "stop"],
    ),
)

extension = Extension(Lego, descriptor)

if __name__ == '__main__':
    try:
        extension.run_forever(debug=True)
    except KeyboardInterrupt:
        sys.exit(0)


