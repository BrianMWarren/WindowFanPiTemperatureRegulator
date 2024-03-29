#temp sensors
import board
import busio
import time
import requests
from influxdb import InfluxDBClient
import socket
import subprocess
import json
from dataclasses import dataclass
from statistics import median

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

@dataclass
class Inside:
    IAQ_Accuracy: int
    Pressure: float
    Gas: int
    Temperature: float
    IAQ: float
    Humidity: float
    Status: float

@dataclass
class Outside:
    IAQ_Accuracy: int
    Pressure: float
    Gas: int
    Temperature: float
    IAQ: float
    Humidity: float
    Status: float

class globals():
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

def GetInsideValues(procInside):
    line = procInside.stdout.readline()
    lineJSON = json.loads(line.decode("utf-8")) # process line-by-line
    lineDict = dict(lineJSON)

    Inside.IAQ_Accuracy = (int(lineDict['IAQ_Accuracy']))
    Inside.Pressure = (float(lineDict['Pressure']))
    Inside.Gas = (int(lineDict['Gas']))
    Inside.Temperature = ((float(lineDict['Temperature']))) * (9/5) + 32
    Inside.IAQ = (float(lineDict['IAQ']))
    Inside.Humidity = (float(lineDict['Humidity']))
    Inside.Status = (int(lineDict['Status']))
    return Inside

def GetOutsideValues(procOutside):
    line = procOutside.stdout.readline()
    lineJSON = json.loads(line.decode("utf-8")) # process line-by-line
    lineDict = dict(lineJSON)

    Outside.IAQ_Accuracy = (int(lineDict['IAQ_Accuracy']))
    Outside.Pressure = (float(lineDict['Pressure']))
    Outside.Gas = (int(lineDict['Gas']))
    Outside.Temperature = ((float(lineDict['Temperature'])) * (9/5)) + 32
    Outside.IAQ = (float(lineDict['IAQ']))
    Outside.Humidity = (float(lineDict['Humidity']))
    Outside.Status = (int(lineDict['Status']))
    return Outside

