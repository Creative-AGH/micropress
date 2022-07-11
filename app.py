from state_machine import PressMachine
from devices import StepperDrivers
import threading
import RPi.GPIO as GPIO
from time import sleep
import json
import sys


with open('config.json', 'r') as f:
    config = json.load(f)



GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


press = PressMachine()
exception_showed = False


press.check_devices()

try:
    while True:
        press.callibrate()
        press.move()
        press.finalize()
        press.process_data()
except KeyboardInterrupt:
    sys.exit()


