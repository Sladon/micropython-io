from machine import Pin
from utime import sleep_us

GENERIC_FULL_STEP = {
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

MICRO_TO_SECOND: int = 1e6

class Stepper:
    """
    A class representing a stepper motor controller.

    Parameters:
    - number_of_steps (int): The total number of steps the motor can take in one revolution.
    - pin1, pin2, pin3, pin4, pin5 (int or Pin): The pins connected to the stepper motor coils. 
      It can either be specified as an integer representing the GPIO pin number or as an instance
      of the Pin class.
    - full_steps (list[list[int]], optional): A matrix of integers representing the full step
                                              sequence. 
      If not provided, it defaults to a generic full step sequence based on the number of pins.
    - half_steps (list[list[int]], optional): A matrix of integers representing the half step
                                              sequence.
    - min_full_us (int, optional): The minimum delay in microseconds between full steps.
      Defaults to 10000 us.
    - min_half_us (int, optional): The minimum delay in microseconds between half steps.
      Defaults to 1000 us.

    Public Methods:
    - __init__: Initializes a Stepper instance.
    - delay(delay, method): Sets or retrieves the delay between steps based on the specified time
                            unit.
    - mode(change): Gets or sets the stepping mode of the stepper motor.
    - step(num_steps): Moves the stepper motor by the specified number of steps.
    - reset(): Resets the stepper motor to its initial position.
    - set_start(): Sets the current position as starting position
    - position(): Returns the current position

    Private Methods:
    - __add_pin(pin): Adds a pin to the list of pins connected to the stepper motor.
    - __check_delay(delay): Checks if the provided delay is within acceptable limits and adjusts
                            it if necessary.
    - __us(delay=None): Converts delay from microseconds to microseconds.
    - __sps(delay=None): Converts delay from steps per second to microseconds.
    - __rpm(delay=None): Converts delay from revolutions per minute to microseconds.
    - __clean(): Turns off all pins associated with the stepper motor.
    - __step_motor(this_step): Moves the stepper motor to the specified step position.

    Examples:
    >>> stepper = Stepper(number_of_steps=200, pin1=1, pin2=2, pin3=3, pin4=4)
    >>> stepper.delay(500, method='us')  # Set the delay to 500 microseconds
    >>> stepper.mode(True)  # Set mode to 'FullStep'
    >>> stepper.step(100)  # Move the motor 100 steps clockwise
    >>> stepper.reset()  # Reset the motor to the starting position
    """

    def __init__(
        self, number_of_steps: int, pin1: int or Pin, pin2: int or Pin,
        pin3: int = None or Pin, pin4: int or Pin = None, pin5: int or Pin = None,
        full_steps: list[list[int]] = None, half_steps: list[list[int]] = None,
        min_full_us: int= 10000, min_half_us: int= 1000
        ):
        """
        Initializes a Stepper instance.

        Parameters:
        - number_of_steps (int): The total number of steps the motor can take in one revolution.
        - pin1, pin2, pin3, pin4, pin5 (int or Pin): The pins connected to the stepper motor coils.
        - full_steps (list[list[int]], optional): A matrix of integers representing the full step sequence.
        - half_steps (list[list[int]], optional): A matrix of integers representing the half step sequence.
        - min_full_us (int, optional): The minimum delay in microseconds between full steps.
                                       Defaults to 10000 us.
        - min_half_us (int, optional): The minimum delay in microseconds between half steps.
                                       Defaults to 1000 us.
        """

        self.__number_of_steps: int = number_of_steps
        
        self.__direction: int = 1   # direction the stepper is going 1: clockwise, -1: opposite
        self.__current_step: int = 0    # current step based on a starting position

        self.__delay: int = min_full_us # delay between steps in us
        self.__step_mode: bool = True   # 

        self.__pins: list[Pin] = []
        self.__add_pin(pin1)
        self.__add_pin(pin2)

        if pin3 and pin4:
            self.__add_pin(pin3)
            self.__add_pin(pin4)

            if pin5: self.__add_pin(pin5)
    
        self.__full_steps = full_steps if full_steps else GENERIC_FULL_STEP[len(self.__pins)]
        self.__min_f_us = min_full_us

        self.__half_steps = half_steps
        self.__min_h_us = min_half_us
    
    def __add_pin(self, pin):
        """
        Adds a pin to the list of pins connected to the stepper motor.

        Parameters:
        - pin: Either an instance of the Pin class or an integer representing the GPIO pin number.
        
        Raises:
        - TypeError: If the pin value is not of type 'int' or 'Pin'.
        """
        if isinstance(pin, Pin): self.__pins.append(pin)
        elif isinstance(pin, int): self.__pins.append(Pin(pin, Pin.OUT))
        else: raise TypeError("pin value must be of type 'int' or 'Pin'")

    def delay(self, delay: float = None, method: str = 'us') -> int:
        """
        Sets or retrieves the delay between steps based on the specified time unit.

        Parameters:
        - delay (float, optional): The value of the delay to set, measured in the specified
                                   time unit.
        - method (str, optional): The time unit for the delay. Options: 'us' (microseconds),
                                  'sps'(steps per second), 'rpm' (revolutions per minute).
                                  Defaults to 'us'.

        Returns:
        - int: The current delay in the chosen method.

        Example:
        >>> stepper.delay(500, method='us')  # Set the delay to 500 microseconds
        >>> stepper.delay()  # Retrieve the current delay in microseconds
        """
        if method == 'us':              # steps per nanosecond
            if not delay: return self.__delay
            fc_method = self.__us
        elif method == 'sps':           # steps per second
            if not delay: return self.__sps()
            fc_method = self.__sps
        elif method == 'rpm':           # revolutions per minute
            if not delay: return self.__rpm()
            fc_method = self.__rpm

        time_us = self.__check_delay(fc_method(delay))
        self.__delay = time_us
        return fc_method()

    def __check_delay(self, delay: int) -> int:
        """
        Checks if the provided delay is within acceptable limits and adjusts it if necessary.

        Parameters:
        - delay (int): The delay to check and potentially adjust.

        Returns:
        - int: The adjusted delay, ensuring it meets the minimum requirements.
        """
        min_delay = self.__min_f_us if self.__step_mode else self.__min_h_us * 2
        return min_delay if delay < min_delay else int(delay)

    def __us(self, delay: float = None) -> int:
        """
        Converts delay from microseconds to microseconds.

        Parameters:
        - delay (float, optional): The delay value to convert. Defaults to the current delay.

        Returns:
        - int: The converted delay in microseconds.
        """
        if delay:
            return int(delay)
        return int(self.__delay)

    def __sps(self, delay: float = None) -> float:
        """
        Converts delay from steps per second to microseconds.

        Parameters:
        - delay (float, optional): The delay value to convert. Defaults to the current delay.

        Returns:
        - float: The converted delay in microseconds.
        """
        if delay:
            return MICRO_TO_SECOND/delay
        return MICRO_TO_SECOND/self.__delay
    
    def __rpm(self, delay: float = None) -> float:
        """
        Converts delay from revolutions per minute to microseconds.

        Parameters:
        - delay (float, optional): The delay value to convert. Defaults to the current delay.

        Returns:
        - float: The converted delay in microseconds.
        """
        if delay:
            return 60*MICRO_TO_SECOND / (self.__number_of_steps * delay)
        else:
            return 60*MICRO_TO_SECOND/ (self.__number_of_steps * self.__delay)

    def mode(self, change: bool = None) -> str:
        """
        Gets or sets the stepping mode of the stepper motor.

        Parameters:
        - change (bool, optional): If provided, changes the stepping mode to 'FullStep' (True) or
                                   'HalfStep' (False).
                                   If not provided, returns the current stepping mode.

        Returns:
        - str: The current stepping mode ('FullStep' or 'HalfStep').

        Example:
        >>> stepper.mode()  # Get current mode
        >>> stepper.mode(True)  # Set mode to 'FullStep'
        """
        if change is not None and self.__half_steps: 
            self.__step_mode = True if change else False
        return 'FullStep' if self.__step_mode else 'HalfStep'
    
    def step(self, num_steps) -> None:
        """
        Moves the stepper motor by the specified number of steps.

        Parameters:
        - num_steps (int): The number of steps to move. Positive values move the motor clockwise, 
                          negative values move it counterclockwise.

        Example:
        >>> stepper.step(100)  # Move the motor 100 steps clockwise
        >>> stepper.step(-50)  # Move the motor 50 steps counterclockwise
        """
        self.__direction = 1 if num_steps >= 0 else -1
        steps_left: int = abs(num_steps)

        delay = self.__check_delay(int(self.delay(self.__delay, method='us') / (1 if self.__step_mode else 2)))

        while (steps_left > 0):

            GreaterOrEqual = self.__current_step >= self.__number_of_steps
            LessOrEqual = self.__current_step <= 0

            if GreaterOrEqual and self.__direction == 1:
                self.__current_step = 0
            elif LessOrEqual and self.__direction == -1:
                self.__current_step = self.__number_of_steps

            self.__current_step += (0.5 if self.__step_mode else 1)*self.__direction
            
            steps_left-=1

            step_matrix_size = len(self.__full_steps if self.__step_mode else self.__half_steps)
            step_indx = int(self.__current_step * (2 if self.__step_mode else 1) % step_matrix_size)

            self.__step_motor(step_indx)

            sleep_us(delay)

    def reset(self):
        """
        Resets the stepper motor to its initial position.

        Example:
        >>> stepper.reset()
        """
        steps_diff = self.__number_of_steps - self.__current_step
        if self.__current_step < steps_diff:
            steps = -self.__current_step
        else:
            steps = steps_diff
        self.step(steps*(2 if self.__step_mode else 1))
        self.__clean()

    def set_start(self) -> None:
        """
        Sets the current position as starting position
        
        Example:
        >>> stepper.set_start()
        """
        self.__current_step = 0

    def position(self, ) -> float:
        """
        Returns the current position
        
        Example:
        >>> print(stepper.position())
        """
        return self.__current_step

    def __clean(self,):
        """
        Turns off all pins associated with the stepper motor.

        Example:
        >>> stepper.__clean()  # Turn off all motor pins
        """
        for pin in self.__pins:
            pin.value(0)
        
    def __step_motor(self, this_step: int) -> None:
        """
        Moves the stepper motor to the specified step position.

        Parameters:
        - this_step (int): The index representing the current step in the step sequence.

        Example:
        >>> stepper.__step_motor(2)  # Move the motor to the third step in the sequence
        """
        step = self.__full_steps[this_step] if self.__step_mode else self.__half_steps[this_step]
        
        for i in list(range(len(step)))[::self.__direction]:
            self.__pins[i].value(step[i*(self.__direction if self.__step_mode else 1)])

class Stepper28BYJ48(Stepper):
    """
    A specialized subclass of the Stepper class for the 28BYJ-48 stepper motor using an ul2003
    driver board.

    Attributes:
    - HALF_STEPS (list[list[int]]): Default half-step sequence for the 28BYJ-48 motor.

    Parameters:
    - pin1, pin2, pin3, pin4 (int or Pin): The pins connected to the 28BYJ-48 stepper motor coils.
    - half_steps (list[int], optional): A list of integers representing the half-step sequence.
                                        Defaults to the default sequence.
    - number_of_steps (int, optional): The total number of steps the motor can take in one revolution.
                                       Defaults to 2048.
    """

    HALF_STEPS = [
            [1, 1, 1, 0],
            [1, 1, 0, 0],
            [1, 1, 0, 1],
            [1, 0, 0, 1],
            [1, 0, 1, 1],
            [0, 0, 1, 1],
            [0, 1, 1, 1],
            [0, 1, 1, 0]
        ]

    def __init__(self, pin1: int or Pin, pin2: int or Pin, pin3: int or Pin,
                 pin4: int or Pin, half_steps: list[int] = HALF_STEPS,
                 number_of_steps: int=2048) -> None:

        Stepper.__init__(self, number_of_steps, pin1, pin2, pin3, pin4, half_steps=half_steps)