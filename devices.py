from threading import Thread, Event, Timer
from time import sleep

import RPi.GPIO as GPIO
import minimalmodbus
from LS7366R_Raspberry_Pi.LS7366R_Rpi import LS7366R

class Device(Thread):
    is_exception = False
    exc = None
    CURRENT_TASK_ID = None

    def __init__(self, cancel_func, conn_handler_callback, settings=dict(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._limit = None
        self._pause_flag = Event() # The flag used to pause the thread
        self._pause_flag.set() # Set to True
        self._stop = False
        self._pause_send_data = Event()
        self._cancel_func = cancel_func
        self._conn_handler_callback = conn_handler_callback

        self.current_value = 0

    def pause(self):
        self._pause_flag.clear() # Set to False to block the thread

    def resume(self):
        self._pause_flag.set() # Set to True, let the thread stop blocking

    def pause_send_data(self):
        self._pause_send_data = True

    def resume_send_data(self):
        self._pause_send_data = False 

    def stop(self):
        self._stop = True

    def reset_value(self):
        self.current_value = 0

    def get_status(self):
        return None
    
    def _send_status(self, property_id, entity_name):
        period = 0.1 #seconds
        if not self._pause_send_data: 
            self._conn_handler_callback(entity_name, property_id, self.current_value, self.CURRENT_TASK_ID)
        Timer(period, self._send_status, [property_id, entity_name]).start()


class StepperDrivers(Device):
    DIRECTIONS = {"up" : GPIO.HIGH, "down" : GPIO.LOW}

    def __init__(self, cancel_func, conn_handler_callback, settings=dict(), *args, **kwargs):
        super().__init__(cancel_func, conn_handler_callback, *args, **kwargs)

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
    def __init__(self, cancel_func, conn_handler_callback, settings=dict() , *args, **kwargs):
        super().__init__(cancel_func, conn_handler_callback, *args, **kwargs)

        self._instrument = minimalmodbus.Instrument(settings["usb_device"], 1)
        self._instrument.serial.baudrate = settings["baudrate"]
        self._instrument.serial.stopbits = settings["stopbits"]
        self._delay = 1/settings["read_freq"]
        self.reset_value()

    def run(self, *args, **kwargs):
        property_id = 120 # pressure force
        entity_name = "Pressure force"
        self._pause_send_data = True
        self._send_status(property_id, entity_name)
        try:
            while not self._stop:
                self._pause_flag.wait()
                self.current_value = self._instrument.read_register(0)
                sleep(self._delay)
        except Exception as e:
            self._pause_send_data = True
            if not self.is_exception:
                self.is_exception = True
                self.exc = e
                self._cancel_func()

    def reset_value(self):
        self._instrument.write_bit(4000,True)

class ScaleCounter(Device):
    def __init__(self, cancel_func, conn_handler_callback, settings=dict(), *args, **kwargs):
        super().__init__(cancel_func, conn_handler_callback, *args, **kwargs)
        self._instrument = LS7366R(settings["CS_line"], settings["CLK"], settings["byte_mode"])
        self._delay = 1/settings["read_freq"]

    def run(self, *args, **kwargs):
        property_id = 129 # distance
        entity_name = "Distance"
        self._pause_send_data = True
        self._send_status(property_id, entity_name)
        try:
            while not self._stop: 
                self._pause_flag.wait()
                self.current_value = self._instrument.readCounter()
                sleep(self._delay)
        except Exception as e:
            self._pause_send_data = True

    def reset_value(self):
        self._instrument.clearCounter()

    def get_status(self):
        return self._instrument.readStatus()
