from LS7366R_Raspberry_Pi.LS7366R_Rpi import LS7366R
from threading import Thread, Event
import threading
from time import sleep
import RPi.GPIO as GPIO
import minimalmodbus


def show(exc_type, exc_value, exc_traceback):
    print("BLEE")
    # print(exc_type, exc_value, exc_traceback)

class Device(Thread):
    is_exception = False
    exc = None

    def __init__(self, cancel_func, settings=dict(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._limit = None
        self._pause_flag = Event() # The flag used to pause the thread
        self._pause_flag.set() # Set to True
        self._stop = False
        self._cancel_func = cancel_func

        self.current_value = 0

    def pause(self):
        self._pause_flag.clear() # Set to False to block the thread

    def resume(self):
        self._pause_flag.set() # Set to True, let the thread stop blocking

    def stop(self):
        self._stop = True

    def reset_value(self):
        self.current_value = 0

    def get_status(self):
        return None


class StepperDrivers(Device):
    DIRECTIONS = {"up" : GPIO.HIGH, "down" : GPIO.LOW}

    def __init__(self, cancel_func, settings=dict(), *args, **kwargs):
        super().__init__(cancel_func, *args, **kwargs)

        self.direction = GPIO.HIGH
        self.pul = settings["PUL"]
        self.pul_2 = settings["PUL_2"]
        self.dir = settings["DIR"]
        self.dir_2 = settings["DIR_2"]
        self._std_delay = 1/settings["pulse_freq"]
        self._test_delay = 1/settings["test_pulse_freq"]
        self._delay = self._std_delay

        self.current_value = 0
        self.move_stamp = False

        GPIO.setup(self.pul, GPIO.OUT)
        GPIO.setup(self.pul_2, GPIO.OUT)
        GPIO.setup(self.dir, GPIO.OUT)
        GPIO.setup(self.dir_2, GPIO.OUT)

    def run(self, *args, **kwargs):
        self.current_value = 0

        while self.move_stamp and not self._stop:
            self._pause_flag.wait()
            GPIO.output(self.pul, GPIO.HIGH)
            GPIO.output(self.pul_2, GPIO.HIGH)
        
            sleep(self._delay)

            GPIO.output(self.pul, GPIO.LOW)
            GPIO.output(self.pul_2, GPIO.LOW)

            self.current_value += 1

            sleep(self._delay)

    def lock_movement(self):
        self.move_stamp = False

    def unlock_movement(self):
        self.move_stamp = True

    def set_test_delay(self, is_test):
        if is_test:
            self._delay = self._test_delay
        else:
            self._delay = self._std_delay

    def set_direction(self, direction):
        self.direction = self.DIRECTIONS[direction]
        GPIO.output(self.dir, self.direction)
        GPIO.output(self.dir_2, self.direction)

class TensometerAmplifier(Device):
    def __init__(self, cancel_func, settings=dict() , *args, **kwargs):
        super().__init__(cancel_func, *args, **kwargs)

        self._instrument = minimalmodbus.Instrument(settings["usb_device"], 1)
        self._instrument.serial.baudrate = settings["baudrate"]
        self._instrument.serial.stopbits = settings["stopbits"]
        self._delay = 1/settings["read_freq"]
        self.reset_value()

    def run(self, *args, **kwargs):
        try:
            while not self._stop:
                self._pause_flag.wait()
                self.current_value = self._instrument.read_register(0)
         
                sleep(self._delay)
        except Exception as e:
            if not self.is_exception:
                self.is_exception = True
                self.exc = e
                self._cancel_func()

    def reset_value(self):
        self._instrument.write_bit(4000,True)

class ScaleCounter(Device):
    def __init__(self, cancel_func, settings=dict(), *args, **kwargs):
        super().__init__(cancel_func, *args, **kwargs)
        self._instrument = LS7366R(settings["CS_line"], settings["CLK"], settings["byte_mode"])
        self._delay = 1/settings["read_freq"]

    def run(self, *args, **kwargs):
        while not self._stop: 
            self._pause_flag.wait()
            self.current_value = self._instrument.readCounter()
            sleep(self._delay)

    def reset_value(self):
        self._instrument.clearCounter()

    def get_status(self):
        return self._instrument.readStatus()
