
import threading

class Target:
    def __init__(self):
        self.listener_thread = None
        self.listener_running = False
        self.live_log = False

    def listen(self):
        pass

    def start_listener(self, live):
        self.live_log = live

        if self.listener_thread is not None:
            self.stop_listener()
        
        self.listener_thread = threading.Thread(target=self.listen)
        self.listener_running = True 
        self.listener_thread.start() 

    def stop_listener(self):
        self.listener_running = False
        self.listener_thread.join()
        self.listener_thread = None

    def show_log(self):
        pass
