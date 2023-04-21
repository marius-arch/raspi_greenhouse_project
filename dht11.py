## import all the used libraries
import RPi.GPIO as GPIO
import dht11
import board
import smbus
import time
import ntplib
import requests
import json
import os
import pytz
import urllib3
import time
import mariadb
import sys
 
from adafruit_ht16k33.segments import Seg7x4
import adafruit_character_lcd.character_lcd_i2c as character_lcd
from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.led_matrix.device import max7219
from datetime import datetime, timezone, timedelta
from statistics import median
 
# show that script has started with the current version
print("Script has started. Version: v.1.0.6")
 
## initialize GPIO
# disable warnings for ports that are already in use
GPIO.setwarnings(False)
# refer to the pins by the Broadcom SOC channel
GPIO.setmode(GPIO.BCM)
# cleanup all the used ports
GPIO.cleanup()
 
## Database
# create database connection
config = {
  'user': 'marius',
  'password': 'adminadmin',
  'host': '127.0.0.1',
  'port': 3306,
  'database': 'raspiGreenhouseProject'
}
 
# connect to database and initialize cursor
try:
    conn =  mariadb.connect(**config)
    print('Successfully connected to database.')
except mariadb.Error as e: 
    print(f'Error connecting to MariaDB Platform: {e}')
    sys.exit(1)
cursor = conn.cursor()
 
# create tables of database with database name
DB_NAME = 'raspiGreenhouseProject'
 
TABLES = {}
TABLES['measurements'] = (
    "CREATE TABLE IF NOT EXISTS `measurements` ("
    "  `ID` int(5) NOT NULL AUTO_INCREMENT,"
    "  `Time` datetime NOT NULL,"
    "  `Temperature` float(5) NOT NULL,"
    "  `Humidity` float(5) NOT NULL,"
    "  `Light` int(3) NOT NULL,"
    "  `LightRating` varchar(10) NOT NULL,"
    "  `RelayState` varchar(10) NOT NULL,"
    "  PRIMARY KEY (`ID`)"
    ") ENGINE=InnoDB")
 
