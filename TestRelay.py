import RPi.GPIO as GPIO
import time

relayPin = 24
# Pin Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(relayPin, GPIO.OUT) # pin set as output

# Initial state for LEDs:
GPIO.output(relayPin, GPIO.LOW)

try:
    while True:
        GPIO.output(relayPin, GPIO.LOW)
        print("relay on")
        time.sleep(.5)
        GPIO.output(relayPin, GPIO.HIGH)
        print("relay off")
        time.sleep(.5)

except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup() # cleanup all GPIO