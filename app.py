from state_machine import PressMachine
from connection_handler import ConnectionHandler
from task_handler import TaskHandler
import RPi.GPIO as GPIO
from devices import StepperDrivers
import threading
# import RPi.GPIO as GPIO
from time import sleep
import json
import sys

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

with open('config.json', 'r') as f:
    config = json.load(f)

class App:
    _conn_handler = ConnectionHandler()
    _press = PressMachine(_conn_handler.post_value)
    _task_handler = TaskHandler(_press)

    def start(self):
        # self._press.check_devices()

        while True:
            task = self._conn_handler.get_task()
            if task and task.get("job", False) and not task.get("done", True):
                if self._task_handler.handle(task):
                    self._conn_handler.patch_done_flag(task["id"])
            else:
                sleep(5)


app = App()
app.start()


