#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import time
import logging
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd5in79

logging.basicConfig(level=logging.DEBUG)

# --- Setup directories ---
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

# --- GPIO setup for 4-position slide switch ---
SWITCH_PIN_A = 27  # GPIO27 (pin 13)
SWITCH_PIN_B = 22  # GPIO22 (pin 15)

GPIO.setmode(GPIO.BCM)
GPIO.setup(SWITCH_PIN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SWITCH_PIN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- Font profiles for each switch position ---
font_profiles = {
    (0, 1): {"mode": "inverted", "font": "DS-DIGIT.TTF", "size": 220},  # position 3
    (0, 0): {"mode": "inverted", "font": "Roboto-Regular.ttf", "size": 200},  # position 1
    (1, 0): {"mode": "inverted", "font": "WDXLLubrifontJPN-Regular.ttf", "size": 240},  # position 2
    (1, 1): {"mode": "inverted", "font": "Outfit-Regular.ttf", "size": 230},  # position 4
}

# --- Helper to read switch state ---
def get_switch_state():
    return (GPIO.input(SWITCH_PIN_A), GPIO.input(SWITCH_PIN_B))

try:
    logging.info("Starting e-Paper Clock")
    epd = epd5in79.EPD()
    epd.init()
    epd.Clear()
    time.sleep(1)

    last_switch_state = None
    last_display_time = 0
    last_full_refresh = time.time()
    refresh_interval = 1            # seconds between screen updates
    full_refresh_interval = 300     # seconds between full refreshes (5 minutes)
    full_refresh = True             # force full on startup

    while True:
        now = time.time()
        switch_state = get_switch_state()

        # --- Detect mode/font change ---
        if switch_state != last_switch_state:
            logging.info(f"Switch changed to {switch_state}")
            last_switch_state = switch_state
            full_refresh = True
            last_display_time = 0  # redraw immediately

        # --- Update display every second ---
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
            image = image.rotate(180)

            # --- Full refresh every X minutes or after mode change ---
            if full_refresh or (now - last_full_refresh >= full_refresh_interval):
                logging.info("Performing FULL refresh")
                epd.init()          # reinit display driver
                epd.Clear()         # full clean
                time.sleep(0.2)
                epd.display(epd.getbuffer(image))
                full_refresh = False
                last_full_refresh = now
            else:
                epd.display_Partial(epd.getbuffer(image))

            last_display_time = now

        time.sleep(0.05)  # quick poll for switch state changes

except IOError as e:
    logging.error(e)

except KeyboardInterrupt:
    logging.info("Interrupted by user. Cleaning up...")
    epd.init()
    epd.Clear()
    epd.sleep()
    GPIO.cleanup()
    exit()
