import RPi.GPIO as GPIO
import time

# Updated GPIO pin assignments
SWITCH_PIN_1 = 27  # Connected to switch pins 2 and 3
SWITCH_PIN_2 = 22  # Connected to switch pin 7

GPIO.setmode(GPIO.BCM)
GPIO.setup(SWITCH_PIN_1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SWITCH_PIN_2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def get_position(pin1, pin2):
    a = GPIO.input(pin1)
    b = GPIO.input(pin2)

    if not a and not b:
        return "Position A"
    elif not a and b:
        return "Position B"
    elif a and not b:
        return "Position C"
    elif a and b:
        return "Position D"
    return "Unknown"

try:
    while True:
        pos = get_position(SWITCH_PIN_1, SWITCH_PIN_2)
        print(f"Switch: {pos}")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()
