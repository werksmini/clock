#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import RPi.GPIO as GPIO

# Setup directories
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import time
import logging
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd5in79

logging.basicConfig(level=logging.DEBUG)

# CONFIG
mode = "inverted"
font_size = 200
time_format_24h = False  # Start with 12h

available_fonts = [
    "SpaceMono-Regular.ttf",
    "LEDBOARD.TTF",
    "LEDBDREV.TTF",
    "Jersey15-Regular.ttf",
    "FLIPclockwhite.ttf",
    "FLIPclockblack.ttf",
    "16Segments-Basic.otf",
    "DS-DIGIT.TTF",
    "PaletteMosaic-Regular.ttf"
]

font_index = 0

# Rotary Encoder Setup
CLK = 5
DT = 6
SW = 13

GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

last_clk = GPIO.input(CLK)

def change_font(channel):
    global font_index
    clk_state = GPIO.input(CLK)
    dt_state = GPIO.input(DT)

    if clk_state != last_clk:
        if dt_state != clk_state:
            font_index = (font_index + 1) % len(available_fonts)
        else:
            font_index = (font_index - 1) % len(available_fonts)
    time.sleep(0.05)

def toggle_time_format(channel):
    global time_format_24h
    time_format_24h = not time_format_24h
    time.sleep(0.2)

GPIO.add_event_detect(CLK, GPIO.BOTH, callback=change_font, bouncetime=50)
GPIO.add_event_detect(SW, GPIO.FALLING, callback=toggle_time_format, bouncetime=300)

try:
    logging.info("Starting e-Paper Clock")

    epd = epd5in79.EPD()
    epd.init()
    epd.Clear()
    time.sleep(1)

    while True:
        font = ImageFont.truetype(os.path.join(picdir, available_fonts[font_index]), font_size)

        # Set colors
        bg_color = 255 if mode == "classic" else 0
        text_color = 0 if mode == "classic" else 255

        image = Image.new('1', (epd.width, epd.height), bg_color)
        draw = ImageDraw.Draw(image)

        current_time = time.strftime('%H:%M' if time_format_24h else '%I:%M').lstrip('0')

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

        epd.display_Partial(epd.getbuffer(image))
        time.sleep(0.2)

except KeyboardInterrupt:
    logging.info("Interrupted by user")
    epd.init()
    epd.Clear()
    epd.sleep()
    GPIO.cleanup()
    exit()