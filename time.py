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
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd5in79

logging.basicConfig(level=logging.DEBUG)

# CONFIGURABLE OPTIONS
mode = "inverted"  # options: classic, inverted, invert_numbers
font_choice = "DS-DIGIT.TTF"  # choose from available fonts listed below

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

try:
    logging.info("Starting e-Paper Clock")

    epd = epd5in79.EPD()
    epd.init()
    epd.Clear()
    time.sleep(1)

    font = ImageFont.truetype(os.path.join(picdir, font_choice), 300)

    while True:
        # Set background color based on mode
        bg_color = 255 if mode == "classic" else 0
        text_color = 0 if mode == "classic" else 255

        image = Image.new('1', (epd.width, epd.height), bg_color)
        draw = ImageDraw.Draw(image)

        current_time = time.strftime('%I:%M').lstrip('0')

        # Get accurate text bounding box
        bbox = draw.textbbox((0, 0), current_time, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (epd.width - text_width) // 2
        y = (epd.height - text_height) // 2 - bbox[1]  # Shift y based on bbox

        draw.text((x, y), current_time, font=font, fill=text_color)

        if mode == "invert_numbers":
            inverted = Image.new('1', (epd.width, epd.height), 255)
            inverted.paste(image)
            image = Image.eval(inverted, lambda px: 255 - px)

        # Always rotate the final image
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
    exit()
