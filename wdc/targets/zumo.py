import serial
import struct
import datetime
from enum import Enum, IntEnum

from wdc.targets.target import Target
from pystcp import Status, EngineState, StcpEngine


DISPATCH_MSG_ID = 0x1

START_LINE_FOLLOW_MSG_ID = 0xD
START_LF_TURN_MSG_ID =  0xE
START_180_TURN_MSG_ID = 0xF

SET_P_MSG_ID = 0x20
GET_P_MSG_ID = 0x10
GET_P_RESPONSE_MSG_ID = 0x11
EXPECTED_GET_P_RESPONSE_SIZE = 5

OS_TRACE_MSG_ID = 0x2
OS_TRACE_EXPECTED_SIZE = 7

DRIVE_CTL_TRACE_MSG_ID = 0x3
DRIVE_CTL_EXPECTED_SIZE = 17

DRIVE_CTL_TRACE_INIT_MSG_ID = 0x4
DRIVE_CTL_INIT_EXPECTED_SIZE = 5

LINE_FOLLOW_MSG_ID = 0x5
LINE_FOLLOW_EXPECTED_SIZE = 13


FOOTER = b"\x7F\x7F"

class PTYPE(IntEnum):
    FLOAT = 0,
    BOOL = 1,
    U8 = 2,
    I8 = 3,
    U16 = 4,
    I16 = 5,
    U32 = 6,
    I32 = 7,


class PROPERTY_ID(IntEnum):
    DRIVE_DEADBAND = 0x0,
    DRIVE_CTL_LOOP_PERIOD = 0x1,
    DRIVE_kP = 0x2,
    DRIVE_kI = 0x3,
    DRIVE_kD = 0x4,
    DRIVE_BASE_OUTPUT = 0x5,
    DRIVE_STATE = 0x6,
    DRIVE_SETPOINT = 0x7
    DRIVE_ACTUAL = 0x8
    DRIVE_I_ZONE = 0x9

