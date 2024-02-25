from machine import Pin
from utime import sleep_ms, ticks_us, sleep_us

MICRO_TO_SECOND: int = 1e6

class DriverDefault:

    STEPS = 200

    def __init__(self, step: int or Pin, direction: int or Pin, enable: int or Pin = None, microsteps: int = 1):

        self.__step_pin = self.__pin(step)
        self.__dir_pin = self.__pin(direction)
        if enable is not None: self.__enable_pin = self.__pin(enable)

        self.__microsteps = microsteps
        self.position = 0.0
        self.__rpm = 0.0

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
        delay = self.delay()
        prev_time_us = ticks_us()
        times = 2
        self.__step_pin.value(0)
        while True:
            current_time_us = ticks_us()
            if current_time_us - prev_time_us > delay:
                self.__step_pin.value(1)
                prev_time_us = ticks_us()
                break

    def microsteps(self, microsteps: int = None):
        if microsteps is None: return self.__microsteps
        self.__microsteps = microsteps
        return microsteps

    def rpm(self, rpm: float=None):
        if rpm is not None: self.__rpm = rpm
        return self.__rpm
    
    def enable(self):
        if self.__enable_pin is None: return "Pin not configured"
        if self.__enable_pin.value(): self.__enable_pin.value(0)
    
    def disable(self):
        if self.__enable_pin is None: return "Pin not configured"
        if not self.__enable_pin.value(): self.__enable_pin.value(1)

    def direction(self, direction:  bool = None):
        if direction is None: return self.__dir_pin.value()
        self.__dir_pin.value(direction)
        return self.__dir_pin.value()

    def delay(self, ):
        return int(60*MICRO_TO_SECOND / (self.STEPS * self.__microsteps * self.__rpm))

    def rotate(self, steps):
        orientation = 1 if self.direction() else -1
        self.position += (1 / self.__microsteps * steps * orientation)
          
        for _ in range(steps):
            self.step()

class DriverA4988:
    
    STEPS = 200

    STEP_MODES = {
        "full": {"states": [0, 0, 0], "multiplier": 1},
        "1/2":  {"states": [1, 0, 0], "multiplier": 2},
        "1/4":  {"states": [0, 1, 0], "multiplier": 4},
        "1/8":  {"states": [1, 1, 0], "multiplier": 8},
        "1/16": {"states": [1, 1, 1], "multiplier": 16}
    }

    def __init__(
            self, direction: int or Pin, step: int or Pin, enable: int or Pin = None, ms1: int or Pin = None,
            ms2: int or Pin = None, ms3: int or Pin = None, sleep: int or Pin = None, reset: int or Pin = None,
                ):
        
        self.__mode = "full"
        self.position = 0.0
        self.__rpm = 0

        self.dir_pin = self.__pin(direction)
        self.step_pin = self.__pin(step)

        #* The following pins are not required to be connected to use the stepper motor
        self.enable_pin = self.__pin(enable) if enable else None # If used, when LOW all FET outputs are enabled, off when HIGH

        self.__step_control = ms1 and ms2 and ms3
        if self.__step_control:
            self.ms1_pin = self.__pin(ms1)
            self.ms2_pin = self.__pin(ms2)
            self.ms3_pin = self.__pin(ms3)

        #* If not needed, connect sleep with reset to enable the driver
        self.sleep_pin = self.__pin(sleep) if sleep else None # If used, when LOW sleep mode enabled
        self.reset_pin = self.__pin(reset) if reset else None # All step inputs are ignored if LOW
        
        self.sleep()
        self.reset()
        self.step_pin.value(0)
        self.dir_pin.value(1)
        self.enable()

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
        delay = self.delay()
        prev_time_us = ticks_us()
        times = 2
        self.step_pin.value(0)
        while True:
            current_time_us = ticks_us()
            if current_time_us - prev_time_us > delay:
                self.step_pin.value(1)
                prev_time_us = ticks_us()
                break
        
    def enable(self):
        if self.enable_pin is None: return "Pin not configured"
        if self.enable_pin.value(): self.enable_pin.value(0)
    
    def disable(self):
        if self.enable_pin is None: return "Pin not configured"
        if not self.enable_pin.value(): self.enable_pin.value(1)
    
    def sleep(self):
        if self.sleep_pin is None: return "Pin not configured"
        if self.sleep_pin.value(): self.sleep_pin.value(0)
    
    def awake(self):
        if self.sleep_pin is None: return "Pin not configured"
        if not self.sleep_pin.value():
            sleep_ms(1)
            self.sleep_pin.value(1)
    
    def reset(self):
        if self.reset_pin is None: return "Pin not configured"
        self.reset_pin.value(0)
        self.reset_pin.value(1)
        self.position = 0
        
    
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
        
    def rotate(self, steps, direction, force_mode: str = None):
        self.dir_pin.value(direction)
        orientation = 1 if direction else -1
        self.position += (1 / self.STEP_MODES[self.__mode]["multiplier"]) * steps * orientation
        
        self.awake()
        for _ in range(steps):
            self.step()
        self.sleep()

class DriverTB6600(DriverDefault):

    MICROSTEPS = [2**x for x in range(6)]

    def __init__(self, step: int or Pin, direction: int or Pin, enable: int or Pin = None, mode: str="full"):
        super().__init__(step, direction, enable)

    def microsteps(self, microsteps: int = None):
        if microsteps is None or microsteps not in self.MICROSTEPS: return self.__microsteps
        self.__microsteps = microsteps
        return microsteps

    # TODO: FIX Enable/Disable, probably hardware related