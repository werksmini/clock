#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os

#test to see if vscode switches to new branch

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
    (0, 1): {"mode": "inverted", "font": "DS-DIGIT.TTF", "size": 250}, #position 3
    (0, 0): {"mode": "inverted", "font": "Roboto-Regular.ttf", "size": 220}, #position 1
    (1, 0): {"mode": "inverted", "font": "WDXLLubrifontJPN-Regular.ttf", "size": 240},   #position 2
    (1, 1): {"mode": "inverted", "font": "Outfit-Regular.ttf", "size": 200},  #position 4
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

    last_switch_state = None  # Track last switch state
    last_display_time = 0
    refresh_interval = 1  # seconds
    full_refresh = True  # Trigger on startup

    while True:
        now = time.time()
        switch_state = get_switch_state()

        if switch_state != last_switch_state:
            logging.info(f"Switch changed to {switch_state}")
            last_switch_state = switch_state
            full_refresh = True
            last_display_time = 0  # Force redraw immediately

        # Only update the display every 1 second
        if now - last_display_time >= refresh_interval:
            profile = font_profiles.get(switch_state, font_profiles[(0, 0)])
            mode = profile["mode"]
            font_choice = profile["font"]
            font_size = profile["size"]

            font = ImageFont.truetype(os.path.join(picdir, font_choice), font_size)

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

            if full_refresh:
                epd.Clear()              # Fully clear display first
                time.sleep(0.1)          # Give it time to settle
                epd.display(epd.getbuffer(image))
                full_refresh = False
            else:
                epd.display_Partial(epd.getbuffer(image))

            last_display_time = now

        time.sleep(0.05)  # Fast input polling (20x per second)

except IOError as e:
    logging.error(e)

except KeyboardInterrupt:
    logging.info("Interrupted by user. Cleaning up...")
    epd.init()
    epd.Clear()
    epd.sleep()
    GPIO.cleanup()
    exit()
