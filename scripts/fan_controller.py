"""
fan_controller.py
This script controls a fan based on the Raspberry Pi's CPU temperature.
"""

# pylint:disable=consider-using-from-import, import-error, unspecified-encoding, logging-fstring-interpolation

import logging
import time

import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)
logger.info("Alerts script started")

FAN_PIN = 4  # GPIO 4
ON_TEMP = 80
OFF_TEMP = 75

GPIO.setmode(GPIO.BCM)
GPIO.setup(FAN_PIN, GPIO.OUT)
FAN_ON = False


def get_temp():
    """
    Reads the CPU temperature from the thermal zone file and returns it in Celsius.
    """
    with open("/sys/class/thermal/thermal_zone0/temp") as f:
        return int(f.read()) / 1000


try:
    while True:
        temp = get_temp()
        if temp >= ON_TEMP and not FAN_ON:
            GPIO.output(FAN_PIN, GPIO.HIGH)
            FAN_ON = True
            print(f"Fan ON - Temp: {temp:.1f}°C")
            logger.info(f"Fan ON - Temp: {temp:.1f}°C")
        elif temp <= OFF_TEMP and FAN_ON:
            GPIO.output(FAN_PIN, GPIO.LOW)
            FAN_ON = False
            print(f"Fan OFF - Temp: {temp:.1f}°C")
            logger.info("Fan OFF - Temp: %.1f°C", temp)
        time.sleep(5)
except KeyboardInterrupt:
    print("Exiting fan controller...")
    logger.info("Exiting fan controller...")
    GPIO.cleanup()
