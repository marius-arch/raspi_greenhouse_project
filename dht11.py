import RPi.GPIO as GPIO
import dht11
import board
import time
 
from adafruit_ht16k33.segments import Seg7x4
 
## initialize GPIO
# disable warnings for ports that are already in use
GPIO.setwarnings(False)
# refer to the pins by the Broadcom SOC channel
GPIO.setmode(GPIO.BCM)
# cleanup all the used ports
GPIO.cleanup()

# configure on which gpio pin the dht11 sensor is located
instance = dht11.DHT11(pin = 4)

## initialize 7-segmengt display
# create the i2c interface
i2c = board.I2C()
# create a 4 character 7 segment display
segment = Seg7x4(i2c, address=0x70)
# clear the display
segment.fill(0)

# while 1 continiously runs the code inside of it, to make sure the measured values are up-to-date
while 1:
    # reads the current temperature and humidity from the dht11 sensor
    for i in range(10):
    
    result = instance.read()
   
    while not result.is_valid():  # read until valid values
        result = instance.read()
    
    # prints the current measured temperature and humidity for testing purposes
    print("Temperature: %-3.1f C" % result.temperature)
    print("Humidity: %-3.1f %%" % result.humidity)
 
    # configure what each segment of the display should show
    segment[0] = str(int(result.temperature / 10))
    segment[1] = str(int(result.temperature % 10))
    segment[2] = str(int(result.humidity / 10))
    segment[3] = str(int(result.humidity % 10))
    
    time.sleep(0.2)
