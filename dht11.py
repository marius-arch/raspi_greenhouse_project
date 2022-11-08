# import all the used libraries
import RPi.GPIO as GPIO
import dht11
import board
import time
 
from adafruit_ht16k33.segments import Seg7x4
import adafruit_character_lcd.character_lcd_i2c as character_lcd
from statistics import median

# show that script has started
print("Script has started. Version: v.1.0.0")
 
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
# clear the 7 segment display
segment.fill(0)
 
## initialize lcd display
lcd = character_lcd.Character_LCD_I2C(i2c, 16, 2, 0x21)
# clear the lcd display
lcd.clear()

# pass-trough number for console debugging
passTrough = 1
 
# while 1 continiously runs the code inside of it, to make sure the measured values are up-to-date
while 1:
    # create array for temp and humidity values
    temperatures = []
    humidities = []
    # read temperature and humidity ten times and save it in array
    for i in range(10):
        # reads the current temperature and humidity of the dht11 sensor
        result = instance.read()
        while not result.is_valid():  # read until valid values
            result = instance.read()
        # add the values to the arrays
        temperatures.append(result.temperature)
        humidities.append(result.humidity)
 
    # create the median of the values to avoid deviations and make the values global
    global temperature
    temperature = median(sorted(temperatures))
    global humidity
    humidity = median(sorted(humidities))
    
    print("Current run: {}".format(passTrough))
 
    # prints the current measured temperature and humidity with one decimal place for testing purposes
    print("Temperature: {:.1f}°C".format(temperature))
    print("Humidity: {:.0f}% \n".format(int(humidity)))
 
    # configure what each segment of the display should show
    segment[0] = str(int(temperature / 10))
    segment[1] = str(int(temperature % 10))
    segment[2] = str(int(humidity / 10))
    segment[3] = str(int(humidity % 10))
 
    # turn on backlight of lcd display
    lcd.backlight = True
    # display the temperature and humidity on the lcd display with one decimal place
    lcd.message = "Temp= {:.1f}".format(temperature) + chr(223) + "C\n" + "Humidity= {:.0f}%".format(humidity)
    
    # increase pass-trough number
    passTrough+=1
 
    # wait 200ms until continuing
    #time.sleep(0.2)
