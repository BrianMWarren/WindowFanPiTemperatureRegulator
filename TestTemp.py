import RPi.GPIO as GPIO

import board
import busio
import adafruit_bme680# Create library object using our Bus I2C port
import time

PowerPin = 17
# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(PowerPin, GPIO.OUT) # pin set as output

# Initial state for power:
GPIO.output(PowerPin, GPIO.HIGH)

# i2c setup
i2c = busio.I2C(board.SCL, board.SDA)
outside = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x77)
inside = adafruit_bme680.Adafruit_BME680_I2C(i2c, address=0x76)

while True:
    OutsideFTemperature = (outside.temperature * (9/5)) + 32 # celcious to fahrenheit
    insideFTemperature = (inside.temperature * (9/5)) + 32 # celcious to fahrenheit
    print("Inside : Temperature: %0.1fF, Humidity: %0.1f %%, Pressure: %0.1f hPa, Gas: %0.1f ohms" % (insideFTemperature, inside.humidity, inside.pressure, inside.gas))
    print("Outside: Temperature: %0.1fF, Humidity: %0.1f %%, Pressure: %0.1f hPa, Gas: %0.1f ohms" % (OutsideFTemperature, outside.humidity, outside.pressure, outside.gas))

    
    time.sleep(5)