# create database
def create_database(cursor):
    try:
        cursor.execute(
            "CREATE DATABASE IF NOT EXISTS {} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))
    except mariadb.Error as e:
        print("Failed creating database: {}".format(e))
        exit(1)
 
 
try:
    # tell database connection which database should be used
    cursor.execute("USE {}".format(DB_NAME))
# catch error
except mariadb.Error as err:
    print("Database {} does not exists.".format(DB_NAME))
    if err == err.ER_BAD_DB_ERROR:
        create_database(cursor)
        print("Database {} created successfully.".format(DB_NAME))
        conn.database = DB_NAME
    else:
        print(err)
        exit(1)
 
#create tables
for table_name in TABLES:
    table_description = TABLES[table_name]
    try:
        print("Creating table {}: ".format(table_name), end='')
        cursor.execute(table_description)
    except mariadb.Error as err:
            print(err.msg)
    else:
        print("OK")
 
 
# define relay pin
relay_pin = 21
#set output for gpio
GPIO.setup(relay_pin, GPIO.OUT)
 
# configure on which gpio pin the dht11 sensor is located
dht11_sensor = dht11.DHT11(pin = 4)
 
## initialize 7-segment display
# create the i2c interface
i2c = board.I2C()
# create a 4 character 7 segment display
segment = Seg7x4(i2c, address=0x70)
# clear the 7 segment display
segment.fill(0)
 
## initialize matrix display
serial = spi(port=0, device=1, gpio=noop())
device = max7219(serial)
 
## initialize lcd display
lcd = character_lcd.Character_LCD_I2C(i2c, 16, 2, 0x21)
# clear the lcd display
lcd.clear()
 
## define ntp client for time pull
c = ntplib.NTPClient()
 
## disable certificate warning
urllib3.disable_warnings()
 
## timezone initialization
utc=pytz.UTC
 
## define which smbus to use
bus = smbus.SMBus(1)
 
## define symbols for light levels
happy_smiley = [[0, 0, 1, 1, 1, 1, 0, 0],
                [0, 1, 0, 0, 0, 0, 1, 0],
                [1, 0, 1, 0, 0, 1, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 1],
                [1, 0, 1, 0, 0, 1, 0, 1],
                [1, 0, 0, 1, 1, 0, 0, 1],
                [0, 1, 0, 0, 0, 0, 1, 0],
                [0, 0, 1, 1, 1, 1, 0, 0]]
 
neutral_smiley = [[0, 0, 1, 1, 1, 1, 0, 0],
                  [0, 1, 0, 0, 0, 0, 1, 0],
                  [1, 0, 1, 0, 0, 1, 0, 1],
                  [1, 0, 0, 0, 0, 0, 0, 1],
                  [1, 0, 1, 1, 1, 1, 0, 1],
                  [1, 0, 0, 0, 0, 0, 0, 1],
                  [0, 1, 0, 0, 0, 0, 1, 0],
                  [0, 0, 1, 1, 1, 1, 0, 0]]
 
sad_smiley = [[0, 0, 1, 1, 1, 1, 0, 0],
              [0, 1, 0, 0, 0, 0, 1, 0],
              [1, 0, 1, 0, 0, 1, 0, 1],
              [1, 0, 0, 0, 0, 0, 0, 1],
              [1, 0, 0, 1, 1, 0, 0, 1],
              [1, 0, 1, 0, 0, 1, 0, 1],
              [0, 1, 0, 0, 0, 0, 1, 0],
              [0, 0, 1, 1, 1, 1, 0, 0]]                  
 
class LightSensor():
 
    def __init__(self):
 
        # define constants from datasheet
        self.DEVICE = 0x5c # standard I2C device-id
        self.POWER_DOWN = 0x00 # no active state
        self.POWER_ON = 0x01 # ready for operation
        self.RESET = 0x07 # reset data register
 
        # start measurements at 4 lux
        self.CONTINUOUS_LOW_RES_MODE = 0x13
        # start measurements at 1 lux
        self.CONTINUOUS_HIGH_RES_MODE_1 = 0x10
        # start measurements at 0.5 lux
        self.CONTINUOUS_HIGH_RES_MODE_2 = 0x11
        # start measurements at 1 lux
        # device will be in an inactive state after measurement
        self.ONE_TIME_HIGH_RES_MODE_1 = 0x20
        # start measurements at 0.5 lux
        # device will be in an inactive state after measurement
        self.ONE_TIME_HIGH_RES_MODE_2 = 0x21
        # start measurements at 4 lux
        # device will be in an inactive state after measurement
        self.ONE_TIME_LOW_RES_MODE = 0x23
 
 
    def convertToNumber(self, data):
        # convert 2-byte-data to decimal number
        return ((data[1] + (256 * data[0])) / 1.2)
 
    def readLight(self):
        # read current light level and convert to decimal number
        data = bus.read_i2c_block_data(self.DEVICE,self.ONE_TIME_HIGH_RES_MODE_1)
        return self.convertToNumber(data)
 
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
 
## function for converting array to draw array to matrix
def drawMatrixSymbol(symbol):
    tuples = []
    for row in range(len(symbol)):
        for col in range(len(symbol[row])):
            if(symbol[row][col] == 1):
                tuples.append((row,col))
    with canvas(device) as draw:
        draw.point(tuple(tuples), fill="white")
 
## function for converting utc datetime to local datetime
def datetimeToLocal(utcDateTime):
    nowTimestamp = time.time()
    offset = datetime.fromtimestamp(nowTimestamp) - datetime.utcfromtimestamp(nowTimestamp)
    return utcDateTime + offset
 
# define main function
def main():
    # pass-trough number for console debugging
    passTrough = 1
 
    sensor = LightSensor()
 
    # check if log file exists
    if(os.path.exists("measurements.csv") == False):
        open("measurements.csv", "a").write("Time;Temperature;Humidity;Light;LightRating;RelayState\n")
 
 
    # while True continuously runs the code inside of it, to make sure the measured values are up-to-date
    while True:
        print("Current run: {}".format(passTrough))
        print("Starting measurements...")
 
        # start measurements
        dht11Measurement()
 
        # prints the current measured temperature, light level with two decimal places
        # and humidity with one decimal place for testing purposes
        print("Temperature: {:.1f}°C".format(temperature))
        print("Humidity: {:.0f}%".format(int(humidity)))
 
        #read current light level with sensor and output it in the console
        lightLevel = sensor.readLight()
        print ("Light Level: {:.2f}".format(lightLevel))
 
        # create empty line
        print()
 
        #draw symbols for light level
        if(50000.0 < lightLevel < 65000.0):
            drawMatrixSymbol(happy_smiley)
            lightRating = "good"
        if(45000.0 < lightLevel < 50000.0 or 65000.0 < lightLevel < 70000.0):
            drawMatrixSymbol(neutral_smiley)
            lightRating = "ok"
        if(lightLevel < 45000.0 or lightLevel > 70000.0):
            drawMatrixSymbol(sad_smiley)
            lightRating = "bad"
 
        # configure what each segment of the display should show
        segment[0] = str(int(temperature / 10))
        segment[1] = str(int(temperature % 10))
        segment[2] = str(int(humidity / 10))
        segment[3] = str(int(humidity % 10))
 
        # turn on backlight of lcd display
        lcd.backlight = True
        # display the temperature and humidity on the lcd display with one decimal place
        scroll_message = "Temp= {:.1f}".format(temperature) + chr(223) + "C\n" + "Humidity= {:.0f}%".format(humidity) + " Light= {:.2f}lx".format(lightLevel)
        lcd.message = scroll_message
        for i in range(len(scroll_message)-29):
            time.sleep(0.5)
            lcd.move_left()
        time.sleep(0.5)
        for i in range(len(scroll_message)-29):
            time.sleep(0.5)
            lcd.move_right()
 
        ## check for current time with server
        response = c.request('10.254.5.115', version=3)
        response.offset
        currentTime = datetime.fromtimestamp(response.tx_time, timezone.utc)
 
        ## check for sunrise-/sunsettime
        # lat and long of bszetdd
        lat = 51.033749
        long = 13.748540
 
        # json response of sunrise web api
        response = requests.get(f'https://api.sunrise-sunset.org/json?lat={lat}&lng={long}&formatted=0', verify=False)
        data = json.loads(response.content)
        sunrise = data['results']['sunrise'] # data for sunrise
        sunset = data['results']['sunset'] # data for sunset
        sunrise_time = datetime(year=currentTime.year,month=currentTime.month, day=currentTime.day, hour=int(sunrise[11:13]), minute=int(sunrise[14:16]), tzinfo=(utc)) # transform sunrise into time format
        sunset_time = datetime(year=currentTime.year,month=currentTime.month, day=currentTime.day, hour=int(sunset[11:13]), minute=int(sunset[14:16]), tzinfo=(utc)) # transform sunset into time format
        # calculate the difference between sunset and sunrise and the time that is left when subtracting the difference from 12 hours
        sunset_difference = (sunset_time.hour * 60 + sunset_time.minute) - (sunrise_time.hour * 60 + sunrise_time.minute)
        leftTime = 12*60 - sunset_difference
 
         # Board mode GPIO.BOARD
        #GPIO.setmode(GPIO.BOARD)
        # relay_pin as exit
        #GPIO.setup(relay_pin, GPIO.OUT)
 
        # check if the sun is still shining and the above checked lightRating
        if(currentTime < sunset_time and currentTime > sunrise_time):
            if(lightLevel == "bad"):
                # close relay
                GPIO.output(relay_pin, GPIO.HIGH)
                relayState = "closed"
            else:
                # open relay
                GPIO.output(relay_pin, GPIO.LOW)
                relayState = "opened"
 
        # check if there is still light needed to fullfil the 12 hours of light
        if(leftTime <= 0):
            # open relay -> open means light is off
            GPIO.output(relay_pin, GPIO.LOW)
            relayState = "opened"
        else: 
            shutDownTime = sunset_time + timedelta(minutes=leftTime)
            if(currentTime >= shutDownTime):
                # open relay
                GPIO.output(relay_pin, GPIO.LOW)
                relayState = "opened"
            elif(currentTime > sunset_time and currentTime < sunrise_time):
                # close relay
                GPIO.output(relay_pin, GPIO.HIGH)
                relayState = "closed"
 
        # convert utc to local time
        localTime = datetimeToLocal(currentTime).strftime("%d/%m/%Y, %H:%M:%S")
 
        # write all measurements to log file (csv)
        open("measurements.csv", "a").write(f"{localTime};{temperature};{humidity};{lightLevel};{lightRating};{relayState}\n")
 
        ## write data to database
        sqlStatement = f"INSERT INTO measurements (Time, Temperature, Humidity, Light, LightRating, RelayState) VALUES('{datetime.now()}', '{temperature}', '{humidity}', '{lightLevel}', '{lightRating}', '{relayState}')"
        cursor = conn.cursor() # get a cursor from the database
        # execute the SQL Statement
        cursor.execute(sqlStatement)
        # the commit is used for saving the data in the database
        conn.commit()
 
        # increase pass-trough number
        passTrough+=1
 
        # wait 200ms until continuing
        time.sleep(0.2)
 
# run main function
if __name__ == "__main__":
    main()
    #close database connection
    cursor.close()
    conn.close()