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

class DriverA4988(DriverDefault):

    MICROSTEPS = {
        1:  [0, 0, 0],
        2:  [1, 0, 0],
        4:  [0, 1, 0],
        8:  [1, 1, 0],
        16: [1, 1, 1],
    }

    def __init__(
            self, step: int or Pin, direction: int or Pin, enable: int or Pin = None, ms1: int or Pin = None,
            ms2: int or Pin = None, ms3: int or Pin = None, sleep: int or Pin = None, reset: int or Pin = None,
                ):

        super().__init__(step, direction, enable)

        self.__enable_microstep = ms1 and ms2 and ms3
        if self.__enable_microstep:
            self.__ms1_pin = self.__pin(ms1)
            self.__ms2_pin = self.__pin(ms2)
            self.__ms3_pin = self.__pin(ms3)

        self.__sleep_pin = self.__pin(sleep) if sleep else None
        self.__reset_pin = self.__pin(reset) if reset else None
    
    def sleep(self):
        if self.__sleep_pin is None: return "Pin not configured"
        if self.__sleep_pin.value(): self.__sleep_pin.value(0)
    
    def awake(self):
        if self.__sleep_pin is None: return "Pin not configured"
        if not self.__sleep_pin.value():
            sleep_ms(1)
            self.__sleep_pin.value(1)

    def reset(self):
        if self.__reset_pin is None: return "Pin not configured"
        self.__reset_pin.value(0)
        self.__reset_pin.value(1)
        self.position = 0

    def microsteps(self, microsteps: int = None):
        if self.__enable_microstep and (microsteps is None or microsteps not in self.MICROSTEPS.keys()): return self.__microsteps
        self.__microsteps = microsteps

        ms1, ms2, ms3 = self.MICROSTEPS[microsteps]
        self.__ms1_pin.value(ms1)
        self.__ms2_pin.value(ms2)
        self.__ms3_pin.value(ms3)
            
        return self.__microsteps

    def rotate(self, steps):
        orientation = 1 if self.direction() else -1
        self.position += (1 / self.__microsteps * steps * orientation)
        
        for _ in range(steps):
            self.step()

class DriverTB6600(DriverDefault):

    MICROSTEPS = [2**x for x in range(6)]

    def __init__(self, step: int or Pin, direction: int or Pin, enable: int or Pin = None):
        super().__init__(step, direction, enable)

    def microsteps(self, microsteps: int = None):
        if microsteps is None or microsteps not in self.MICROSTEPS: return self.__microsteps
        self.__microsteps = microsteps
        return self.__microsteps

    # TODO: FIX Enable/Disable, probably hardware related

motor = Driver2A4988(15,2,27,26,25,14,4,23)