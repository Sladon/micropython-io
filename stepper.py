from machine import Pin
from utime import sleep_us, sleep_ms

MICRO_TO_SECOND: int = 1e6

class DriverA4988:
    
    STEPS = 200

    STEP_MODES = {
        "full": {"states": [0, 0, 0], "multiplier": 1},
        "1/2":  {"states": [1, 0, 0], "multiplier": 2},
        "1/4":  {"states": [0, 1, 0], "multiplier": 4},
        "1/8":  {"states": [1, 1, 0], "multiplier": 8},
        "1/16": {"states": [1, 1, 1], "multiplier": 16}
    }

    MESSAGES = {
        "enable": {0: "FET outputs enabled", 1: "FET outputs disabled"},
        "sleep": {0: "Sleeping", 1: "Awake"},
        "reset": {0: "Can't get input", 1: "Waiting inputs"}
    }

    def __init__(
            self, direction: int or Pin, step: int or Pin, enable: int or Pin = None, ms1: int or Pin = None,
            ms2: int or Pin = None, ms3: int or Pin = None, sleep: int or Pin = None, reset: int or Pin = None,
                ):
        
        self.__mode = "full"
        self.position = 0
        self.away_from_origin = 0
        self.__rpm = 0
        self.__delay = 0

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

    def __toggle_state(self, tg_pin: Pin, tg_msg: str, toggle: bool, get_str: bool):
        if toggle: tg_pin.value(not tg_pin.value())
        return tg_pin.value() if not get_str else tg_msg[tg_pin.value()]
        
    def enable(self, toggle: bool = False, get_str:bool = False):
        return self.__toggle_state(self.enable_pin, self.MESSAGES["enable"], toggle, get_str)
    
    def sleep(self, toggle: bool = False, get_str:bool = False):
        return self.__toggle_state(self.sleep_pin, self.MESSAGES["sleep"], toggle, get_str)
    
    def reset(self, toggle: bool = False, get_str:bool = False):
        return self.__toggle_state(self.reset_pin, self.MESSAGES["reset"], toggle, get_str)
    
    def mode(self, mode: str = None):
        if mode is not None:
            ms1, ms2, ms3 = self.STEP_MODES[mode]["states"]
            self.ms1_pin.value(ms1)
            self.ms2_pin.value(ms2)
            self.ms3_pin.value(ms3)
            self.__mode = mode
        return self.__mode
    
    def rpm(self, tg_rpm: float=None):
        if tg_rpm is not None: self.__rpm = tg_rpm
        return self.__rpm
    
    def delay(self, ):
        return int(60*MICRO_TO_SECOND / (self.STEPS * self.STEP_MODES[self.__mode]["multiplier"] * self.__rpm))
        
    def rotate(self, steps, direction):
        delay = self.delay()
        for _ in range(steps):
            self.step()
            sleep_us(delay)