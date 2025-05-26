#!/usr/bin/python3
# -*- coding:utf-8 -*-
import sys
import os
import time
import logging
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd5in79

# Setup directories
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

# Encoder Pin setup
CLK = 5     # Encoder Pin A
DT = 6      # Encoder Pin B
SW = 13     # Encoder Button

GPIO.setmode(GPIO.BCM)
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

last_clk_state = GPIO.input(CLK)
last_button_state = GPIO.input(SW)

# Fonts and settings
font_list = [
    "SpaceMono-Regular.ttf",
    "LEDBOARD.TTF",
    "LEBDREV.TTF",
    "Jersey15-Regular.ttf",
    "FLIPclockwhite.ttf",
    "FLIPclockblack.ttf",
    "16Segments-Basic.otf",
    "DS-DIGIT.TTF",
    "PaletteMosaic-Regular.ttf",
    "TOYOTA.otf",
    "MoiraiOne.ttf"
]
font_index = 0
time_format_24h = False  # Default to 12-hour
mode = "inverted"  # "classic", "inverted", "invert_numbers"

logging.basicConfig(level=logging.DEBUG)
logging.info("Starting e-Paper Clock with Encoder")

try:
    epd = epd5in79.EPD()
    epd.init()
    epd.Clear()
    time.sleep(1)

    update_count = 0

    while True:
        # === Handle Encoder Rotation ===
        clk_state = GPIO.input(CLK)
        if clk_state == 0 and last_clk_state == 1:  # falling edge
            if GPIO.input(DT) == 1:
                font_index = (font_index + 1) % len(font_list)
            else:
                font_index = (font_index - 1) % len(font_list)
            logging.info(f"Font changed to: {font_list[font_index]}")
        last_clk_state = clk_state

        # === Handle Button Press ===
        button_state = GPIO.input(SW)
        if button_state == GPIO.LOW and last_button_state == GPIO.HIGH:
            time_format_24h = not time_format_24h
            logging.info(f"Toggled time format to {'24h' if time_format_24h else '12h'}")
            time.sleep(0.3)  # Debounce
        last_button_state = button_state

        # === Time Display ===
        font = ImageFont.truetype(os.path.join(picdir, font_list[font_index]), 300)
        current_time = time.strftime('%H:%M' if time_format_24h else '%I:%M').lstrip('0')

        bg_color = 255 if mode == "classic" else 0
        text_color = 0 if mode == "classic" else 255
        image = Image.new('1', (epd.width, epd.height), bg_color)
        draw = ImageDraw.Draw(image)

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

        if update_count % 60 == 0:
            epd.init()
            epd.display(epd.getbuffer(image))  # Full refresh
        else:
            epd.display_Partial(epd.getbuffer(image))  # Partial refresh

        update_count += 1
        time.sleep(1)

except KeyboardInterrupt:
    logging.info("Interrupted. Cleaning up GPIO and e-Paper.")
    GPIO.cleanup()
    epd.init()
    epd.Clear()
    epd.sleep()
except Exception as e:
    logging.error(e)
    GPIO.cleanup()
