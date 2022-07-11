import sys
from threading import Thread, Event

from connection_handler import ConnectionHandler

class TaskHandler:
    _press = None
    _connection_handler = None

    def __init__(self, statemachine_instance):
        self._press = statemachine_instance
        self._press.check_devices()

        
        stopFlag = Event()
        thread = StopperThread(stopFlag)
        thread.start()


    def handle(self, task):
        try:
            if task["name"] == "callibration":
                self._press.callibrate()
                self._press.config["general_settings"]["max_force"] = task["maxForce"]
                self._press.config["general_settings"]["starting_height"] = task["startingHeight"]
                # self._press.config["general_settings"]["max_force"] = task["maxForce"]

            elif task["name"] == "Squeeze The Sample":
                self._press.move()
                self._press.finalize()
                self._press.process_data()

            else:
                print(f"Unhandled task:\n {task}")
                return False

            return True

        except KeyboardInterrupt:
            sys.exit()
            return False

class StopperThread(Thread):
        def __init__(self, event):
            Thread.__init__(self)
            self.stopped = event
            self._connection_handler = ConnectionHandler()

        def run(self):
            while not self.stopped.wait(5):
                if(self._connection_handler.get_stop_flag() != None and self._connection_handler.get_stop_flag().get("stop", True)):
                    sys.exit()
