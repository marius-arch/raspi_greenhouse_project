import RPi.GPIO as GPIO
import dht11
import board

from adafruit_ht16k33.segments import Seg7x4

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.cleanup()

i2c = board.I2C()
segment = Seg7x4(i2c, address=0x70)

segment.fill(0)

instance = dht11.DHT11(pin = 4)
result = instance.read()

while not result.is_valid():
   result = instance.read()
    
segment[0] = str(int(result.temperature) / 10)
segment[1] = str(int(result.temperature) % 10)
segment[2] = str(int(result.temperature) % 1)
segment[3] = str(int(result.temperature) % 1) / 1
    
