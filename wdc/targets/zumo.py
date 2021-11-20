import serial

from wdc.targets.target import Target

DISPATCH_MSG_ID = 0x1

DISPATCH_MSG = bytearray([DISPATCH_MSG_ID, 0, 0])

class ZumoTarget(Target):

    def __init__(self, port: str, baud):
        self.sp = serial.Serial(port, int(baud))

        super().__init__()

    def dispatch(self, bay: int, aisle: int) -> None:
        self.sp.write(DISPATCH_MSG)

        
