from .racecar import Racecar
import traitlets
from adafruit_servokit import ServoKit


class CServo():
  @property                                                                                                                                                                                                                                                                 
  def throttle(self):                                                                                                                                                                                                                                                       
    """How much power is being delivered to the motor. Values range from ``-1.0`` (full                                                                                                                                                                                   
       throttle reverse) to ``1.0`` (full throttle forwards.) ``0`` will stop the motor from                                                                                                                                                                              
       spinning."""                                                                                                                                                                                                                                                       
    return self.fraction * 2 - 1                                                                                                                                                                                                                                          

  @throttle.setter
  def throttle(self, value):
    if value > 1.0 or value < -1.0:
      raise ValueError("Throttle must be between -1.0 and 1.0")
    if value is None:
      raise ValueError("Continuous servos cannot spin freely")
    self.fraction = (value + 1) / 2
    print ("CServo.fraction {}".format(self.fraction))

  def __enter__(self):
    return self

  def __exit__(self, exception_type, exception_value, traceback):
    self.throttle = 0

  def deinit(self):
    """Stop using the servo."""
    self.throttle = 0 

class MServo ():
  def __init__(self, kit):
    self.kit = kit

  def __getitem__(self, servo_channel):
    servo = self.kit._items[servo_channel]
    if servo is None:
      servo = CServo ()
      self.kit._items[servo_channel] = servo
      return servo
    if isinstance (self.kit._items[servo_channel], CServo):
      return servo
    raise ValueError("Channel {} is already in use.".format(servo_channel))

  def __len__(self):
    return len (self.kit._items)

class MKit ():
	def __init__(self, *, channels, address):
	    self.mchan = channels
	    self.maddr = address
	    self._items = [None] * channels
	    print ("MKit has {}chns at addr:{}".format (self.mchan, hex (self.maddr)))
	    self._continuous_servo = MServo(self)

	@property
	def continuous_servo(self):
	    return self._continuous_servo

class NvidiaRacecar(Racecar):
    
    #i2c_address = traitlets.Integer(default_value=0x40)
    steering_gain = traitlets.Float(default_value=-0.65)
    steering_offset = traitlets.Float(default_value=0)
    steering_channel = traitlets.Integer(default_value=0)
    throttle_gain = traitlets.Float(default_value=0.8)
    throttle_channel = traitlets.Integer(default_value=1)
    
    def __init__(self, *args, **kwargs):
        super(NvidiaRacecar, self).__init__(*args, **kwargs)
        self.kit = MKit(channels=16, address=0x40)
        self.steering_motor = self.kit.continuous_servo[self.steering_channel]
        self.throttle_motor = self.kit.continuous_servo[self.throttle_channel]
    
    @traitlets.observe('steering')
    def _on_steering(self, change):
        self.steering_motor.throttle = change['new'] * self.steering_gain + self.steering_offset
    
    @traitlets.observe('throttle')
    def _on_throttle(self, change):
        self.throttle_motor.throttle = change['new'] * self.throttle_gain