import serial
import struct
import datetime
from enum import IntEnum

from wdc.targets.target import Target

DISPATCH_MSG_ID = 0x1

OS_TRACE_MSG_ID = 0x2
OS_TRACE_EXPECTED_SIZE = 8


DRIVE_CTL_TRACE_MSG_ID = 0x3
DRIVE_CTL_EXPECTED_SIZE = 18

DRIVE_CTL_TRACE_INIT_MSG_ID = 0x4
DRIVE_CTL_INIT_EXPECTED_SIZE = 6

LINE_FOLLOW_MSG_ID = 0x5
LINE_FOLLOW_EXPECTED_SIZE = 14

END_CHAR = b"\x5A"

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
    DRIVE_BASE_VELOCITY = 0x14,
    DRIVE_SETPOINT = 0x15,
    DRIVE_TIMED_TURN = 0x18,
    DRIVE_TIMED_TURN_DONE = 0x19,
    DRIVE_OPEN_LOOP_CTL = 0x1A,
    DRIVE_PERIODIC_EVENT = 0x1B,
    REFARR_CALIBRATE = 0x30,
    REFARR_PERIODIC_EVENT = 0x36,
    REFARR_START_LINE_FOLLOW = 0x37,
    REFARR_STOP_LINE_FOLLOW = 0x38,
    REFARR_INTERSECTION_COUNT_HIT = 0x39,
    PUSH_BUTTON_PRESSED = 0x61,
    LIMIT_SWITCH_HIT = 0x62,
    UART_SMALL_PACKET = 0x81,
    UART_LARGE_PACKET = 0x82,
    OS_DEBUG_MSG = 0x83,
    SM_PERIODIC_EVENT = 0x100,
    SM_DISPATCH_FROM_IDLE = 0x110,
    SM_CALIBRATE_DONE = 0x120,

class DriveCtlInitPacket:
    def __init__(self, sp, timestamp):
        self.setpoint = sp
        self.timestamp = timestamp

    def __repr__(self):
        return "[" + str(self.timestamp.time()) + "]: " + str(self.setpoint)

class DriveCtlTracePacket:
    def __init__(self, left_out, right_out, error, actual, timestamp):
        self.left_out = left_out
        self.right_out = right_out
        self.error = error
        self.actual = actual
        self.timestamp = timestamp

    def __repr__(self):
        return "[" + str(self.timestamp.time()) + "]: " + str(self.left_out) + " " + str(self.right_out) + " " + str(self.error) + " " + str(self.actual)

class LineFollowTracePacket:
    def __init__(self, readings, timestamp):
        self.readings = readings
        self.timestamp = timestamp
    
    def __repr__(self):
        readings_str = [str(i) for i in self.readings]
        return "[" + str(self.timestamp.time()) + "]: " + ",".join(readings_str)

class DebugMessagePackets:
    def __init__(self, ao_id, msg_id, is_queue, timestamp):
        self.ao_id = ao_id
        self.msg_id = msg_id
        self.is_queue = is_queue
        self.timestamp = timestamp

    def __repr__(self):
        operation = "queued to" if self.is_queue else "handled by"

        return "[" + str(self.timestamp.time()) + "]: " + MSG_ID(self.msg_id).name + " " + operation + " " + AO_ID(self.ao_id).name

class ZumoTarget(Target):

    def __init__(self, port: str, baud, filtered=None):
        self.sp = serial.Serial(port, int(baud))

        if filtered is not None:
            self.filtered = filtered
        else:
            self.filtered = []

        super().__init__()

    def get_drive_ctl_data(self):
        ctl_times = []
        left_outs = []
        right_outs = []
        errors = []
        actuals = []

        sp_times = []
        setpoints = []


        for c in self.captures:
            if isinstance(c, DriveCtlInitPacket):
                setpoints.append(c.setpoint)
                sp_times.append(c.timestamp)

            if isinstance(c, DriveCtlTracePacket):
                ctl_times.append(c.timestamp)
                left_outs.append(c.left_out)
                right_outs.append(c.right_out)
                errors.append(c.error)
                actuals.append(c.actual)

        return {"timestamps": ctl_times, "left_percent_out": left_outs, "right_percent_out": right_outs, "errors": errors, "actual": actuals, "sp_times": sp_times, "setpoints": setpoints}

    def dispatch(self, bay: int, aisle: int) -> None:
        self.sp.write(DISPATCH_MSG)

    def start_listener(self, live=False):
        super().start_listener(live)

    def stop_listener(self):
        super().stop_listener()
    
    def listen(self):
        self.sp.reset_input_buffer()
        
        while self.listener_running:
            packet = self.sp.read_until(END_CHAR)
            timestamp = datetime.datetime.now()
            
            if packet[0] == DRIVE_CTL_TRACE_MSG_ID:
                o = self._handle_drive_ctl_msg(packet, timestamp)
            elif packet[0] == DRIVE_CTL_TRACE_INIT_MSG_ID:
                o = self._handle_drive_ctl_init_msg(packet, timestamp)
            elif packet[0] == LINE_FOLLOW_MSG_ID:
                o = self._handle_line_follow_trace_msg(packet, timestamp)
            elif packet[0] == OS_TRACE_MSG_ID:
                o = self._handle_trace_msg(packet, timestamp)


            if self.live_log:
                print(o)
    
    def _handle_drive_ctl_msg(self, packet, timestamp):
        if len(packet) != DRIVE_CTL_EXPECTED_SIZE:
            return None

        _, lo, ro, error, actual, _ = struct.unpack("<BffffB", packet)

        cp = DriveCtlTracePacket(lo, ro, error, actual, timestamp)
        self.captures.append(cp)

        return cp

    def _handle_drive_ctl_init_msg(self, packet, timestamp):
        if len(packet) != DRIVE_CTL_INIT_EXPECTED_SIZE:
            return None

        _, sp, _ = struct.unpack("<BfB", packet)

        initp = DriveCtlInitPacket(sp, timestamp)
        self.captures.append(initp)


    def _handle_line_follow_trace_msg(self, packet, timestamp):
        if len(packet) != LINE_FOLLOW_EXPECTED_SIZE:
            self.sp.reset_input_buffer()
            return None

        _, s0, s1, s2, s3, s4, s5, _ = struct.unpack("<BhhhhhhB", packet)

        lfp = LineFollowTracePacket([s0, s1, s2, s3, s4, s5], timestamp)
        self.captures.append(lfp)

        return lfp


    def _handle_trace_msg(self, packet, timestamp):
        if len(packet) != OS_TRACE_EXPECTED_SIZE:
            self.sp.reset_input_buffer()
            return None

        _, ao_id, is_queue, msg_id, _ = struct.unpack("<BB?IB", packet)
            
        if MSG_ID(msg_id) in self.filtered:
            return None

        dp = DebugMessagePackets(ao_id, msg_id, is_queue, timestamp)
        self.captures.append(dp)

        return dp

