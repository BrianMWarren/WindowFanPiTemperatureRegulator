import subprocess
import json
from dataclasses import dataclass

#Open C File
proc = subprocess.Popen(['/home/pi/WindowPiShare/bsec/bsec_bme680_python/bsec_bme680_76'], stdout=subprocess.PIPE)

@dataclass
class Inside:
    IAQ_Accuracy: int
    Pressure: float
    Gas: int
    Temperature: float
    IAQ: float
    Humidity: float
    Status: int

for line in iter(proc.stdout.readline, ''):
    lineJSON = json.loads(line.decode("utf-8")) # process line-by-line
    lineDict = dict(lineJSON)

    Inside.IAQ_Accuracy = (int(lineDict['IAQ_Accuracy']))
    Inside.Pressure = (float(lineDict['Pressure']))
    Inside.Gas = (int(lineDict['Gas']))
    Inside.Temperature = (float(lineDict['Temperature']))
    Inside.IAQ = (float(lineDict['IAQ']))
    Inside.Humidity = (float(lineDict['Humidity']))
    Inside.Status = (int(lineDict['Status']))

    print(Inside.Temperature)