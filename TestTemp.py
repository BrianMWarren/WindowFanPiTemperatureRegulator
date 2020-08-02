import RPi.GPIO as GPIO

import board
import busio
import adafruit_bme280# Create library object using our Bus I2C port
import time

PowerPin = 17
# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(PowerPin, GPIO.OUT) # pin set as output

# Initial state for power:
GPIO.output(PowerPin, GPIO.HIGH)

# i2c setup
i2c = busio.I2C(board.SCL, board.SDA)
outside = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
inside = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)

while True:
    OutsideFTemperature = (outside.temperature * (9/5)) + 32 # celcious to fahrenheit
    insideFTemperature = (inside.temperature * (9/5)) + 32 # celcious to fahrenheit
    print("Inside : Temperature: %0.1fF, Humidity: %0.1f %%, Pressure: %0.1f hPa" % (insideFTemperature, inside.humidity, inside.pressure))
    print("Outside: Temperature: %0.1fF, Humidity: %0.1f %%, Pressure: %0.1f hPa" % (OutsideFTemperature, outside.humidity, outside.pressure))

    
    time.sleep(5)