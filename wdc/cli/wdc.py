import cmd2

from wdc.targets.zumo import ZumoTarget, MSG_ID


class WdcCLI(cmd2.Cmd):
    prompt = "(wdc) "

    def __init__(self):
        self.target = None
        self.listen = False

        super().__init__()

    def run(self):
        self.cmdloop("Welcome to warehouse-debug-console")

    def do_exit(self, arg):
        return True

    def do_EOF(self):
        return True

    def do_listen(self, args):
        self.listen = (args != "stop")

        if self.listen:
            self.target.start_listener((args == "live"))
        else:
            self.target.stop_listener()

    def do_connect(self, arg):
        """Connect to serial port"""
        self.target = ZumoTarget("/dev/cu.usbserial-0001", 115200, [MSG_ID.HEARTBEAT_MSG])

    def do_dispatch(self, arg):
        if isinstance(self.target, ZumoTarget):
            self.target.dispatch(0, 0);
    
    def do_showlog(self, arg):
        if self.target is not None:
            self.target.show_log()

    def do_resetlog(self, arg):
        if self.target is not None:
            self.target.reset_log()

    def do_disconnect(self, arg):
        """Disconnect"""
        pass

    def do_reconnect(self, arg):
        """Reconnect"""
        pass
