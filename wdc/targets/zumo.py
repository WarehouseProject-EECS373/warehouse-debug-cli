import serial
import struct
import datetime
from enum import IntEnum

from wdc.targets.target import Target

DISPATCH_MSG_ID = 0x1
DEBUG_PACKET_MSG_ID = 0x2
DEBUG_PACKET_PAYLOAD_SIZE = 6

DISPATCH_MSG = bytearray([DISPATCH_MSG_ID, 0, 0])

class AO_ID(IntEnum):
    WATCHDOG = 0x0,
    DRIVE = 0x1,
    INPUT_CTL = 0x2,
    COMMS = 0x3,
    STATE = 0x4,
    REFARR = 0x5

class MSG_ID(IntEnum):
    DATA_MSG_ID = 0x0,
    SENSOR_READ_MSG_ID = 0x1,
    HEARTBEAT_MSG = 0x2,
    DRIVE_CTL_IN = 0x10,
    DRIVE_DISABLE = 0x11,
    DRIVE_ENABLE = 0x12,
    DRIVE_TIMED_ACTIVITY = 0x13,
    DRIVE_TIMED_TURN = 0x18,
    DRIVE_TIMED_TURN_DONE = 0x19,
    REFARR_CALIBRATE = 0x30,
    REFARR_PERIODIC_EVENT = 0x36,
    PUSH_BUTTON_PRESSED = 0x61,
    UART_SMALL_PACKET = 0x81,
    UART_LARGE_PACKET = 0x82,
    OS_DEBUG_MSG = 0x83,
    SM_PERIODIC_EVENT = 0x100,
    SM_DISPATCH_FROM_IDLE = 0x110,
    SM_CALIBRATE_DONE = 0x120,



class DebugMessagePackets:
    def __init__(self, ao_id, msg_id, is_queue, timestamp):
        self.ao_id = ao_id
        self.msg_id = msg_id
        self.is_queue = is_queue
        self.timestamp = timestamp

    def __repr__(self):
        operation = "queued to" if self.is_queue else "handled by"

        return "[" + str(self.timestamp) + "]: " + MSG_ID(self.msg_id).name + " " + operation + " " + AO_ID(self.ao_id).name

class ZumoTarget(Target):

    def __init__(self, port: str, baud):
        self.sp = serial.Serial(port, int(baud))
        self.captures = []
        super().__init__()

    def dispatch(self, bay: int, aisle: int) -> None:
        self.sp.write(DISPATCH_MSG)

    def start_listener(self, live):
        super().start_listener(live)
        self.captures = []

    def stop_listener(self):
        super().stop_listener()
    
    def show_log(self):
        for c in self.captures:
            print(c)

    def listen(self):
        print("Starting listener")
        self.sp.reset_input_buffer()
        
        while self.listener_running:
            payload = self.sp.read_until(b"\x5A")

            if len(payload) != 8:
                self.sp.reset_input_buffer()
                continue

            timestamp = datetime.datetime.now().time()

            _, ao_id, is_queue, msg_id, _ = struct.unpack("<BB?IB", payload)
                
            packet = DebugMessagePackets(ao_id, msg_id, is_queue, timestamp)
            self.captures.append(packet)

            if self.live_log:
                print(packet)