class AO_ID(IntEnum):
    WATCHDOG = 0x0,
    DRIVE = 0x1,
    INPUT_CTL = 0x2,
    COMMS = 0x3,
    STATE = 0x4,
    REFARR = 0x5,
    TEST = 0x6,
    ELECTROMAGNET = 0x7,

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
    REFARR_PROCESS_READING = 0x3A,
    PUSH_BUTTON_PRESSED = 0x61,
    LIMIT_SWITCH_HIT = 0x62,
    UART_SMALL_PACKET = 0x81,
    UART_LARGE_PACKET = 0x82,
    OS_DEBUG_MSG = 0x83,
    SM_PERIODIC_EVENT = 0x100,
    SM_DISPATCH_FROM_IDLE = 0x110,
    SM_CALIBRATE_DONE = 0x120,
    GET_PROPERTY = 0x220,
    SET_PROPERTY = 0x221,
    EM_ENABLE = 0x400,
    EN_DISABLE = 0x401

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
        self.stcp = StcpEngine(self.write)
        if filtered is not None:
            self.filtered = filtered
        else:
            self.filtered = []

        super().__init__()

    def set_pid(self, p, i, d, izone=None):
        self.set_property(PROPERTY_ID.DRIVE_kP, PTYPE.FLOAT, p)
        self.set_property(PROPERTY_ID.DRIVE_kI, PTYPE.FLOAT, i)
        self.set_property(PROPERTY_ID.DRIVE_kD, PTYPE.FLOAT, d)
        if izone is not None:
            self.set_property(PROPERTY_ID.DRIVE_I_ZONE, PTYPE.FLOAT, izone);

    def get_pid(self):
        pid = {}
        pid["p"] = self.get_property(PROPERTY_ID.DRIVE_kP, PTYPE.FLOAT)
        pid["i"] = self.get_property(PROPERTY_ID.DRIVE_kI, PTYPE.FLOAT)
        pid["d"] = self.get_property(PROPERTY_ID.DRIVE_kD, PTYPE.FLOAT)
        pid["izone"] = self.get_property(PROPERTY_ID.DRIVE_I_ZONE, PTYPE.FLOAT)

        return pid

    def drive_enable(self):
        self.set_property(PROPERTY_ID.DRIVE_STATE, PTYPE.U32, 1)

    def drive_disable(self):
        self.set_property(PROPERTY_ID.DRIVE_STATE, PTYPE.U32, 0)

    def drive_set_setpoint(self, sp):
        self.set_property(PROPERTY_ID.DRIVE_SETPOINT, PTYPE.FLOAT, sp)

    def read(self):
        raw = self.sp.read_until(FOOTER)
        return self.stcp.handle_message(raw)

    def write(self, msg):
        self.sp.write(msg)

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

    def dispatch(self, aisle: int, bay: int) -> None:
        self.stcp.write(struct.pack("<BBB", DISPATCH_MSG_ID, aisle, bay))

    def start_line_follow(self, count: int, base_velocity: float) -> None:
        self.stcp.write(struct.pack("<BBf", START_LINE_FOLLOW_MSG_ID, count, base_velocity))

    def start_turn(self, left_out: float, right_out: float, mode: int, base_velocity: float) -> None:
        self.stcp.write(struct.pack("<BBfff", START_LF_TURN_MSG_ID, mode, base_velocity, left_out, right_out))

    def start_180_turn(self, left_out: float, right_out: float, mode: int, base_velocity: float, rev_velocity: float, post_turn_left: float, post_turn_right: float) -> None:
        self.stcp.write(struct.pack("<BBffffff", START_180_TURN_MSG_ID, mode, base_velocity, left_out, right_out, rev_velocity, post_turn_left, post_turn_right))

    def get_property(self, pid, ptype):
        self.sp.reset_input_buffer()
        get_msg = struct.pack("<BH", GET_P_MSG_ID, pid)
        self.stcp.write(get_msg)
        packet = self.read()
        if len(packet) != EXPECTED_GET_P_RESPONSE_SIZE:
            return
        
        if ptype == PTYPE.FLOAT:
            _, v = struct.unpack("<Bf", packet)
        elif ptype == PTYPE.BOOL:
            _, v = struct.unpack("<B?xxx", packet)
        elif ptype == PTYPE.U8:
            _, v = struct.unpack("<BBxxx", packet)
        elif ptype == PTYPE.I8:
            _, v = struct.unpack("<Bbxxx", packet)
        elif ptype == PTYPE.U16:
            _, v = struct.unpack("<BHxx", packet)
        elif ptype == PTYPE.I16:
            _, v = struct.unpack("<Bhxx", packet)
        elif ptype == PTYPE.U32:
            _, v = struct.unpack("<BI", packet)
        elif ptype == PTYPE.I32:
            _, v = struct.unpack("<Bi", packet)
    
        return v

    def set_property(self, pid, ptype, value):
        if ptype == PTYPE.FLOAT:
            set_msg = struct.pack("<BHf", SET_P_MSG_ID, pid, value)
        elif ptype == PTYPE.BOOL:
            set_msg = struct.pack("<BH?xxx", SET_P_MSG_ID, pid, value)
        elif ptype == PTYPE.U8:
            set_msg = struct.pack("<BHBxxx", SET_P_MSG_ID, pid, value)
        elif ptype == PTYPE.I8:
            set_msg = struct.pack("<BHbxxx", SET_P_MSG_ID, pid, value)
        elif ptype == PTYPE.U16:
            set_msg = struct.pack("<BHHxx", SET_P_MSG_ID, pid, value)
        elif ptype == PTYPE.I16:
            set_msg = struct.pack("<BHhxx", SET_P_MSG_ID, pid, value)
        elif ptype == PTYPE.U32:
            set_msg = struct.pack("<BHI", SET_P_MSG_ID, pid, value)
        elif ptype == PTYPE.I32:
            set_msg = struct.pack("<BHi", SET_P_MSG_ID, pid, value)

        self.stcp.write(set_msg)
        

    def start_listener(self, live=False):
        super().start_listener(live)

    def stop_listener(self):
        self.sp.cancel_read()
        super().stop_listener()
    
    def listen(self):
        self.sp.reset_input_buffer()
        
        while self.listener_running:
            packet = self.read()
            timestamp = datetime.datetime.now()

            if len(packet) == 0:
                continue
            
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

        _, lo, ro, error, actual  = struct.unpack("<Bffff", packet)

        cp = DriveCtlTracePacket(lo, ro, error, actual, timestamp)

        self.captures.append(cp)

        return cp

    def _handle_drive_ctl_init_msg(self, packet, timestamp):
        if len(packet) != DRIVE_CTL_INIT_EXPECTED_SIZE:
            return None

        _, sp = struct.unpack("<Bf", packet)

        initp = DriveCtlInitPacket(sp, timestamp)
        self.captures.append(initp)


    def _handle_line_follow_trace_msg(self, packet, timestamp):
        if len(packet) != LINE_FOLLOW_EXPECTED_SIZE:
            self.sp.reset_input_buffer()
            return None

        _, s0, s1, s2, s3, s4, s5 = struct.unpack("<BHHHHHH", packet)

        lfp = LineFollowTracePacket([s0, s1, s2, s3, s4, s5], timestamp)
        self.captures.append(lfp)

        return lfp


    def _handle_trace_msg(self, packet, timestamp):
        if len(packet) != OS_TRACE_EXPECTED_SIZE:
            self.sp.reset_input_buffer()
            return None

        _, ao_id, is_queue, msg_id = struct.unpack("<BB?I", packet)
            
        if MSG_ID(msg_id) in self.filtered:
            return None

        dp = DebugMessagePackets(ao_id, msg_id, is_queue, timestamp)
        self.captures.append(dp)

        return dp

