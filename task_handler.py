import sys

class TaskHandler:
    _press = None
    _connection_handler = None

    def __init__(self, statemachine_instance):
        self._press = statemachine_instance
        self._press.check_devices()

    def handle(self, task):
        try:
            self._press.set_task_id(task["id"])
            if task["job"]["name"] == "Press calibration":
                self._press.callibrate()
                

            elif task["job"]["name"] == "Squeeze The Sample":
                self._press.move()

            elif task["job"]["name"] == "Release The Sample":
                self._press.finalize()
                self._press.process_data()

            elif task["job"]["name"] == "process data":
                pass

            else:
                print(f"Unhandled task:\n {task}")
                return False

            return True

        except KeyboardInterrupt:
            sys.exit()
            return False