from machine import Pin
from time import ticks_ms, sleep

class Stepper:
    """
    Stepper class for controlling a stepper motor.

    Reference:
    - Original code from arduino-libraries available at https://github.com/arduino-libraries/Stepper.

    Attributes:
    - __direction: Direction of rotation (True for forward, False for backward)
    - __step_number: Current step the motor is on
    - __last_step_time: Timestamp in microseconds of when the last step was taken
    - __step_delay: Delay between steps in microseconds, based on motor speed
    - __number_of_steps: Total number of steps the motor can take
    - __motor_pin_1 to __motor_pin_5: Pins used for controlling the motor phases

    Methods:
    - __init__: Constructor method to initialize the Stepper object with motor parameters
    - set_speed(value): Set the speed of the stepper motor
    - step(num_steps): Move the stepper motor by a specified number of steps
    - __step_motor(this_step): Control the stepper motor to take a step based on the current step number
    """

    __STEPS = {
        2: [[0, 1],
            [1, 1]],
            
        4: [[1, 0, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 0, 1],
            [1, 0, 0, 1]],

        5: [[0, 1, 1, 0, 1],
            [0, 1, 0, 0, 1],
            [0, 1, 0, 1, 1],
            [0, 1, 0, 1, 0],
            [1, 1, 0, 1, 0],
            [1, 0, 0, 1, 0],
            [1, 0, 1, 1, 0],
            [1, 0, 1, 0, 0],
            [1, 0, 1, 0, 1],
            [0, 0, 1, 0, 1]]
    }

    __steps: list[int] = None

    __direction: bool= False    # Direction of rotation
    __step_number: int= 0       # Which step the motor is on
    __last_step_time: int= 0    # Timestamp in us of when the last step was taken

    __step_delay: int = 1       # Delay between steps, in us, based on speed
    __number_of_steps:int       # Total number of steps this motor can take

    __pins: list[Pin] = []

    def __init__(self, number_of_steps: int, pin1: int, pin2: int, pin3: int= None, pin4: int= None, pin5: int= None, steps: list[int] = None) -> None:
        """
        Initialize the Stepper object.

        Parameters:
        - number_of_steps: Total number of steps the motor can take
        - pin1 to pin5: GPIO pins connected to the stepper motor phases
        """
        self.__number_of_steps = number_of_steps
        if pin1 and pin2:
            self.__pins += [Pin(pin1, Pin.OUT), Pin(pin2, Pin.OUT)]

            if pin3 and pin4:
                self.__pins += [Pin(pin3, Pin.OUT), Pin(pin4, Pin.OUT)]

                if pin5: 
                    self.__pins += [Pin(pin5, Pin.OUT)]
        
        if steps: self.__steps = steps
        else:
            self.__steps = self.__STEPS[len(self.__pins)]

    def set_speed(self, value: int) -> None:
        """
        Sets the speed in revs per minute.

        Parameters:
        - value: Speed value, affecting the delay between steps.
        """
        self.__step_delay = 60 * 1000 * 1000 / self.__number_of_steps / value

    def step(self, num_steps: int) -> None:
        """
        Move the stepper motor by a specified number of steps.

        Parameters:
        - num_steps: Number of steps to move the motor (positive for forward, negative for backward).
        """

        if num_steps < 0: self.__direction = False
        else: self.__direction = True

        steps_left: int = abs(num_steps)

        while (steps_left > 0):
            now: int = ticks_ms()

            if now - self.__last_step_time >= self.__step_delay:
                self.__last_step_time = now
                
                if self.__step_number == self.__number_of_steps and self.__direction:
                    self.__step_number = 0
                elif self.__step_number == 0 and not self.__direction:
                    self.__step_number = self.__number_of_steps

                self.__step_number += 1 if self.__direction else -1

                steps_left -= 1

                self.__step_motor(self.__step_number % len(self.__steps))
            
            else: sleep(self.__step_delay/1000000)

    def __step_motor(self, this_step: int) -> None:
        """
        Control the stepper motor to take a step based on the current step number.

        Parameters:
        - this_step: Current step number for motor control.
        """
        step = self.__steps[this_step]
        
        for i in range(len(step)):
            self.__pins[i].value(step[i * (1 if self.__direction else -1)])

class Stepper28BYJ48(Stepper):
    """
    Stepper28BYJ48 class extends the Stepper class to specifically control a 28BYJ-48 stepper motor using 
    uln2003 driver board.

    Connection between 28BYJ-48 Stepper Motor and ULN2003 Driver Board:
    - Plug the stepper into the ULN2003

    Connection between ESP-32 and ULN2003 Driver Board:
    - Pin1 (IN1) on the ULN2003 connects to the GPIO pin controlling the first phase of the stepper motor.
    - Pin2 (IN2) on the ULN2003 connects to the GPIO pin controlling the second phase of the stepper motor.
    - Pin3 (IN3) on the ULN2003 connects to the GPIO pin controlling the third phase of the stepper motor.
    - Pin4 (IN4) on the ULN2003 connects to the GPIO pin controlling the fourth phase of the stepper motor.
    - VCC on the ULN2003 connects to the power supply (usually +5V).
    - GND on the ULN2003 connects to the ground of the power supply.
    """

    def __init__(self, pin1: int, pin2: int, pin3: int, pin4: int, number_of_steps: int = 2048) -> None:
        Stepper.__init__(self, number_of_steps, pin1, pin2, pin3, pin4)

class Stepper28BYJ48v2(Stepper):
    """
    Stepper28BYJ48 class extends the Stepper class to specifically control a 28BYJ-48 stepper motor using 
    uln2003 driver board.

    Connection between 28BYJ-48 Stepper Motor and ULN2003 Driver Board:
    - Plug the stepper into the ULN2003

    Connection between ESP-32 and ULN2003 Driver Board:
    - Pin1 (IN1) on the ULN2003 connects to the GPIO pin controlling the first phase of the stepper motor.
    - Pin2 (IN2) on the ULN2003 connects to the GPIO pin controlling the second phase of the stepper motor.
    - Pin3 (IN3) on the ULN2003 connects to the GPIO pin controlling the third phase of the stepper motor.
    - Pin4 (IN4) on the ULN2003 connects to the GPIO pin controlling the fourth phase of the stepper motor.
    - VCC on the ULN2003 connects to the power supply (usually +5V).
    - GND on the ULN2003 connects to the ground of the power supply.
    """

    def __init__(self, pin1: int, pin2: int, pin3: int, pin4: int, number_of_steps: int = 4096, steps: list[int]= [
            [1, 1, 1, 0],
            [1, 1, 0, 0],
            [1, 1, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 1, 1],
            [0, 0, 1, 1],
            [0, 1, 1, 1],
            [0, 1, 1, 0]
        ]) -> None:
        Stepper.__init__(self, number_of_steps, pin1, pin2, pin3, pin4, steps=steps)