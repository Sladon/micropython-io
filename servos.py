from machine import Pin, PWM
from math import radians, degrees

class Servo:
    """
    A class representing a servo motor controlled by PWM signals.

    Reference:
    - Original code written by redoxcode available at https://github.com/redoxcode/micropython-servo.

    Attributes:
    - pin (int): The pin number to which the servo signal wire is connected.
    - min_us (float): The minimum pulse duration in microseconds corresponding to the minimum angle.
    - max_us (float): The maximum pulse duration in microseconds corresponding to the maximum angle.
    - min_deg (float): The minimum angle in degrees.
    - max_deg (float): The maximum angle in degrees.
    - freq (int): The PWM frequency in hertz.

    Methods:
    - __init__(self, pin: int, min_us: float, max_us: float, min_deg: float, max_deg: float, freq: int) -> None:
        Initializes the Servo instance with specified parameters and sets the PWM pin.

    - write(self, value: float, method: str = 'deg') -> None:
        Writes the specified value to the servo, where value is either in degrees ('deg'), radians ('rad'),
        or microseconds ('us'). Raises a ValueError if the value is not a float or int.

    - read(self, method: str = 'deg') -> int:
        Reads the current position of the servo in degrees ('deg'), radians ('rad'), or microseconds ('us').

    - off(self) -> None:
        Turns off the servo by setting the PWM duty cycle to 0.

    Private Methods:
    - __write_us(self, us: float) -> None:
        Writes the pulse duration in microseconds to the servo, ensuring it stays within the valid range.

    - __write_rad(self, rad: float) -> None:
        Converts the angle in radians to microseconds and writes it to the servo.

    - __write_deg(self, deg: float) -> None:
        Converts the angle in degrees to radians and writes it to the servo.

    - __read_us(self) -> int:
        Returns the current pulse duration in microseconds.

    - __read_rad(self) -> int:
        Converts the current pulse duration to radians and returns the angle.

    - __read_deg(self) -> int:
        Converts the current pulse duration to degrees and returns the angle.
    """

    def __init__(self, pin: int, min_us: float, max_us: float, min_deg: float, max_deg: float, freq:int) -> None:
        self.__pwm = PWM(Pin(15, Pin.OUT), freq=freq)
        self.__current_us: float = 0
        self.off()
        self.__min_us = min_us
        self.__max_us = max_us
        self.__slope = (min_us-max_us)/(radians(min_deg)-radians(max_deg))
        self.__offset = min_us

    def write(self, value: float, method: str= 'deg') -> None:
        """
        Writes the specified value to the servo.

        Args:
        - value (float): The value to be written to the servo.
        - method (str): The unit of the value ('deg', 'rad', or 'us'). Default is 'deg'.
        """

        if not isinstance(value, (int, float)): 
            raise ValueError(f"Value must be float or int, received {type(value)}")

        if method == 'deg':
            self.__write_deg(value)
        elif method == 'rad':
            self.__write_rad(value)
        elif method == 'us':
            self.__write_us(value)

    def __write_us(self, us: float) -> None:
        if us < self.__min_us:
            us = self.__min_us
        elif us > self.__max_us:
            us = self.__max_us

        self.__current_us = us
        self.__pwm.duty_ns(int(self.__current_us*1000))

    def __write_rad(self, rad: float) -> None:
        self.__write_us(rad*self.__slope+self.__offset)

    def __write_deg(self, deg: float) -> None:
        self.__write_rad(radians(deg))

    def read(self, method: str= 'deg') -> int or float:
        """
        Reads the current position of the servo.

        Args:
        - method (str): The unit in which to return the position ('deg', 'rad', or 'us'). Default is 'deg'.

        Returns:
        - int or float: The current position of the servo in the specified unit.
        """
        if method == 'deg':
            return self.__read_deg()
        elif method == 'rad':
            return self.__read_rad()
        elif method == 'us':
            return self.__read_us()

    def __read_deg(self) -> float:
        return degrees(self.__read_rad())

    def __read_rad(self) -> float:
        return (self.__current_us-self.__offset)/self.__slope

    def __read_us(self) -> int:
        return self.__current_us

    def off(self) -> None:
        """Turns off the servo by setting the PWM duty cycle to 0."""
        self.__pwm.duty_ns(0)


class SG90(Servo):
    """
    Sg90 class represents an interface for controlling an SG90 servo motor using PWM.

    The SG90 servo typically has three wires:
    - Brown or Black: Ground
    - Red: Power
    - Orange or Yellow: Signal

    Connect the servo wires as follows:
    - Brown or Black wire: Connect to the ground of your power source.
    - Red wire: Connect to the positive voltage supply.
    - Orange or Yellow wire: Connect to the GPIO pin specified during object creation.

    Inherits from:
    - Servo: The base class providing generic servo control functionality.

    Initialization Parameters:
    - pin (int): The pin number to which the SG90 servo signal wire is connected.
    - min_us (float): The minimum pulse duration in microseconds corresponding to the minimum angle. Default is 500.
    - max_us (float): The maximum pulse duration in microseconds corresponding to the maximum angle. Default is 2500.
    - min_deg (float): The minimum angle in degrees. Default is 0.
    - max_deg (float): The maximum angle in degrees. Default is 180.
    - freq (int): The PWM frequency in hertz. Default is 50.
    """

    def __init__(self, pin: int, min_us: float=500, max_us: float=2500, min_deg: float=0, max_deg: float=180, freq: int=50):
        Servo.__init__(self, pin, min_us, max_us, min_deg, max_deg, freq)