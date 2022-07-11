from devices import StepperDrivers, TensometerAmplifier, ScaleCounter, Device
from statemachine import StateMachine, State
from time import sleep
import logging
from datetime import datetime
import json
import csv
import sys
import os

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class PressMachine(StateMachine):
    
    def __init__(self, send_data_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.send_data_callback = send_data_func
        
    initial = State("Initial", initial=True)
    preparation = State("Preparation")
    ready = State("Ready")
    data_collection = State("Data collection")
    standby = State("Standby")
    failed = State("Failed")
    terminate = State("Terminate")
    
    check_devices = initial.to(preparation)
    callibrate = preparation.to(ready)
    move = ready.to(data_collection)
    finalize = data_collection.to(standby)
    process_data = standby.to(preparation)

    cancel = failed.from_(initial, preparation, ready, data_collection, standby, failed)
    exit = terminate.from_(failed, standby)

    current_data = None
    config = None


    def on_check_devices(self):
        logging.debug("EVENT: INITIAL - PREPARATION")
        with open('config.json', 'r') as f:
            self.config = json.load(f)

        self.stepper_motors = StepperDrivers(self.cancel, self.send_data_callback, self.config["stepper_drivers_settings"], daemon=True)
        self.amplifier = TensometerAmplifier(self.cancel, self.send_data_callback, self.config["modbus_amplifier_settings"], daemon=True)
        self.magnetic_scale = ScaleCounter(self.cancel, self.send_data_callback, self.config["spi_scale_counter_settings"], daemon=True)

        self.amplifier.start()
        self.magnetic_scale.start()
        self.stepper_motors.unlock_movement()
        self.stepper_motors.start()

        self.stepper_motors.pause()
        self.amplifier.pause()
        self.magnetic_scale.pause()

        self.amplifier.pause_send_data()
        self.magnetic_scale.pause_send_data()

    def on_callibrate(self):
        logging.debug("EVENT: PREPARATION -> READY")
        starting_height = self.config["general_settings"]["starting_height"]

        self.amplifier.resume()
        self.magnetic_scale.resume()

        self.stepper_motors.set_test_delay(False)

        self.stepper_motors.set_direction("down")
        self.stepper_motors.resume()

        while self.amplifier.current_value <= 2:
            sleep(0.0001)
            continue

        self.amplifier.pause()
        self.stepper_motors.pause()
        self.stepper_motors.set_direction("up")
        self.magnetic_scale.reset_value()
        self.stepper_motors.set_test_delay(True)#should be True
        self.stepper_motors.resume()
        print("TEST:")
        print(abs(self.magnetic_scale.current_value))

        while abs(self.magnetic_scale.current_value) < starting_height:
            sleep(0.09)
            print(abs(self.magnetic_scale.current_value))
        self.stepper_motors.pause()
        # self.stepper_motors.set_test_delay(True)#Delete
        self.stepper_motors.set_direction("down")

    def on_move(self):
        logging.debug("EVENT: READY -> DATA COLLECTION")
        is_ready = False
        self.current_data = list()

        max_force = self.config["general_settings"]["max_force"]

        # while not is_ready:
        #     is_ready = input("Ready? Type 'yes': ") == "yes"

        initial_height = self.magnetic_scale.current_value
        self.amplifier.reset_value()
        self.amplifier.resume()
        self.stepper_motors.resume()
        # sleep(1) # only for mock version
        self.amplifier.resume_send_data()
        self.magnetic_scale.resume_send_data()

        while self.amplifier.current_value <= max_force:
            self.current_data.append((self.amplifier.current_value, self.magnetic_scale.current_value))
            sleep(0.001)
            continue
        # sleep(1) # only for mock version
        self.amplifier.pause_send_data()
        self.magnetic_scale.pause_send_data()
        self.stepper_motors.pause()
        self.amplifier.pause()
        self.magnetic_scale.pause()


    def on_finalize(self):
        logging.debug("EVENT: DATA COLECTION -> STANDBY")
        starting_height = self.config["general_settings"]["starting_height"]

        self.stepper_motors.set_direction("up")
        self.stepper_motors.set_test_delay(False)
        self.magnetic_scale.reset_value()

        self.magnetic_scale.resume()
        self.amplifier.resume()
        self.stepper_motors.resume()

        while self.magnetic_scale.current_value < starting_height:
            sleep(0.001)
            continue

        is_ready = False

        self.magnetic_scale.pause()
        self.amplifier.pause()
        self.stepper_motors.pause()

        # while not is_ready:
        #     is_ready = input("The sample was taken? Type 'yes': ") == "yes"
        sleep(1) # only for mock version

    def on_process_data(self):
        logging.debug("EVENT: STANDBY -> PREPARATION")
        current_time = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
        force_index = 0
        height_index = 1
        is_ready = False

        last_zero_index = 0
        for ind, measurement in enumerate(self.current_data):
            if measurement[force_index] <= 0:
                last_zero_index = ind

        data = self.current_data[last_zero_index:]

        first_height_value = data[0][height_index]

        data = [(measurement[force_index], -1 * (measurement[height_index] - first_height_value)) for measurement in data]

        with open(f"data_{current_time}.csv", "w", newline="") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerows(data)

        self.current_data = list()

        # while not is_ready:
        #     input_val = input("Perform another test? Type 'yes' or 'no': ")
        #     if input_val == "yes":
        #         is_ready = True
        #     elif input_val == "no":
        #         is_ready = True
        #         self.exit()
        sleep(1) # only for mock version

    def on_enter_failed(self):
        self.stepper_motors.pause()
        self.amplifier.pause()
        self.magnetic_scale.pause()

        print(f"\nCURRENT EVENT: {self.current_state}", file=sys.stderr)
        print(f"\nSTEPPER DRIVERS STATUS: {self.stepper_motors.get_status()}\n"
                f"TENSOMETER AMPLIFIER STATUS: {self.amplifier.get_status()}\n"
                f"MAGNETIC SCALE STATUS: {self.magnetic_scale.get_status()}",
                file=sys.stderr)

        self.stepper_motors.stop()
        self.amplifier.stop()
        self.magnetic_scale.stop()
        self.exit()

    def on_enter_terminate(self):
        os._exit(0)

    def set_task_id(self, task_id):
        Device.CURRENT_TASK_ID = task_id
  