#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os

# Setup directories
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import time
import logging
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd5in79

logging.basicConfig(level=logging.DEBUG)

# --- GPIO setup for 4-position slide switch ---
SWITCH_PIN_A = 27  # GPIO27 (pin 13)
SWITCH_PIN_B = 22  # GPIO22 (pin 15)

GPIO.setmode(GPIO.BCM)
GPIO.setup(SWITCH_PIN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SWITCH_PIN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- Font profiles for each switch position ---
font_profiles = {
    (0, 0): {"mode": "classic", "font": "SpaceMono-Regular.ttf", "size": 250},
    (0, 1): {"mode": "inverted", "font": "DS-DIGIT.TTF", "size": 300},
    (1, 0): {"mode": "invert_numbers", "font": "LEDBDREV.TTF", "size": 200},
    (1, 1): {"mode": "inverted", "font": "FLIPclockblack.ttf", "size": 220},
}

# Available Fonts:
# SpaceMono-Regular.ttf
# LEDBOARD.TTF
# LEDBDREV.TTF
# Jersey15-Regular.ttf
# FLIPclockwhite.ttf
# FLIPclockblack.ttf
# 16Segments-Basic.otf #200 inverted
# 16Segments-Background.otf #doesn't work well
# DS-DIGIT.TTF #300 size inverted
# PaletteMosaic-Regular.ttf
# TOYOTA.otf
# MoiraiOne.ttf

def get_switch_state():
    return (GPIO.input(SWITCH_PIN_A), GPIO.input(SWITCH_PIN_B))

try:
    logging.info("Starting e-Paper Clock")
    epd = epd5in79.EPD()
    epd.init()
    epd.Clear()
    time.sleep(1)

    last_state = None

    while True:
        switch_state = get_switch_state()

        if switch_state != last_state:
            logging.info(f"Switch changed to {switch_state}")
            last_state = switch_state

        profile = font_profiles.get(switch_state, font_profiles[(0, 0)])
        mode = profile["mode"]
        font_choice = profile["font"]
        font_size = profile["size"]

        font = ImageFont.truetype(os.path.join(picdir, font_choice), font_size)

        # Set background color based on mode
        bg_color = 255 if mode == "classic" else 0
        text_color = 0 if mode == "classic" else 255

        image = Image.new('1', (epd.width, epd.height), bg_color)
        draw = ImageDraw.Draw(image)

        current_time = time.strftime('%I:%M').lstrip('0')

        bbox = draw.textbbox((0, 0), current_time, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (epd.width - text_width) // 2
        y = (epd.height - text_height) // 2 - bbox[1]

        draw.text((x, y), current_time, font=font, fill=text_color)

        if mode == "invert_numbers":
            inverted = Image.new('1', (epd.width, epd.height), 255)
            inverted.paste(image)
            image = Image.eval(inverted, lambda px: 255 - px)

        image = image.rotate(180)
        epd.display_Partial(epd.getbuffer(image))
        time.sleep(1)

except IOError as e:
    logging.error(e)

except KeyboardInterrupt:
    logging.info("Interrupted by user. Cleaning up...")
    epd.init()
    epd.Clear()
    epd.sleep()
    GPIO.cleanup()
    exit()
