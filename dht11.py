# import all the used libraries
import RPi.GPIO as GPIO
import dht11
import board
# import smbus
import time
 
from adafruit_ht16k33.segments import Seg7x4
import adafruit_character_lcd.character_lcd_i2c as character_lcd
import adafruit_bh1750
from statistics import median

# show that script has started
print("Script has started. Version: v.1.0.2")

## initialize GPIO
# disable warnings for ports that are already in use
GPIO.setwarnings(False)
# refer to the pins by the Broadcom SOC channel
GPIO.setmode(GPIO.BCM)
# cleanup all the used ports
GPIO.cleanup()

# configure on which gpio pin the dht11 sensor is located
dht11_sensor = dht11.DHT11(pin = 4)
 
## initialize 7-segment display
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

## initialize light sensor
lightsensor = adafruit_bh1750.BH1750(i2c)

# ## define which smbus to use
# bus = smbus.SMBus(1)
# class LightSensor():

#     def __init__(self):

#         # define constants from datasheet
#         self.DEVICE = 0x5c # standard I2C device-id
#         self.POWER_DOWN = 0x00 # no active state
#         self.POWER_ON = 0x01 # ready for operation
#         self.RESET = 0x07 # reset data register

#         # start measurements at 4 lux
#         self.CONTINUOUS_LOW_RES_MODE = 0x13
#         # start measurements at 1 lux
#         self.CONTINUOUS_HIGH_RES_MODE_1 = 0x10
#         # start measurements at 0.5 lux
#         self.CONTINUOUS_HIGH_RES_MODE_2 = 0x11


#     def convertToNumber(self, data):
#         # convert 2-byte-data to decimal number
#         return ((data[1] + (256 * data[0])) / 1.2)

#     def readLight(self):
#         data = bus.read_i2c_block_data(self.DEVICE,self.ONE_TIME_HIGH_RES_MODE_1)
#         return self.convertToNumber(data)

def dht11Measurement():
    # create array for temp and humidity values
    temperatures = []
    humidities = []
    # read temperature and humidity ten times and save it in array
    for i in range(10):
        # reads the current temperature and humidity of the dht11 sensor
        result = dht11_sensor.read()
        while not result.is_valid():  # read until valid values
            result = dht11_sensor.read()
        # add the values to the arrays
        temperatures.append(result.temperature)
        humidities.append(result.humidity)

    # create the median of the values to avoid deviations and make the values global
    global temperature
    temperature = median(sorted(temperatures))
    global humidity
    humidity = median(sorted(humidities))

# define main function
def main():
    # pass-trough number for console debugging
    passTrough = 1
    
    #sensor = LightSensor()

    # while True continiously runs the code inside of it, to make sure the measured values are up-to-date
    while True:
        print("Current run: {}".format(passTrough))
        print("Starting measurements...")

        #start measurements
        dht11()
    
        # prints the current measured temperature and humidity with one decimal place for testing purposes
        print("Temperature: {:.1f}°C".format(temperature))
        print("Humidity: {:.0f}%".format(int(humidity)))
        print("Light Level: {:.2f} lx".format(lightsensor.lux))
        #print ("Light Level : " + str(sensor.readLight()) + " lx")
        #create empty line
        print()
    
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
        time.sleep(0.2)

        # website for matrix:
        # https://xantorohara.github.io/led-matrix-editor/

# run main function
if __name__ == "__main__":
    main()