def TestTemperature():
    calibrationAttempts = 0
    try:
        #Open C Files
        procOutside = subprocess.Popen(["/home/pi/WindowPiShare/bsec/bsec_bme680_python_77/bsec_bme680"], cwd="/home/pi/WindowPiShare/bsec/bsec_bme680_python_77/", stdout=subprocess.PIPE)
        procInside = subprocess.Popen(["/home/pi/WindowPiShare/bsec/bsec_bme680_python_76/bsec_bme680"], cwd="/home/pi/WindowPiShare/bsec/bsec_bme680_python_76/", stdout=subprocess.PIPE)
        
        while True:
            InsideReadings = []
            OutsideReadings = []    
            while(len(OutsideReadings) < 100):
                InsideReadings.append(GetInsideValues(procInside))
                OutsideReadings.append(GetOutsideValues(procOutside))
            
            #average all readings
            OutsideIAQ_Accuracy = 0
            OutsidePressure = 0
            OutsideGas = 0
            OutsideTemperature = 0
            OutsideIAQ = 0
            OutsideHumidity = 0
            OutsideStatus = 0
            
            InsideIAQ_Accuracy = 0
            InsidePressure = 0
            InsideGas = 0
            InsideTemperature = 0
            InsideIAQ = 0
            InsideHumidity = 0
            InsideStatus = 0
            for i in range(len(OutsideReadings)):
                OutsideIAQ_Accuracy += OutsideReadings[i].IAQ_Accuracy
                OutsidePressure += OutsideReadings[i].Pressure
                OutsideGas += OutsideReadings[i].Gas
                OutsideTemperature += OutsideReadings[i].Temperature
                OutsideIAQ += OutsideReadings[i].IAQ
                OutsideHumidity += OutsideReadings[i].Humidity
                OutsideStatus += OutsideReadings[i].Status

                InsideIAQ_Accuracy += InsideReadings[i].IAQ_Accuracy
                InsidePressure += InsideReadings[i].Pressure
                InsideGas += InsideReadings[i].Gas 
                InsideTemperature += InsideReadings[i].Temperature
                InsideIAQ += InsideReadings[i].IAQ
                InsideHumidity += InsideReadings[i].Humidity
                InsideStatus += InsideReadings[i].Status

            Outside.IAQ_Accuracy = OutsideIAQ_Accuracy / len(OutsideReadings)
            Outside.Pressure = OutsidePressure / len(OutsideReadings)
            Outside.Gas = OutsideGas / len(OutsideReadings)
            Outside.Temperature = OutsideTemperature / len(OutsideReadings)
            Outside.IAQ = OutsideIAQ / len(OutsideReadings)
            Outside.Humidity = OutsideHumidity / len(OutsideReadings)
            Outside.Status = OutsideStatus / len(OutsideReadings)

            Inside.IAQ_Accuracy = InsideIAQ_Accuracy / len(InsideReadings)
            Inside.Pressure = InsidePressure / len(InsideReadings)
            Inside.Gas = InsideGas / len(InsideReadings)
            Inside.Temperature = InsideTemperature / len(InsideReadings)
            Inside.IAQ = InsideIAQ / len(InsideReadings)
            Inside.Humidity = InsideHumidity / len(InsideReadings)
            Inside.Status = InsideStatus / len(InsideReadings)


            if(Inside.Temperature != "" and Outside.Temperature != ""):
                # prediction -----------------
                if(len(globals.previousTemps) > 0):
                    predictedOutsideTemp = LerpTemp(Outside.Temperature)
                else:
                    predictedOutsideTemp = Outside.Temperature

                globals.previousTemps[time.time()] = Outside.Temperature
                if(len(globals.previousTemps) > 2):
                    del globals.previousTemps[list(globals.previousTemps.keys())[0]]
                # prediction -----------------

                if(Inside.Temperature > predictedOutsideTemp and Outside.Temperature > coldestInsideTemp):
                    GPIO.output(relayPin, GPIO.LOW)
                    print(SendFanSignal("ON"))
                    fanOn = True
                else:
                    GPIO.output(relayPin, GPIO.HIGH)
                    print(SendFanSignal("OFF"))
                    fanOn = False

                print("Inside : Temperature: %0.1fF, Humidity: %0.1f %%, Pressure: %0.1f hPa, Gas: %0.1f ohms, IAQ accuracy: %i, IAQ: %i" % (Inside.Temperature, Inside.Humidity, Inside.Pressure, Inside.Gas, Inside.IAQ_Accuracy, Inside.IAQ))
                print("Outside: Temperature: %0.1fF, Humidity: %0.1f %%, Pressure: %0.1f hPa, Gas: %0.1f ohms, IAQ accuracy: %i, IAQ: %i" % (Outside.Temperature, Outside.Humidity, Outside.Pressure, Outside.Gas, Outside.IAQ_Accuracy, Outside.IAQ))
                print("predicted outside temperature: %0.1f in: %d minutes" % (predictedOutsideTemp, futureInterpolationTime / 60))
                print("________________________________________")

                #send dweet.io and update on temperature status
                # dweetContent = {
                #     "Inside_Temp": round(Inside.Temperature. , 2),
                #     "Outside_Temp": round(Outside.Temperature, 2),
                #     "Inside_Difference": round(Inside.Temperature - Outside.Temperature, 2),
                #     "Inside_Humidity": round(Inside.Humidity, 1),
                #     "Outside_Humidity": round(Outside.Humidity, 1),
                #     "Inside_Pressure": round(Inside.Pressure, 1),
                #     "Outside_Pressure": round(Outside.Pressure, 1),
                #     "Inside_IAQ_Accuracy": Inside.IAQ_Accuracy,
                #     "Outside_IAQ_Accuracy": Outside.IAQ_Accuracy,
                #     "Inside_IAQ": Inside.IAQ,
                #     "Outside_IAQ": Outside.IAQ,
                #     "Is_Fan_On": fanOn
                # }
                #send dweet.io and update on temperature status
                # URL = "https://dweet.io/dweet/for/409HouseWeather"
                # r = requests.post(url = URL, params = dweetContent)

                #load influx db
                influxDBContent = [
                    {"measurement" : "Inside_Temp",
                    "fields":{
                        "value": round(Inside.Temperature , 2)}},
                    {"measurement" : "Outside_Temp",
                    "fields":{
                        "value": round(Outside.Temperature , 2)}},
                    {"measurement" : "Inside_Difference",
                    "fields":{
                        "value": round(Inside.Temperature - Outside.Temperature, 2)}},
                    {"measurement" : "Inside_Humidity",
                    "fields":{
                        "value": round(Inside.Humidity , 1)}},
                    {"measurement" : "Outside_Humidity",
                    "fields":{
                        "value": round(Outside.Humidity , 1)}},
                    {"measurement" : "Inside_Pressure",
                    "fields":{
                        "value": round(Inside.Pressure, 1)}},
                    {"measurement" : "Outside_Pressure",
                    "fields":{
                        "value": round(Outside.Pressure, 1)}},
                    {"measurement" : "Inside_IAQ_Accuracy",
                    "fields":{
                        "value": round(Inside.IAQ_Accuracy, 1)}},
                    {"measurement" : "Outside_IAQ_Accuracy",
                    "fields":{
                        "value": round(Outside.IAQ_Accuracy, 1)}},
                    {"measurement" : "Inside_IAQ",
                    "fields":{
                        "value": Inside.IAQ}},
                    {"measurement" : "Outside_IAQ",
                    "fields":{
                        "value": Outside.IAQ}},
                    {"measurement" : "Is_Fan_On",
                    "fields":{
                        "value": fanOn}}
                ]
                client = InfluxDBClient('localhost', 8086, '', '', 'weather409')
                client.write_points(influxDBContent)

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
