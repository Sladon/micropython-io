from machine import Pin
from utime import sleep_us, sleep_ms

MICRO_TO_SECOND: int = 1e6

class DriverA4988:
    
    STEPS = 256

    STEP_MODES = {
        "full": {"states": [0, 0, 0], "multiplier": 1},
        "half": {"states": [1, 0, 0], "multiplier": 2},
        "1/4":  {"states": [0, 1, 0], "multiplier": 4},
        "1/8":  {"states": [1, 1, 0], "multiplier": 8},
        "1/16": {"states": [1, 1, 1], "multiplier": 16}

    }

    def __init__(
            self, direction: int or Pin, step: int or Pin, enable: int or Pin = None, ms1: int or Pin = None,
            ms2: int or Pin = None, ms3: int or Pin = None, sleep: int or Pin = None, reset: int or Pin = None,
                ):
        
        self.current_mode = "full"
        self.position = 0

        self.dir_pin = self.__pin(direction)
        self.step_pin = self.__pin(step)

        #* The following pins are not required to be connected to use the stepper motor
        self.enable_pin = self.__pin(enable) if enable else None #* If used, when LOW all FET outputs are enabled, off when HIGH

        self.step_control = ms1 and ms2 and ms3
        if self.step_control:
            self.ms1_pin = self.__pin(ms1)
            self.ms2_pin = self.__pin(ms2)
            self.ms3_pin = self.__pin(ms3)

        #* If not needed, connect sleep with reset to enable the driver
        self.sleep_pin = self.__pin(sleep) if sleep else None #* If used, when LOW sleep mode enabled
        self.reset_pin = self.__pin(reset) if reset else None #* All step inputs are ignored if LOW

    def __pin(self, pin):
        """
        Adds a pin to the list of pins connected to the stepper motor.

        Parameters:
        - pin: Either an instance of the Pin class or an integer representing the GPIO pin number.
        
        Raises:
        - TypeError: If the pin value is not of type 'int' or 'Pin'.
        """
        if isinstance(pin, Pin): return pin
        elif isinstance(pin, int): return Pin(pin, Pin.OUT)
        else: raise TypeError("pin value must be of type 'int' or 'Pin'")
        
    def step(self):
        self.step_pin.value(not self.step_pin.value())
        self.step_pin.value(not self.step_pin.value())
        
    def enable(self, state: bool or int = None, get_str:bool = False):
        if state is not None: self.enable_pin.value(state)
        str_result = "FET outputs disabled" if self.enable_pin.value() else "FET outputs enabled"
        return self.enable_pin.value() if not get_str else str_result
    
    def sleep(self, state: bool or int = None, get_str:bool = False):
        if state is not None:
            self.sleep_pin.value(state)
            if self.sleep_pin.value(): sleep_ms(1)
        str_result = "AWAKE" if self.sleep_pin.value() else "SLEEP"
        return self.sleep_pin.value() if not get_str else str_result
    
    def reset(self, state: bool or int = None, get_str:bool = False):
        if state is not None: self.reset_pin.value(state)
        str_result = "Waiting input" if self.reset_pin.value() else "No input"
        return self.reset_pin.value() if not get_str else str_result
    
    def mode(self, mode: str = None):
        if mode is not None:
            ms1, ms2, ms3 = self.STEP_MODES[mode]["states"]
            self.ms1_pin.value(ms1)
            self.ms2_pin.value(ms2)
            self.ms3_pin.value(ms3)
            self.current_mode = mode
        return self.current_mode
    
    def delay(self, delay: int)
        
    def rotate(self, steps, delay, direction):
        for _ in range(steps):
            self.step()
            sleep_us(delay)