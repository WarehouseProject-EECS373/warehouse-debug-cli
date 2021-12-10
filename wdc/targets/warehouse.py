import serial
import struct
import datetime
from enum import Enum, IntEnum


from wdc.targets.target import Target

class BarcodeSimulator(Target):

    def __init__(self, port: str, baud):
        self.sp = serial.Serial(port, int(baud))
        
        super().__init__()

    def take_reading(self, package_code: int):
        c = package_code + ord('0')
        self.sp.write(struct.pack("<10B", c, c, c, c, c, c, c, ord("0"), ord("\r"), ord("\n")))


