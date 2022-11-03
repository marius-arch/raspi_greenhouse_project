import RPi.GPIO as GPIO
import dht11
import board
import time
 
from adafruit_ht16k33.segments import Seg7x4
 
# initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()
 
# read data using pin 14
instance = dht11.DHT11(pin = 4)
 
i2c = board.I2C()
segment = Seg7x4(i2c, address=0x70)
 
segment.fill(0)
 
while 1:
    result = instance.read()
    while not result.is_valid():  # read until valid values
        result = instance.read()
    print("Temperature: %-3.1f C" % result.temperature)
    print("Humidity: %-3.1f %%" % result.humidity)
 
    segment[0] = str(int(result.temperature / 10))
    segment[1] = str(int(result.temperature % 10))
    segment[2] = str(int(result.humidity / 10))
    segment[3] = str(int(result.humidity % 10))
    time.sleep(0.2)
