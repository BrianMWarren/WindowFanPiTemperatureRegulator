#temp sensors
import board
import busio
import adafruit_bme280# Create library object using our Bus I2C port
import time
import requests
from influxdb import InfluxDBClient
import socket

#relay setup
import RPi.GPIO as GPIO

# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
relayPin = 24
powerPin = 17
GPIO.setup(relayPin, GPIO.OUT) # pin set as output
GPIO.setup(powerPin, GPIO.OUT) # pin set as output

# Initial state for outputs:
GPIO.output(relayPin, GPIO.LOW)
GPIO.output(powerPin, GPIO.HIGH)
time.sleep(5)

#const variables
futureInterpolationTime = 30 * 60
coldestInsideTemp = 66

class globals():
    inside = ""
    outside = ""
    previousTemps = {}

def PowerReset():
    print("Device error: ")
    GPIO.output(powerPin, GPIO.LOW)
    print("Power to i2c devices OFF")
    time.sleep(10)
    GPIO.output(powerPin, GPIO.HIGH)
    print("Power to i2c decives ON")
    time.sleep(10)
    TrySensorSetup()

def TrySensorSetup():
    try:
        GPIOSetup()
    except ValueError as e:
        PowerReset()

def GPIOSetup():
    i2c = busio.I2C(board.SCL, board.SDA)
    globals.outside = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x77)
    globals.inside = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)

def ResetVariables():
    globals.previousTemps = {}

def SendFanSignal(isOn):
    HOST = "192.168.1.5"
    PORT = 6998        # The port used by the server
    isOnB = bytes(isOn, encoding="utf-8")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(isOnB)
            s.close()
            return "sent" + isOn
    except (ConnectionRefusedError, OSError) as e:
        print("error in network: ", e)
        return "Network Error on remote pi"

def LerpTemp(outTemp):
    pastTime = list(globals.previousTemps.keys())[0]
    timeDiff = time.time() - pastTime
    pastTemp = globals.previousTemps[pastTime]
    tempDiff = outTemp - pastTemp
    multiFactor = futureInterpolationTime / timeDiff 
    perdictedTemp = (tempDiff * multiFactor) + outTemp
    return perdictedTemp



def TestTemperature():
    try:
        while True:
                OutsideFTemperature = (globals.outside.temperature * (9/5)) + 32 # celcious to fahrenheit
                insideFTemperature = (globals.inside.temperature * (9/5)) + 32 # celcious to fahrenheit 

                # prediction -----------------
                if(len(globals.previousTemps) > 0):
                    predictedOutsideTemp = LerpTemp(OutsideFTemperature)
                else:
                    predictedOutsideTemp = OutsideFTemperature

                globals.previousTemps[time.time()] = OutsideFTemperature
                if(len(globals.previousTemps) > 3):
                    del globals.previousTemps[list(globals.previousTemps.keys())[0]]
                # prediction -----------------

                if(insideFTemperature > predictedOutsideTemp and insideFTemperature > coldestInsideTemp):
                    GPIO.output(relayPin, GPIO.LOW)
                    print(SendFanSignal("ON"))
                    fanOn = True
                else:
                    GPIO.output(relayPin, GPIO.HIGH)
                    print(SendFanSignal("OFF"))
                    fanOn = False

                print("Inside : Temperature: %0.1fF, Humidity: %0.1f %%, Pressure: %0.1f hPa" % (insideFTemperature, globals.inside.humidity, globals.inside.pressure))
                print("Outside: Temperature: %0.1fF, Humidity: %0.1f %%, Pressure: %0.1f hPa" % (OutsideFTemperature, globals.outside.humidity, globals.outside.pressure))
                print("predicted outside temperature: %0.1f in: %d minutes" % (predictedOutsideTemp, futureInterpolationTime / 60))
                print("________________________________________")

                #send dweet.io and update on temperature status
                # dweetContent = {
                #     "Inside_Temp": round(insideFTemperature , 2),
                #     "Outside_Temp": round(OutsideFTemperature, 2),
                #     "Inside_Difference": round(insideFTemperature - OutsideFTemperature, 2),
                #     "Inside_Humidity": round(globals.inside.humidity, 1),
                #     "Outside_Humidity": round(globals.outside.humidity, 1),
                #     "Inside_Pressure": round(globals.inside.pressure, 1),
                #     "Outside_Pressure": round(globals.outside.pressure, 1),
                #     "Is_Fan_On": fanOn
                # }
                #send dweet.io and update on temperature status
                # URL = "https://dweet.io/dweet/for/409HouseWeather"
                # r = requests.post(url = URL, params = dweetContent)
                #load influx db

                influxDBContent = [
                    {"measurement" : "Inside_Temp",
                    "fields":{
                        "value": round(insideFTemperature , 2)}},
                    {"measurement" : "Outside_Temp",
                    "fields":{
                        "value": round(OutsideFTemperature , 2)}},
                    {"measurement" : "Inside_Difference",
                    "fields":{
                        "value": round(insideFTemperature - OutsideFTemperature, 2)}},
                    {"measurement" : "Inside_Humidity",
                    "fields":{
                        "value": round(globals.inside.humidity , 1)}},
                    {"measurement" : "Outside_Humidity",
                    "fields":{
                        "value": round(globals.outside.humidity , 1)}},
                    {"measurement" : "Inside_Pressure",
                    "fields":{
                        "value": round(globals.inside.pressure, 1)}},
                    {"measurement" : "Outside_Pressure",
                    "fields":{
                        "value": round(globals.outside.pressure, 1)}},
                    {"measurement" : "Is_Fan_On",
                    "fields":{
                        "value": fanOn}}
                ]
                client = InfluxDBClient('localhost', 8086, '', '', 'weather409')
                client.write_points(influxDBContent)

                #dweet pro authentication
                # dweet = {
                # "thing": "409HouseWeather2",
                # "key": "Bni05-8BtiA-8FV8z-1h0$9-9IGtI-8k1qo-A6XuO-EC2O2-1t@BZ-FfJbn-1MweA-6mssX-4ib4s-wab-1W",
                # "content": dweetContent
                # }
                # header = {"X-Dweet-Auth": "eyJyb2xlIjoiYXV0byIsImNvbXBhbnkiOiJTVVBFUlNQRUNJQUxOT05FTk9USElOR05PVEFOT1JHSU5JWkFUSU9OIiwiZ2VuZXJhdGVkIjoxNTk0NjgxNTI4MjQzfQ==.f52b975dd0a588a2b4ff59633d64ec5189f811e814bdc79d59fc66c53acc27e9"}
                # URL = "https://dweetpro.io:443/v2/dweets"
                # r = requests.post(url = URL, headers = header, json = dweet)




                time.sleep(300)

    except (OSError, ValueError) as e:
        print("error ", e)
        PowerReset()
        TestTemperature()
    
    except KeyboardInterrupt:
        GPIO.cleanup()
        SendFanSignal("OFF")


TrySensorSetup()
TestTemperature()
