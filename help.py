from devices import StepperDrivers
import RPi.GPIO as GPIO
import json
with open('config.json', 'r') as f:
    config = json.load(f)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

stepper_motors = StepperDrivers(None, None, config["stepper_drivers_settings"])
stepper_motors.set_direction("up")
stepper_motors.unlock_movement()
stepper_motors.start()