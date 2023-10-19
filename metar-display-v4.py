#!/usr/bin/python3
#metar-display-v4.py - by Mark Harris.
#     Updated to work with Python 3.7
#     Adds TAF display when rotary switch is positioned accordingly. Default data user selectable if no rotary switch is used.
#     Adds MOS data display when rotary switch is positioned accordingly.
#     Adds timer routine to turn off map at night (or whenever) then back on again automatically. Pushbutton to turn on temporarily
#     Fixed bug where 'LGND' wasn't filtered from URL.
#     Changed welcome message to stop scrolling.
#     Add auto restart if config.py is saved so new settings will automatically be read by scripts
#     Add IP display with welcome message if desired.
#     Added internet availability check and retry if necessary. This should help when power is disrupted and board reboots before router does.
#     Added Logging capabilities which is stored in /NeoSectional/logfile.log
#     Added ability to display wind direction as an arrow or numbers.
#     Fixed bug when a blank screen is desired and abovekts is used as well. Thanks Lance.
#     Added Top 10 list for Heat Map
#     Added Gusting Winds, CALM and VRB based on Lance Blank's work. Thank you Lance.
#     Added ability to detect a Rotary Switch is NOT installed and react accordingly.
#     Added ability to specifiy an exclusive subset of airports to display.
#     Added ability to display text rotated 180 degrees, and/or reverse order of display of multiple OLED's if wired backwards
#     Added fix to Sleep Timer. Thank You to Matthew G for your code to make this work.
#     Added feature for static (no scroll) of OLED displays. Look for %%% to denote changed code

#Displays airport ID, wind speed in kts and wind direction on an LCD or OLED display.
#Wind direction uses an arrow to display general wind direction from the 8 cardinal points on a compass.
#The settings below can be changed to display the top X number of airports or just those whose winds are above a specified speed.
#The OLED display can be inverted, and even the highest wind can be displayed in bold font.
#A welcome message can be displayed each time the FAA weather is updated. (Multi-Oleds only)
#Also, the local and zulu time can be displayed after each group of high winds have been displayed. (Multi-Oleds only)

#To be used along with metar-v4.py if an LCD or OLED display is used.
#startup.py is run at boot-up by /etc/rc.local to create 2 threads. One running this script and the other thread running metar-v4.py
#startup.py taken from; https://raspberrypi.stackexchange.com/questions/39108/how-do-i-start-two-different-python-scripts-with-rc-local

#Currently written for 16x2 LCD panel wired in 4 bit arrangement or a Single OLED Display SSD1306.SSD1306_128_64 or 128x32 with changes to text output.
#With a TCA9548A I2C Multiplexer, up to 8 OLED displays can be used and some of the features need multiple OLED's. https://www.adafruit.com/product/2717
#For info on using the TCA9548A see;
#https://buildmedia.readthedocs.org/media/pdf/adafruit-circuitpython-tca9548a/latest/adafruit-circuitpython-tca9548a.pdf

#An IC238 Light Sensor can be used to control the brightness of the OLED displays, or a potentiometer for an LCD Display.
#For more info on the sensor visit; http://www.uugear.com/portfolio/using-light-sensor-module-with-raspberry-pi/

#Important note: to insure the displayed time is correct, follow these instructions
#   sudo raspi-config
#   Select Internationalisation Options
#   Select I2 Change Timezone
#   Select your Geographical Area
#   Select your nearest City
#   Select Finish
#   Select Yes to reboot now

#RPI GPIO Pinouts reference
###########################
#    3V3  (1) (2)  5V     #
#  GPIO2  (3) (4)  5V     #
#  GPIO3  (5) (6)  GND    #
#  GPIO4  (7) (8)  GPIO14 #
#    GND  (9) (10) GPIO15 #
# GPIO17 (11) (12) GPIO18 #
# GPIO27 (13) (14) GND    #
# GPIO22 (15) (16) GPIO23 #
#    3V3 (17) (18) GPIO24 #
# GPIO10 (19) (20) GND    #
#  GPIO9 (21) (22) GPIO25 #
# GPIO11 (23) (24) GPIO8  #
#    GND (25) (26) GPIO7  #
#  GPIO0 (27) (28) GPIO1  #
#  GPIO5 (29) (30) GND    #
#  GPIO6 (31) (32) GPIO12 #
# GPIO13 (33) (34) GND    #
# GPIO19 (35) (36) GPIO16 #
# GPIO26 (37) (38) GPIO20 #
#    GND (39) (40) GPIO21 #
###########################

#Import needed libraries
#Misc libraries
import urllib.request, urllib.error, urllib.parse
import requests
import xml.etree.ElementTree as ET
import time
import sys
import os
from os.path import getmtime
from datetime import datetime
from datetime import timedelta
from datetime import time as time_ #part of timer fix
import operator
import RPi.GPIO as GPIO
import socket
import collections
import re
import random
import logging
import logzero
from logzero import logger
import config                                   #User settings stored in file config.py, used by other scripts
import admin

#LCD Libraries - Only needed if an LCD Display is to be used. Comment out if you would like.
#Visit; http://www.circuitbasics.com/raspberry-pi-lcd-set-up-and-programming-in-python/ and follow info for 4-bit mode.
#To install RPLCD library;
#    sudo pip3 install RPLCD
import RPLCD as RPLCD
from RPLCD.gpio import CharLCD

#OLED libraries - Only needed if OLED Display(s) are to be used. Comment out if you would like.
import smbus2                                   #Install smbus2; sudo pip3 install smbus2
#   git clone https://github.com/adafruit/Adafruit_Python_GPIO.git
#   cd Adafruit_Python_GPIO
#   sudo python3 setup.py install
from Adafruit_GPIO import I2C
import Adafruit_SSD1306                         #sudo pip3 install Adafruit-SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# Setup rotating logfile with 3 rotations, each with a maximum filesize of 1MB:
version = admin.version                         #Software version
loglevel = config.loglevel
loglevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
logzero.loglevel(loglevels[loglevel])           #Choices in order; DEBUG, INFO, WARNING, ERROR
logzero.logfile("/NeoSectional/logfile.log", maxBytes=1e6, backupCount=1)
logger.info("\n\nStartup of metar-display-v4.py Script, Version " + version)
logger.info("Log Level Set To: " + str(loglevels[loglevel]))

#****************************************************************************
#*  User defined Setting Here - Make changes in config.py instead of here.  *
#****************************************************************************

# Testing Socket Time-out, thanks Eric Blevins. From https://python.readthedocs.io/en/stable/howto/urllib2.html#sockets-and-layers
# timeout in seconds
timeout = 30
socket.setdefaulttimeout(timeout)

#rotate and oled wiring order
rotyesno = config.rotyesno                      #Rotate 180 degrees, 0 = No, 1 = Yes
oledposorder = config.oledposorder              #Oled Wiring Position, 0 = Normally pos 0-7, 1 = Backwards pos 7-0

#create list of airports to exclusively display on the OLEDs
exclusive_list = config.exclusive_list          #Must be in this format: ['KFLG', 'KSEZ', 'KPHX', 'KCMR', 'KINW', 'KPAN', 'KDVT', 'KGEU']
exclusive_flag = config.exclusive_flag          #0 = Do not use exclusive list, 1 = only use exclusive list

#Specific Variables to default data to display if Rotary Switch is not installed.
wind_numorarrow = config.wind_numorarrow        #0 = Display Wind direction using arrows, 1 = Display wind direction using numbers.

#Typically if rotary switch is not used, METAR's will be displayed exclusively. But if metar_taf = 0, then TAF's can be the default.
hour_to_display = config.time_sw0               #hour_to_display #Offset in HOURS to choose which TAF to display
metar_taf_mos = config.data_sw0                 #config.metar_taf_mos    #0 = Display TAF, 1 = Display METAR, 2 = Display MOS, 3 = Heat Map
toggle_sw = -1                                  #Set toggle_sw to an initial value that forces rotary switch to dictate data displayed.

data_sw0 = config.data_sw0                      #User selectable source of data on Rotary Switch position 0. 0 = TAF, 1 = METAR, 2 = MOS
data_sw1 = config.data_sw1                      #User selectable source of data on Rotary Switch position 1. 0 = TAF, 1 = METAR, 2 = MOS
data_sw2 = config.data_sw2                      #User selectable source of data on Rotary Switch position 2. 0 = TAF, 1 = METAR, 2 = MOS
data_sw3 = config.data_sw3                      #User selectable source of data on Rotary Switch position 3. 0 = TAF, 1 = METAR, 2 = MOS
data_sw4 = config.data_sw4                      #User selectable source of data on Rotary Switch position 4. 0 = TAF, 1 = METAR, 2 = MOS
data_sw5 = config.data_sw5                      #User selectable source of data on Rotary Switch position 5. 0 = TAF, 1 = METAR, 2 = MOS
data_sw6 = config.data_sw6                      #User selectable source of data on Rotary Switch position 6. 0 = TAF, 1 = METAR, 2 = MOS
data_sw7 = config.data_sw7                      #User selectable source of data on Rotary Switch position 7. 0 = TAF, 1 = METAR, 2 = MOS
data_sw8 = config.data_sw8                      #User selectable source of data on Rotary Switch position 8. 0 = TAF, 1 = METAR, 2 = MOS
data_sw9 = config.data_sw9                      #User selectable source of data on Rotary Switch position 9. 0 = TAF, 1 = METAR, 2 = MOS
data_sw10 = config.data_sw10                    #User selectable source of data on Rotary Switch position 10. 0 = TAF, 1 = METAR, 2 = MOS
data_sw11 = config.data_sw11                    #User selectable source of data on Rotary Switch position 11. 0 = TAF, 1 = METAR, 2 = MOS

time_sw0 = config.time_sw0                      #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw1 = config.time_sw1                      #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw2 = config.time_sw2                      #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw3 = config.time_sw3                      #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw4 = config.time_sw4                      #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw5 = config.time_sw5                      #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw6 = config.time_sw6                      #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw7 = config.time_sw7                      #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw8 = config.time_sw8                      #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw9 = config.time_sw9                      #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw10 = config.time_sw10                    #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw11 = config.time_sw11                    #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.

displayIP = config.displayIP                    #display IP address with welcome message, 0 = No, 1 = Yes

#MOS Config settings
prob = config.prob                              #probability threshhold in Percent to assume reported weather will be displayed on map or not.

#Specific settings for on/off timer. Used to turn off LED's at night if desired.
#Verify Raspberry Pi is set to the correct time zone, otherwise the timer will be off.
usetimer = config.usetimer                      #0 = No, 1 = Yes. Turn the timer on or off with this setting
offhour = config.offhour                        #Use 24 hour time. Set hour to turn off display
offminutes = config.offminutes                  #Set minutes to turn off display
onhour = config.onhour                          #Use 24 hour time. Set hour to turn on display
onminutes = config.onminutes                    #Set minutes to on display

#Sleep Timer settings
tempsleepon = config.tempsleepon                #Set number of MINUTES to turn map on temporarily during sleep mode
sleepmsg = config.sleepmsg                      #Display message "Sleeping". 0 = No, 1 = Yes.

#Display type to use. Both can be used but will delay before updating each display.
lcddisplay = config.lcddisplay                  #1 = Yes, 0 = No. Using an LCD to display the highest winds. Scripted for 64x2 LCD display use.
oledused = config.oledused                      #1 = Yes, 0 = No. Using a single OLED to display the highest winds and airports

#Misc Settings - Should match the values in metar-v3.py
update_interval = config.update_interval        #Number of MINUTES between FAA updates - 15 minutes is a good compromise.
metar_age = config.metar_age                    #Metar Age in HOURS. This will pull the latest metar that has been published within the timeframe listed here.
num2display = config.num2display                #number of highest wind airports to display. Can be as high as airports listed in airports file. 5 to 10 good number.
abovekts = config.abovekts                      #1 = Yes, 0 = No. If "Yes" then only display high winds above value stored in 'minwinds' below.
minwinds = config.max_wind_speed                #Value in knots to filter high winds. if abovekts is 1 then don't display winds less than this value on LCD/OLED

#LCD Display settings
lcdpause = config.lcdpause                      #pause between character movements in scroll.

#OLED Display settings
numofdisplays = config.numofdisplays            #Number of OLED displays being used. 1 Oled minimum. With TCA9548A I2C Multiplexer, 8 can be used.
oledpause = config.oledpause                    #Pause time in seconds between airport display updates
fontsize = config.fontsize                      #Size of font for OLED display. 24 works well with current font type
boldhiap = config.boldhiap                      #1 = Yes, 0 = No. Bold the text for the airport that has the highest windspeed.
blankscr = config.blankscr                      #1 = Yes, 0 = No. Add a blank screen between the group of airports to display.
offset = config.offset                          #Pixel offset for OLED text display vertically. Leave at 3 for current font type.
border = config.border                          #0 = no border, 1 = yes border. Either works well.
dimswitch = config.dimswitch                    #0 = Full Bright, 1 = Low Bright, 2 = Medium Bright, if IC238 Light Sensor is NOT used.
dimmin = config.dimmin                          #Set value 0-255 for the minimum brightness (0=darker display, but not off)
dimmax = config.dimmax                          #Set value 0-255 for the maximum brightness (bright display)
invert = config.invert                          #0 = normal display, 1 = inverted display, supercedes toginv. Normal = white text on black background.
toginv = config.toginv                          #0 = no toggle of inverted display. 1 = toggle inverted display between groups of airports
usewelcome = config.usewelcome                  #0 = No, 1 = Yes. Display a welcome message on the displays?
welcome = config.welcome                        #will display each time the FAA weather is updated.
displaytime = config.displaytime                #0 = No, 1 = Yes. Display the local and Zulu Time between hi-winds display
scrolldis = config.scrolldis                    #0 = Scroll display to left, 1 = scroll display to right, 2 = no scroll


#*********************************
#* End of User Defined Settings  *
#*********************************

#misc settings that won't normally need to be changed.
fontindex = 0                                   #Font selected may have various versions that are indexed. 0 = Normal. Leave at 0 unless you know otherwise.
backcolor = 0                                   #0 = Black, background color for OLED display. Shouldn't need to change
fontcolor = 255                                 #255 = White, font color for OLED display. Shouldn't need to change
temp_time_flag = 0                              #Set flag for next round of tempsleepon activation (temporarily turns on map when in sleep mode)

#Set general GPIO parameters
GPIO.setmode(GPIO.BCM)                          #set mode to BCM and use BCM pin numbering, rather than BOARD pin numbering.
GPIO.setwarnings(False)

#Set GPIO pin 4 for IC238 Light Sensor, if used.
GPIO.setup(4, GPIO.IN)                          #set pin 4 as input for light sensor, if one is used. If no sensor used board remains at high brightness always.

#set GPIO pin 22 to momentary push button to force FAA Weather Data update if button is used.
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Setup GPIO pins for rotary switch to choose between METARs, or TAFs and which hour of TAF
#Not all the pins are required to be used. If only METARS are desired, then no Rotary Switch is needed.
#A rotary switch with up to 12 poles can be installed, but as few as 2 poles will switch between METAR's and TAF's
GPIO.setup(0, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 0 to ground for METARS
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 5 to ground for TAF + 1 hour
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 6 to ground for TAF + 2 hours
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 13 to ground for TAF + 3 hours
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 19 to ground for TAF + 4 hours
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 26 to ground for TAF + 5 hours
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 21 to ground for TAF + 6 hours
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 20 to ground for TAF + 7 hours
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 16 to ground for TAF + 8 hours
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 12 to ground for TAF + 9 hours
GPIO.setup(1, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 1 to ground for TAF + 10 hours
GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 7 to ground for TAF + 11 hours

# Raspberry Pi pin configuration:
RST = None                                      #on the PiOLED this pin isnt used

#Setup Adafruit library for OLED display.
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST) #128x64 or 128x32 - disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

TCA_ADDR = 0x70                                 #use cmd i2cdetect -y 1 to ensure multiplexer shows up at addr 0x70
tca = I2C.get_i2c_device(address=TCA_ADDR)
port = 1                                        #Default port. set to 0 for original RPi or Orange Pi, etc
bus = smbus2.SMBus(port)                        #From smbus2 set bus number

#Setup paths for restart on change routine. Routine from;
#https://blog.petrzemek.net/2014/03/23/restarting-a-python-script-within-itself
LOCAL_CONFIG_FILE_PATH = '/NeoSectional/config.py'
WATCHED_FILES = [LOCAL_CONFIG_FILE_PATH, __file__]
WATCHED_FILES_MTIMES = [(f, getmtime(f)) for f in WATCHED_FILES]
logger.info('Watching ' + LOCAL_CONFIG_FILE_PATH + ' For Change')

#Timer calculations - Part of Timer Fix - Thank You to Matthew G
now = datetime.now()                    #Get current time and compare to timer setting
lights_out = time_(offhour, offminutes, 0)
timeoff = lights_out
lights_on = time_(onhour, onminutes, 0)
end_time = lights_on
delay_time = 10                         #Number of seconds to delay before retrying to connect to the internet.
temp_lights_on = 0                      #Set flag for next round if sleep timer is interrupted by button push.

#MOS related settings
mos_filepath = '/NeoSectional/GFSMAV'           #location of the downloaded local MOS file.
categories = ['HR', 'CLD', 'WDR', 'WSP', 'P06', 'T06', 'POZ', 'POS', 'TYP', 'CIG','VIS','OBV'] #see legend below
obv_wx = {'N': 'None', 'HZ': 'HZ','BR': 'RA','FG': 'FG','BL': 'HZ'} #Decode from MOS to TAF/METAR
typ_wx = {'S': 'SN','Z': 'FZRA','R': 'RA'}      #Decode from MOS to TAF/METAR
mos_dict = collections.OrderedDict()            #Outer Dictionary, keyed by airport ID
hour_dict = collections.OrderedDict()           #Middle Dictionary, keyed by hour of forcast. Will contain a list of data for categories.
ap_flag = 0                                     #Used to determine that an airport from our airports file is currently being read.
hmdata_dict = {}                                #Used for top 10 list for heat map
startnum = 0                                    #Used for cycling through the number of displays used.
stopnum = numofdisplays                         #Same
stepnum = 1                                     #Same

#Get info to display active IP address
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
logger.info("Settings Loaded")

#Functions
# Part of Timer Fix - Thank You to Matthew G
# See if a time falls within a range
def time_in_range(start, end, x):
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

#Functions for LCD Display
def write_to_lcd(lcd, framebuffer, num_cols):
    #Write the framebuffer out to the specified LCD.
    lcd.home()
    for row in framebuffer:
        lcd.write_string(row.ljust(num_cols)[:num_cols])
        lcd.write_string('\r\n')

def loop_string(string, lcd, framebuffer, row, num_cols, delay=0.4):
    padding = ' ' * num_cols
    s = padding + string + padding
    for i in range(len(s) - num_cols + 1):
        framebuffer[row] = s[i:i+num_cols]
        write_to_lcd(lcd, framebuffer, num_cols)
        time.sleep(delay)

#Functions for OLED display
def tca_select(channel):                        #Used to tell the multiplexer which oled display to send data to.
    #Select an individual channel
    if channel > 7 or numofdisplays < 2:        #Verify we need to use the multiplexer.
        return
    tca.writeRaw8(1 << channel)                 #from Adafruit_GPIO I2C

def oledcenter(txt, ch, font, dir=0, dim=dimswitch, onoff = 0, pause = 0): #Center text vertically and horizontally
    tca_select(ch)                              #Select the display to write to
    oleddim(dim)                                #Set brightness, 0 = Full bright, 1 = medium bright, 2 = low brightdef oledcenter(txt): #Center text vertically and horizontally
    draw.rectangle((0, 0, width-1, height-1), outline=border, fill=backcolor) #blank the display
    x1, y1, x2, y2 = 0, 0, width, height        #create boundaries of display

    if dir == "" or txt == '\n' or 'Updated' in txt or 'Calm' in txt: #Print text other than wind directions and speeds
        pass

    elif 'METARs' in txt or 'TAF' in txt or 'MOS' in txt or 'Heat' in txt: #Print text other than wind directions and speeds
        pass

    elif wind_numorarrow == 0:                  #draw wind direction using arrows
        arrowdir = winddir(dir)                 #get proper proper arrow to display
        draw.text((96, 37), arrowdir, font=arrows, fill=fontcolor) #lower right of oled
        txt = txt + 'kts'
        pass

    else:                                       #draw wind direction using numbers
        ap, wndsp = txt.split('\n')
        wnddir = str(dir)

        if len(wnddir) == 2:                    #pad direction with zeros to get 3 digits.
            wnddir = '0' + wnddir

        elif len(wnddir) == 1:
            wnddir = '00' + wnddir

        #Calm and VRB winds contributed by Lance Black - Thank you Lance
        if wnddir == '000' and wndsp == '0':
            txt = ap + "\n" + 'Calm'

        elif wnddir == '000' and wndsp >= '1' and gust > 0:
            txt = ap + "\n" + 'VRB@' + wndsp + 'g' + str(gust)

        elif wnddir == '000' and wndsp >= '1' and gust == 0:
            txt = ap + "\n" + 'VRB@' + wndsp + 'kts'

        elif gust == 0 or gust == '' or gust is None: #Lance Blank
            txt = ap + '\n' + wnddir + chr(176) + '@' + wndsp + 'kts' #'360@21kts' layout

        elif gust > 0:
            txt = ap + '\n' + wnddir + '@' + wndsp + 'g' + str(gust) #Lance Blank - '360@5g12' layout

        else:
            txt = ap + "\n" + wndsp + 'kts'

    w, h = draw.textsize(txt, font=font)        #get textsize of what is to be displayed
    x = (x2 - x1 - w)/2 + x1                    #calculate center for text
    y = (y2 - y1 - h)/2 + y1 - offset

    draw.text((x, y), txt, align='center', font=font, fill=fontcolor) #Draw the text to buffer

    invertoled(onoff)                           #invert display if set
    rotate180(rotyesno)                         #Rotate display if setrotate180

    disp.image(image)                           #Display image
    disp.display()                              #display text in buffer

    time.sleep(pause)                           #pause long enough to be read

def winddir(wndir=0):                           #Using the arrows.ttf font return arrow to represent wind direction at airport
    if (wndir >= 338 and wndir <= 360) or (wndir >= 1 and wndir <= 22): #8 arrows representing 45 degrees each around the compass.
        return 'd'                              #wind blowing from the north (pointing down)
    elif wndir >= 23 and wndir <= 67:
        return 'f'                              #wind blowing from the north-east (pointing lower-left)
    elif wndir >= 68 and wndir <= 113:
        return 'b'                              #wind blowing from the east (pointing left)
    elif wndir >= 114 and wndir <= 159:
        return 'e'                              #wind blowing from the south-east (pointing upper-left)
    elif wndir >= 160 and wndir <= 205:
        return 'c'                              #wind blowing from the south (pointing up)
    elif wndir >= 206 and wndir <= 251:
        return 'g'                              #wind blowing from the south-west (pointing upper-right)
    elif wndir >= 252 and wndir <= 297:
        return 'a'                              #wind blowing from the west (pointing right)
    elif wndir >= 298 and wndir <= 337:
        return 'h'                              #wind blowing from the north-west (pointing lower-right)
    else:
        return ''                               #No arrow returned

def oleddim(level=0): #Dimming routine. 0 = Full Brightness, 1 = low brightness, 2 = medium brightness. See https://www.youtube.com/watch?v=hFpXfSnDNSY a$
    if level == 0: #https://github.com/adafruit/Adafruit_Python_SSD1306/blob/master/Adafruit_SSD1306/SSD1306.py for more info.
        disp.command(0x81)                      #SSD1306_SETCONTRAST = 0x81
        disp.command(dimmax)
        disp.command(0xDB)                      #SSD1306_SETVCOMDETECT = 0xDB
        disp.command(dimmax)

    if level == 1 or level == 2:
        disp.command(0x81)                      #SSD1306_SETCONTRAST = 0x81
        disp.command(dimmin)

    if level == 1:
        disp.command(0xDB)                      #SSD1306_SETVCOMDETECT = 0xDB
        disp.command(dimmin)

def invertoled(i):                              #Invert display pixels. Normal = white text on black background.
    if i:                                       #Inverted = black text on white background #0 = Normal, 1 = Inverted
        disp.command(0xA7)                      #SSD1306_INVERTDISPLAY
    else:
        disp.command(0xA6)                      #SSD1306_NORMALDISPLAY

def rotate180(i):                               #Rotate display 180 degrees to allow mounting of OLED upside down
    if i:
        #Y Direction
        disp.command(0xA0)
        #X Direction
        disp.command(0xC0)

    else:
        pass

def clearoleddisplays():
    for j in range(numofdisplays):
        tca_select(j)
#        disp.clear()                            #commenting this out sped up the display refresh.
        draw.rectangle((0,0,width-1,height-1), outline=border, fill=backcolor)
        disp.image(image)
        disp.display()

#Compare current time plus offset to TAF's time period and return difference
def comp_time(taf_time):
    global current_zulu
    datetimeFormat = ('%Y-%m-%dT%H:%M:%SZ')
    date1 = taf_time
    date2 = current_zulu
    diff = datetime.strptime(date1, datetimeFormat) - datetime.strptime(date2, datetimeFormat)
    diff_minutes = int(diff.seconds/60)
    diff_hours = int(diff_minutes/60)
    return diff.seconds, diff_minutes, diff_hours, diff.days

#Used by MOS decode routine. This routine builds mos_dict nested with hours_dict
def set_data():
    global hour_dict
    global mos_dict
    global dat0, dat1, dat2, dat3, dat4, dat5, dat6, dat7
    global apid
    global temp
    global keys

    #Clean up line of MOS data.
    if len(temp) >= 0:                          #this check is unneeded. Put here to vary length of list to clean up.
        temp1 = []
        tmp_sw = 0

        for val in temp:                        #Check each item in the list
            val = val.lstrip()                  #remove leading white space
            val = val.rstrip('/')               #remove trailing /

            if len(val) == 6:                   #this is for T06 to build appropriate length list
                temp1.append('0')               #add a '0' to the front of the list. T06 doesn't report data in first 3 hours.
                temp1.append(val)               #add back the original value taken from T06
                tmp_sw = 1                      #Turn on switch so we don't go through it again.

            elif len(val) > 2 and tmp_sw == 0:  #if item is 1 or 2 chars long, then bypass. Otherwise fix.
                pos = val.find('100')           #locate first 100
                tmp = val[0:pos]                #capture the first value which is not a 100
                temp1.append(tmp)               #and store it in temp list.

                k = 0
                for j in range(pos, len(val), 3): #now iterate through remainder
                    temp1.append(val[j:j+3])    #and capture all the 100's
                    k += 1
            else:
                temp1.append(val)               #Store the normal values too.

        temp = temp1

    #load data into appropriate lists by hours designated by current MOS file
    #clean up data by removing '/' and spaces
    temp0 = ([x.strip() for x in temp[0].split('/')])
    temp1 = ([x.strip() for x in temp[1].split('/')])
    temp2 = ([x.strip() for x in temp[2].split('/')])
    temp3 = ([x.strip() for x in temp[3].split('/')])
    temp4 = ([x.strip() for x in temp[4].split('/')])
    temp5 = ([x.strip() for x in temp[5].split('/')])
    temp6 = ([x.strip() for x in temp[6].split('/')])
    temp7 = ([x.strip() for x in temp[7].split('/')])

    #build a list for each data group. grab 1st element [0] in list to store.
    dat0.append(temp0[0])
    dat1.append(temp1[0])
    dat2.append(temp2[0])
    dat3.append(temp3[0])
    dat4.append(temp4[0])
    dat5.append(temp5[0])
    dat6.append(temp6[0])
    dat7.append(temp7[0])

    j = 0
    for key in keys:                            #add cat data to the hour_dict by hour

        if j == 0:
            hour_dict[key] = dat0
        elif j == 1:
            hour_dict[key] = dat1
        elif j == 2:
            hour_dict[key] = dat2
        elif j == 3:
            hour_dict[key] = dat3
        elif j == 4:
            hour_dict[key] = dat4
        elif j == 5:
            hour_dict[key] = dat5
        elif j == 6:
            hour_dict[key] = dat6
        elif j == 7:
            hour_dict[key] = dat7
        j += 1

        mos_dict[apid] = hour_dict              #marry the hour_dict to the proper key in mos_dict

##########################
# Start of executed code #
##########################
while True:
    logger.info('Start of metar-display-v4.py executed code main loop')
    #Time calculations, dependent on 'hour_to_display' offset. this determines how far in the future the TAF data should be.
    #This time is recalculated everytime the FAA data gets updated
    zulu = datetime.utcnow() + timedelta(hours=hour_to_display) #Get current time plus Offset
    current_zulu = zulu.strftime('%Y-%m-%dT%H:%M:%SZ') #Format time to match whats reported in TAF
    current_hr_zulu = zulu.strftime('%H')       #Zulu time formated for just the hour, to compare to MOS data

    logger.debug('datetime - ' + str(datetime.utcnow()))
    logger.debug('zulu - ' + str(zulu))
    logger.debug('hour_to_display - ' + str(hour_to_display))
    logger.debug('current_zulu - ' + str(current_zulu))

    #Get current date and time
    now = datetime.now()
    dt_string = now.strftime("%I:%M%p")         #12:00PM format

    #Dictionary definitions. Need to reset whenever new weather is received
    stationiddict = {}                          #hold the airport identifiers
    windsdict = {}                              #holds the wind speeds by identifier
    wnddirdict = {}                             #holds the wind direction by identifier
    wxstringdict = {}                           #holds the weather conditions by identifier
    wndgustdict = {}                            #hold wind gust by identifier - Mez

    #read airports file - read each time weather is updated in case a change to "airports" file was made while script was running.
    try:
        with open("/NeoSectional/airports") as f:
            airports = f.readlines()
    except IOError as error:
        logger.error('Airports file could not be loaded.')
        logger.error(error)
        break

    airports = [x.strip() for x in airports]
    logger.info("Airports File Loaded")

    #read hmdata file and display the top 10 airports on the OLEDs
    try:
        with open("/NeoSectional/hmdata") as f:
            hmdata = f.readlines()
    except IOError as error:
        logger.error('Heat Map file could not be loaded.')
        logger.error(error)
        break

    hmdata = [x.strip() for x in hmdata]
    logger.info("Heat Map File Loaded")

    for line in hmdata:
        hmap, numland = line.split()
        hmdata_dict[hmap] = int(numland)

    hmdata_sorted = sorted(hmdata_dict.items(), key=lambda x:x[1], reverse=True)
    hmdata_sorted.insert(0, 'Top AP\nLandings')
    print(hmdata_sorted)

    #depending on what data is to be displayed, either use an URL for METARs and TAFs or read file from drive (pass).
    if metar_taf_mos == 1: #Check to see if the script should display TAF data (0) or METAR data (1)
        #Define URL to get weather METARS. If no METAR reported withing the last 2.5 hours, Airport LED will be white (nowx).
        url = f"https://aviationweather.gov/api/data/metar?hours={metar_age}&ids={apts}"
        logger.info(f"METAR Data Loading from url: {url}")

    elif metar_taf_mos == 0: #TAF data
        #Define URL to get weather URL for TAF. If no TAF reported for an airport, the Airport LED will be white (nowx).
        url = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=tafs&requestType=retrieve&format=xml&mostRecentForEachStation=constraint&hoursBeforeNow="+str(metar_age)+"&stationString="
        logger.info("TAF Data Loading")

    elif metar_taf_mos == 2:                    #MOS data. This is not accessible in the same way as METARs and TAF's.
        pass                                    #This elif is not strictly needed and is only here for clarity
        logger.info("MOS Data Loading")

    elif metar_taf_mos == 3:                    #Heat Map data.
        pass                                    #This elif is not strictly needed and is only here for clarity
        logger.info("Heat Map Data Loading")

    #Build URL to submit to FAA with the proper airports from the airports file
    if metar_taf_mos != 2 and metar_taf_mos != 3:
        for airportcode in airports:
            if airportcode == "NULL" or airportcode == "LGND":
                continue
            url = url + airportcode + ","
        url = url[:-1]                          #strip trailing comma from string
        logger.debug(url)

        while True:                             #check internet availability and retry if necessary. Power outage, map may boot quicker than router.
            try:
                ret = requests.get(url, headers={'Accept': 'application/xml'})
                logger.info('Internet Available')
                logger.info(url)
                break
            except:
                logger.warning('FAA Data is Not Available')
                logger.info(url)
                time.sleep(delay_time)
                pass

        try:
            root = ET.fromstring(ret.text)    #Process XML data returned from FAA
        except  xml.etree.ElementTree.ParseError as ex:
            logger.info(f"failed to parse XML, text: {ret.text}")

    #MOS decode routine
    #MOS data is downloaded daily from; https://www.weather.gov/mdl/mos_gfsmos_mav to the local drive by crontab scheduling.
    #Then this routine reads through the entire file looking for those airports that are in the airports file. If airport is
    #found, the data needed to display the weather for the next 24 hours is captured into mos_dict, which is nested with
    #hour_dict, which holds the airport's MOS data by 3 hour chunks. See; https://www.weather.gov/mdl/mos_gfsmos_mavcard for
    #a breakdown of what the MOS data looks like and what each line represents.
    if metar_taf_mos == 2:
        #Read current MOS text file
        try:
            file = open(mos_filepath, 'r')
            lines = file.readlines()
        except IOError as error:
            logger.error('MOS data file could not be loaded.')
            logger.error(error)
            break

        for line in lines:                      #read the MOS data file line by line0
            line = str(line)

            #Ignore blank lines of MOS airport
            if line.startswith('     '):
                ap_flag = 0
                continue

            #Check for and grab date of MOS
            if 'DT /' in line:
                unused, dt_cat, month, unused, unused, day, unused = line.split(" ",6)
                continue

            #Check for and grab the Airport ID of the current MOS
            if 'MOS' in line:
                unused, apid, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, updt1, updt2, v13 = line.split(" ", 14)
                mos_updt_time = updt1 + ' ' + updt2 #Grab the MOS report's update timestamp
                dt_string = mos_updt_time

                #If this Airport ID is in the airports file then grab all the info needed from this MOS
                if apid in airports:
                    ap_flag = 1
                    cat_counter = 0             #used to determine if a category is being reported in MOS or not. If not, need to inject i$
                    dat0, dat1, dat2, dat3, dat4, dat5, dat6, dat7 = ([] for i in range(8)) #Clear lists
                continue

            #If we just found an airport that is in our airports file, then grab the appropriate weather data from it's MOS
            if ap_flag:
                xtra, cat, value = line.split(" ",2) #capture the category the line read represents
                #Check if the needed categories are being read and if so, grab its data
                if cat in categories:
                    cat_counter += 1            #used to check if a category is not in mos report for airport
                    if cat == 'HR':             #hour designation
                        temp = (re.findall(r'\s?(\s*\S+)', value.rstrip()))     #grab all the hours from line read
                        for j in range(8):
                            tmp = temp[j].strip()
                            hour_dict[tmp] = '' #create hour dictionary based on mos data
                        keys = list(hour_dict.keys()) #Get the hours which are the keys in this dict, so they can be prope$

                    else:
                        #Checking for missing lines of data and x out if necessary.
                        if (cat_counter == 5 and cat != 'P06')\
                                or (cat_counter == 6 and cat != 'T06')\
                                or (cat_counter == 7 and cat != 'POZ')\
                                or (cat_counter == 8 and cat != 'POS')\
                                or (cat_counter == 9 and cat != 'TYP'):

                            #calculate the number of consecutive missing cats and inject 9's into those positions
                            a = categories.index(last_cat)+1
                            b = categories.index(cat)+1
                            c = b - a - 1
                            logger.debug(apid,last_cat,cat,a,b,c)

                            for j in range(c):
                                temp = ['9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9']
                                set_data()
                                cat_counter += 1

                            #Now write the orignal cat data read from the line in the mos file
                            cat_counter += 1
                            hour_dict = collections.OrderedDict() #clear out hour_dict for next airport
                            last_cat = cat
                            temp = (re.findall(r'\s?(\s*\S+)', value.rstrip())) #add the actual line of data read
                            set_data()
                            hour_dict = collections.OrderedDict() #clear out hour_dict for next airport

                        else:
                            #continue to decode the next category data that was read.
                            last_cat = cat      #store what the last read cat was.
                            temp = (re.findall(r'\s?(\s*\S+)', value.rstrip()))
                            set_data()
                            hour_dict = collections.OrderedDict() #clear out hour_dict for next airport

        #Now grab the data needed to display on map. Key: [airport][hr][j] - using nested dictionaries
        #   airport = from airport file, 4 character ID. hr = 1 of 8 three-hour periods of time, 00 03 06 09 12 15 18 21
        #   j = index to weather categories, in this order; 'CLD','WDR','WSP','P06', 'T06', 'POZ', 'POS', 'TYP','CIG','VIS','OBV'.
        #   See; https://www.weather.gov/mdl/mos_gfsmos_mavcard for description of available data.
        for airport in airports:
            if airport in mos_dict:
                logger.debug('\n' + airport)
                logger.debug(categories)

                mos_time = int(current_hr_zulu) + hour_to_display
                if mos_time >= 24:              #check for reset at 00z
                    mos_time = mos_time - 24

                logger.debug(keys)
                for hr in keys:
                    logger.debug(hr + ", " +  str(mos_time) + ", " + str(int(hr)+2.99))

                    if int(hr) <= mos_time <= int(hr)+2.99:

                        cld = (mos_dict[airport][hr][0])
                        wdr = (mos_dict[airport][hr][1]) +'0' #make wind direction end in zero
                        wsp = (mos_dict[airport][hr][2])
                        p06 = (mos_dict[airport][hr][3])
                        t06 = (mos_dict[airport][hr][4])
                        poz = (mos_dict[airport][hr][5])
                        pos = (mos_dict[airport][hr][6])
                        typ = (mos_dict[airport][hr][7])
                        cig = (mos_dict[airport][hr][8])
                        vis = (mos_dict[airport][hr][9])
                        obv = (mos_dict[airport][hr][10])

                        logger.debug(hr+", "+cld+", "+wdr+", "+wsp+", "+p06+", "+t06+", "+poz+", "+pos+", "+typ+", "+cig+", "+vis+", "+obv) #debug

                        #decode the weather for each airport to display on the livesectional map
                        flightcategory = "VFR"  #start with VFR as the assumption
                        if cld in ("OV","BK"):  #If the layer is OVC, BKN, set Flight category based on height of layer

                            if cig <= '2':      #AGL is less than 500:
                                flightcategory = "LIFR"

                            elif cig == '3':    #AGL is between 500 and 1000
                                flightcategory = "IFR"
                            elif '4' <= cig <= '5': #AGL is between 1000 and 3000:
                                flightcategory = "MVFR"

                            elif cig >= '6':    #AGL is above 3000
                                flightcategory = "VFR"

                        #Check visability too.
                        if flightcategory != "LIFR": #if it's LIFR due to cloud layer, no reason to check any other things$

                            if vis <= '2':      #vis < 1.0 mile:
                                flightcategory = "LIFR"

                            elif '3' <= vis < '4': #1.0 <= vis < 3.0 miles:
                                flightcategory = "IFR"

                            elif vis == '5' and flightcategory != "IFR":  #3.0 <= vis <= 5.0 miles
                                flightcategory = "MVFR"

                        logger.debug(flightcategory + " |"),
                        logger.debug('Windspeed = ' + wsp + ' | Wind dir = ' + wdr + ' |'),

                        #decode reported weather using probabilities provided.
                        if typ == '9':          #check to see if rain, freezing rain or snow is reported. If not use obv weather
                            wx = obv_wx[obv]    #Get proper representation for obv designator
                        else:
                            wx = typ_wx[typ]    #Get proper representation for typ designator

                            if wx == 'RA' and int(p06) < prob:
                                if obv != 'N':
                                    wx = obv_wx[obv]
                                else:
                                    wx = 'NONE'

                            if wx == 'SN' and int(pos) < prob:
                                wx = 'NONE'

                            if wx == 'FZRA' and int(poz) < prob:
                                wx = 'NONE'

                            if t06 == '' or t06 is None:
                                t06 = '0'

                            if int(t06) > prob: #check for thunderstorms
                                wx = 'TSRA'
                            else:
                                wx = 'NONE'

                        logger.debug('Reported Weather = ' + wx)

                #Connect the information from MOS to the board
                stationId = airport

                #grab wind speeds from returned MOS data
                if wsp is None:                 #if wind speed is blank, then bypass
                    windspeedkt = 0
                elif wsp == '99':               #Check to see if the MOS data didn't report a windspeed for this airport
                    windspeedkt = 0
                else:
                    windspeedkt = int(wsp)

                #grab wind direction from returned FAA data
                if wdr is None:                 #if wind direction is blank, then bypass
                    winddirdegree = 0
                else:
                    winddirdegree = int(wdr)

                #grab Weather info from returned FAA data
                if wx is None:                  #if weather string is blank, then bypass
                    wxstring = "NONE"
                else:
                    wxstring = wx

                logger.debug(stationId+ ", " + str(windspeedkt) + ", " + wxstring)

                #Check for duplicate airport identifier and skip if found, otherwise store in dictionary. covers for dups in "airp$
                if stationId in stationiddict:
                    logger.info(stationId + " Duplicate, only saved first metar category")
                else:
                    stationiddict[stationId] = flightcategory #build category dictionary

                if stationId in windsdict:
                    logger.info(stationId + " Duplicate, only saved first metar category")
                else:
                    windsdict[stationId] = windspeedkt #build windspeed dictionary

                if stationId in wnddirdict:
                    logger.info(stationId + " Duplicate, only saved first metar category")
                else:
                    wnddirdict[stationId] = winddirdegree #build wind direction dictionary

                if stationId in wxstringdict:
                    logger.info(stationId + " Duplicate, only saved first metar category")
                else:
                    wxstringdict[stationId] = wxstring #build weather dictionary
        logger.info("Decoded MOS Data for Display")

    #TAF decode routine. This routine will decode the TAF, pick the appropriate time frame to display.
    if metar_taf_mos == 0:                      #0 equals display TAF.
        #start of TAF decoding routine
        for data in root.iter('data'):
            num_results = data.attrib['num_results'] #get number of airports reporting TAFs to be used for diagnosis only
            logger.debug("\nNum of Airport TAFs = " + num_results)

        for taf in root.iter('TAF'):            #iterate through each airport's TAF
            stationId = taf.find('station_id').text
            logger.debug(stationId)
            logger.debug('Current+Offset Zulu - ' + current_zulu)
            taf_wx_string = ""
            taf_change_indicator = ""
            taf_wind_dir_degrees = ""
            taf_wind_speed_kt = ""
            taf_wind_gust_kt = ""

            for forecast in taf.findall('forecast'): #Now look at the forecasts for the airport

                # Routine inspired by Nick Cirincione.
                flightcategory = "VFR"          #intialize flight category
                taf_time_from = forecast.find('fcst_time_from').text #get taf's from time
                taf_time_to = forecast.find('fcst_time_to').text #get taf's to time

                if forecast.find('wx_string') is not None:
                    taf_wx_string = forecast.find('wx_string').text #get weather conditions

                if forecast.find('change_indicator') is not None:
                    taf_change_indicator = forecast.find('change_indicator').text #get change indicator

                if forecast.find('wind_dir_degrees') is not None:
                    taf_wind_dir_degrees = forecast.find('wind_dir_degrees').text #get wind direction

                if forecast.find('wind_speed_kt') is not None:
                    taf_wind_speed_kt = forecast.find('wind_speed_kt').text #get wind speed

                if forecast.find('wind_gust_kt') is not None:
                    taf_wind_gust_kt = forecast.find('wind_gust_kt').text #get wind gust speed

                if taf_time_from <= current_zulu <= taf_time_to: #test if current time plus offset falls within taf's timeframe
                    logger.debug('TAF FROM - ' + taf_time_from)
                    logger.debug(comp_time(taf_time_from))
                    logger.debug('TAF TO - ' + taf_time_to)
                    logger.debug(comp_time(taf_time_to))

                    #There can be multiple layers of clouds in each taf, but they are always listed lowest AGL first.
                    #Check the lowest (first) layer and see if it's overcast, broken, or obscured. If it is, then compare to cloud bas$
                    #This algorithm basically sets the flight category based on the lowest OVC, BKN or OVX layer.
                    for sky_condition in forecast.findall('sky_condition'): #for each sky_condition from the XML
                        sky_cvr = sky_condition.attrib['sky_cover'] #get the sky cover (BKN, OVC, SCT, etc)
                        logger.debug(sky_cvr)

                        if sky_cvr in ("OVC","BKN","OVX"): #If the layer is OVC, BKN or OVX, set Flight category based on height A$

                            try:
                                cld_base_ft_agl = sky_condition.attrib['cloud_base_ft_agl'] #get cloud base AGL from XML
                                logger.debug(cld_base_ft_agl) #debug
                            except:
                                cld_base_ft_agl = forecast.find('vert_vis_ft').text #get cloud base AGL from XML

#                            cld_base_ft_agl = sky_condition.attrib['cloud_base_ft_agl'] #get cloud base AGL from XML
#                            logger.debug(cld_base_ft_agl)

                            cld_base_ft_agl = int(cld_base_ft_agl)
                            if cld_base_ft_agl < 500:
                                flightcategory = "LIFR"
                                break

                            elif 500 <= cld_base_ft_agl < 1000:
                                flightcategory = "IFR"
                                break

                            elif 1000 <= cld_base_ft_agl <= 3000:
                                flightcategory = "MVFR"
                                break

                            elif cld_base_ft_agl > 3000:
                                flightcategory = "VFR"
                                break

                    #visibilty can also set flight category. If the clouds haven't set the fltcat to LIFR. See if visibility will
                    if flightcategory != "LIFR": #if it's LIFR due to cloud layer, no reason to check any other things that can set fl$
                        if forecast.find('visibility_statute_mi') is not None: #check XML if visibility value exists
                            visibility_statute_mi = forecast.find('visibility_statute_mi').text   #get visibility number
                            visibility_statute_mi = float(visibility_statute_mi)
                            print (visibility_statute_mi)

                            if visibility_statute_mi < 1.0:
                                flightcategory = "LIFR"

                            elif 1.0 <= visibility_statute_mi < 3.0:
                                flightcategory = "IFR"

                            elif 3.0 <= visibility_statute_mi <= 5.0 and flightcategory != "IFR":  #if Flight Category was already
                                flightcategory = "MVFR"

                    #Print out TAF data to screen for debugging only
                    logger.debug('Airport - ' + stationId)
                    logger.debug('Flight Category - ' + flightcategory)
                    logger.debug('Wind Speed - ' + taf_wind_speed_kt)
                    logger.debug('WX String - ' + taf_wx_string)
                    logger.debug('Change Indicator - ' + taf_change_indicator)
                    logger.debug('Wind Director Degrees - ' + taf_wind_dir_degrees)
                    logger.debug('Wind Gust - ' + taf_wind_gust_kt)

                    #grab flightcategory from returned FAA data
                    if flightcategory is None:  #if wind speed is blank, then bypass
                        flightcategory = None

                    #grab wind speeds from returned FAA data
                    if taf_wind_speed_kt is None: #if wind speed is blank, then bypass
                        windspeedkt = 0
                    else:
                        windspeedkt = int(taf_wind_speed_kt)

                    #grab wind gust from returned FAA data - Lance Blank
                    if taf_wind_gust_kt is None or taf_wind_gust_kt == '': #if wind speed is blank, then bypass
                        windgustkt = 0
                    else:
                        windgustkt = int(taf_wind_gust_kt)

                    #grab wind direction from returned FAA data
                    if taf_wind_dir_degrees is None: #if wind direction is blank, then bypass
                        winddirdegree = 0
                    else:
                        winddirdegree = int(taf_wind_dir_degrees)

                    #grab Weather info from returned FAA data
                    if taf_wx_string is None:   #if weather string is blank, then bypass
                        wxstring = "NONE"
                    else:
                        wxstring = taf_wx_string

            #Check for duplicate airport identifier and skip if found, otherwise store in dictionary. covers for dups in "airports" file
            if stationId in stationiddict:
                logger.info(stationId + " Duplicate, only saved first metar category")
            else:
                stationiddict[stationId] = flightcategory #build category dictionary

            if stationId in windsdict:
                logger.info(stationId + " Duplicate, only saved first metar category")
            else:
                windsdict[stationId] = windspeedkt #build windspeed dictionary

            if stationId in wnddirdict:
                logger.info(stationId + " Duplicate, only saved first metar category")
            else:
                wnddirdict[stationId] = winddirdegree #build wind direction dictionary

            if stationId in wxstringdict:
                logger.info(stationId + " Duplicate, only saved first metar category")
            else:
                wxstringdict[stationId] = wxstring #build weather dictionary

            if stationId in wndgustdict:        #Lance Blank
                logger.info(stationId + "Duplicate, only saved the first winds")
            else:
                wndgustdict[stationId] = windgustkt #build windgust dictionary

        logger.info("Decoded TAF Data for Display")


    elif metar_taf_mos == 1:                    #Decode METARs to display
        #grab the airport category, wind speed and various weather from the results given from FAA.
        #start of METAR decode routine if 'metar_taf' equals 1. Script will default to this routine without a rotary switch installed.
        for metar in root.iter('METAR'):
            stationId = metar.find('station_id').text

            #grab flight category from returned FAA data
            if metar.find('flight_category') is None: #if category is blank, then bypass
                flightcategory = "NONE"
            else:
                flightcategory = metar.find('flight_category').text

            #grab wind speeds from returned FAA data
            if metar.find('wind_speed_kt') is None: #if wind speed is blank, then bypass
                windspeedkt = 0
            else:
                windspeedkt = int(metar.find('wind_speed_kt').text)

            #grab wind gust from returned FAA data - Lance Blank
            if metar.find('wind_gust_kt') is None: #if wind speed is blank, then bypass
                windgustkt = 0
            else:
                windgustkt = int(metar.find('wind_gust_kt').text)

            #grab wind direction from returned FAA data
            if metar.find('wind_dir_degrees') is None or metar.find('wind_dir_degrees').text == 'VRB': #if wind speed is blank, then bypass
                winddirdegree = 0
            else:
                winddirdegree = int(metar.find('wind_dir_degrees').text)

            #grab Weather info from returned FAA data
            if metar.find('wx_string') is None: #if weather string is blank, then bypass
                wxstring = "NONE"
            else:
                wxstring = metar.find('wx_string').text

            #Check for duplicate airport identifier and skip if found, otherwise store in dictionary. covers for dups in "airports" file
            if stationId in stationiddict:
                logger.info(stationId + " Duplicate, only saved first metar category")
            else:
                stationiddict[stationId] = flightcategory #build category dictionary

            if stationId in windsdict:
                logger.info(stationId + " Duplicate, only saved first metar category")
            else:
                windsdict[stationId] = windspeedkt #build windspeed dictionary

            if stationId in wnddirdict:
                logger.info(stationId + " Duplicate, only saved first metar category")
            else:
                wnddirdict[stationId] = winddirdegree #build wind direction dictionary

            if stationId in wxstringdict:
                logger.info(stationId + " Duplicate, only saved first metar category")
            else:
                wxstringdict[stationId] = wxstring #build weather dictionary

            if stationId in wndgustdict:        #Lance - Thanks
                print ("Duplicate, only saved the first winds")
            else:
                wndgustdict[stationId] = windgustkt #build windgust dictionary

        logger.info("Decoded METAR Data for Display")


    #Grab the top X number of highwinds and put them in a sorted list from highest to lowest to display
    if exclusive_flag == 1:
        num2display = config.LED_COUNT          #Reset num2display to all the airports if we are using exclusive_list

    newwindsdict = dict(sorted(iter(windsdict.items()), key=operator.itemgetter(1), reverse=True)[:num2display])
    sortwindslist = sorted(list(newwindsdict.items()), key=operator.itemgetter(1))
    sortwindslist.reverse()

    if sortwindslist == []:
        sortwindslist = [(' ',0)]               #Used when Heat Map is selected

    if exclusive_flag == 1:                     #check if we should include an exclusive subset of airports to display
        logger.debug(sortwindslist)
        

        tmp1 = sorted(i for i in sortwindslist if i[0] in exclusive_list)
        if scrolldis != 2: # %%% disable sorting by winds if static display is used

            tmp1.sort(key=lambda tup: tup[1])       #sort by wind value
            tmp1.reverse()                          #Reverse so list is sorted highest to lowest

            if len(tmp1) < numofdisplays:           #Pad blanks if airports are less than numofdisplays
                blank = [('', '')] * (numofdisplays - len(tmp1))
                tmp1 = tmp1 + blank

        sortwindslist = tmp1                    #Reset sortwindslist to only those whose winds are higher than specified

    hiap, hiwind = sortwindslist[0]             #Get the highest wind speed airport identifier and its wind speed.

    if abovekts == 1:                           #check if we should only display airports whose winds are higher or equal to value in minwinds
        logger.debug(sortwindslist)

        tmp1 = sorted(i for i in sortwindslist if i[1] != '') #filter out blank screens that would throw an error when compared to minwinds
        logger.debug(tmp1)
        tmp1 = sorted(i for i in tmp1 if i[1] >= minwinds) #sortwindslist if i[1] >= minwinds)
        tmp1.sort(key=lambda tup: tup[1])       #sort by wind value
        tmp1.reverse()                          #Reverse so list is sorted highest to lowest

        if len(tmp1) <= 0:                      #If there are no airports with winds higher than set add comment to string
            if lcddisplay:                      #different comments depending on display used
                tmp1 = [("All Airports"," Lower Than " + str(minwinds))]
            else:
                tmp1 = [("Winds","Calm")]

        if len(tmp1) < numofdisplays:           #Pad blanks if airports are less than numofdisplays
            blank = [('','')] * (numofdisplays - len(tmp1))
            tmp1 = tmp1 + blank

        sortwindslist = tmp1                    #Reset sortwindslist to only those whose winds are higher than specified

    if blankscr:                                #Add a blank screen to separate the group of airports displayed
        sortwindslist.append(tuple(('','')))

    #Force the list to be at least as long as the number of displays.
    if len(sortwindslist) < numofdisplays:      #Pad blanks if airports are less than numofdisplays
        blank = [('','')] * (numofdisplays - len(sortwindslist))
        sortwindslist = sortwindslist + blank
    logger.debug(len(sortwindslist))
    logger.debug(sortwindslist)
    logger.info("Built Wind Dictionary")

    #See http://www.circuitbasics.com/raspberry-pi-lcd-set-up-and-programming-in-python/
    #Find the top windspeeds and airports and display to LCD if used. Written for a 16x2 display wired in 4 bit format.
    if lcddisplay:
        logger.info("LCD Display Being Used")
        #Bit maps for 8 special characters, Arrows, to display wind direction along with wind speed.
        #See https://rplcd.readthedocs.io/en/stable/usage.html#creating-custom-characters for more info on creating characters.
        swarrow = (
            0b00000,
            0b01111,
            0b00011,
            0b00101,
            0b01001,
            0b10000,
            0b00000,
            0b00000
        )

        nwarrow = (
            0b00000,
            0b00000,
            0b10000,
            0b01001,
            0b00101,
            0b00011,
            0b01111,
            0b00000
        )

        nearrow = (
            0b00000,
            0b00000,
            0b00001,
            0b10010,
            0b10100,
            0b11000,
            0b11110,
            0b00000
        )

        searrow = (
            0b00000,
            0b11110,
            0b11000,
            0b10100,
            0b10010,
            0b00001,
            0b00000,
            0b00000
        )

        northarrow = (
            0b00000,
            0b00100,
            0b00100,
            0b00100,
            0b10101,
            0b01110,
            0b00100,
            0b00000
        )

        eastarrow = (
            0b00000,
            0b00000,
            0b00100,
            0b01000,
            0b11111,
            0b01000,
            0b00100,
            0b00000
        )

        southarrow = (
            0b00000,
            0b00100,
            0b01110,
            0b10101,
            0b00100,
            0b00100,
            0b00100,
            0b00000
        )

        westarrow = (
            0b00000,
            0b00000,
            0b00100,
            0b00010,
            0b11111,
            0b00010,
            0b00100,
            0b00000
        )

        long_string = "Winds Updated " + dt_string + "--"

        #Build the instance of LCD. Be sure to include "compat_mode = True" to eliminate extraneous characters on the display.
        lcd = CharLCD(numbering_mode=GPIO.BCM, cols=16, rows=2, pin_rs=26, pin_e=19, pins_data=[13, 6, 5 ,11], compat_mode = True)
        lcd.clear()
        lcd.cursor_mode = 'hide'

        #Create special Characters using bitmaps above. See https://rplcd.readthedocs.io/en/stable/usage.html#creating-custom-characters
        lcd.create_char(0,swarrow)
        lcd.create_char(1,nwarrow)
        lcd.create_char(2,nearrow)
        lcd.create_char(3,searrow)
        lcd.create_char(4,northarrow)
        lcd.create_char(5,eastarrow)
        lcd.create_char(6,southarrow)
        lcd.create_char(7,westarrow)

        for ap,wnd in sortwindslist:            #airport and winds
            dir = wnddirdict.get(ap)            #get wind direction by airport
            arrowdir = winddir(dir)             #get proper proper arrow to display

            #Determine wind direction and assign proper arrow direction
            if arrowdir == 'd':                 #From North
                arrow = '\x04'
            elif arrowdir == 'f':               #From North East
                arrow = '\x02'
            elif arrowdir == 'b':               #From East
                arrow = '\x05'
            elif arrowdir == 'e':               #From South East
                arrow = '\x03'
            elif arrowdir == 'c':               #From South
                arrow = '\x06'
            elif arrowdir == 'g':               #From South West
                arrow = '\x00'
            elif arrowdir == 'a':               #From West
                arrow = '\x07'
            elif arrowdir == 'h':               #From North West
                arrow = '\x01'
            else:
                arrow = ''                      #No arrow returned

            if ap != '':                        #check to see if there is an airport to display
                long_string = long_string + ap + ":" + str(wnd) + "kts " + arrow + "  "

        logger.debug(long_string)

        if abovekts:                            #check to see if we should only display airports whose winds are higher than 'minwinds'
            framebuffer = [str(minwinds) + ' kts or Above','']
        else:
            framebuffer = [str(num2display) + ' Highest Winds','']

    #OLED Display
    if oledused:
        logger.info("OLED Displays Used")
        #Reference material; https://pillow.readthedocs.io/en/stable/reference
        #Initialize library.
        for j in range(numofdisplays):
            tca_select(j)                       #select display to write to
            disp.begin()

        disp.display()

        #Create blank image for drawing.
        width = disp.width
        height = disp.height
        image = Image.new('1', (width, height)) #Make sure to create image with mode '1' for 1-bit color.

        #Get drawing object to draw on image.
        draw = ImageDraw.Draw(image)

        #Load fonts. Install font package --> sudo apt-get install ttf-mscorefonts-installer
        #Also see; https://stackoverflow.com/questions/1970807/center-middle-align-text-with-pil for info
        #Arrows.ttf downloaded from https://www.1001fonts.com/arrows-font.html#styles
        boldfont = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf', fontsize, fontindex)
        regfont = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf', fontsize, fontindex)
        arrows = ImageFont.truetype('/usr/share/fonts/truetype/misc/Arrows.ttf', fontsize, fontindex)

        logger.info("Fonts Loaded")
        font = regfont                          #initialize font to start

        temp = 0                                #Used to toggle invert if set
        toggle = 0                              #Used to toggle invert between groups of airports. Leave set at 0

        if scrolldis != 2:
            #Add update message to beginning of list
            sortwindslist.insert(0,("Updated", dt_string))

            #Add type of data being displayed, METAR, TAF, MOS etc
            if metar_taf_mos == 1:                  #Displaying METAR data
                sortwindslist.insert(0,("METARs", "Displayed"))

            elif metar_taf_mos == 0:                #TAF hour_to_display
                if toggle_sw == 0:
                    sortwindslist.insert(0,(str(time_sw0) + " hr TAF", "Displayed"))
                if toggle_sw == 1:
                    sortwindslist.insert(0,(str(time_sw1) + " hr TAF", "Displayed"))
                if toggle_sw == 2:
                    sortwindslist.insert(0,(str(time_sw2) + " hr TAF", "Displayed"))
                if toggle_sw == 3:
                    sortwindslist.insert(0,(str(time_sw3) + " hr TAF", "Displayed"))
                if toggle_sw == 4:
                    sortwindslist.insert(0,(str(time_sw4) + " hr TAF", "Displayed"))
                if toggle_sw == 5:
                    sortwindslist.insert(0,(str(time_sw5) + " hr TAF", "Displayed"))
                if toggle_sw == 6:
                    sortwindslist.insert(0,(str(time_sw6) + " hr TAF", "Displayed"))
                if toggle_sw == 7:
                    sortwindslist.insert(0,(str(time_sw7) + " hr TAF", "Displayed"))
                if toggle_sw == 8:
                    sortwindslist.insert(0,(str(time_sw8) + " hr TAF", "Displayed"))
                if toggle_sw == 9:
                    sortwindslist.insert(0,(str(time_sw9) + " hr TAF", "Displayed"))
                if toggle_sw == 10:
                    sortwindslist.insert(0,(str(time_sw10) + " hr TAF", "Displayed"))
                if toggle_sw == 11:
                    sortwindslist.insert(0,(str(time_sw11) + " hr TAF", "Displayed"))
                if toggle_sw == 12:
                    sortwindslist.insert(0,(str(time_sw0) + " hr TAF", "Displayed"))

            elif metar_taf_mos == 2:                #MOS hour_to_display
                if toggle_sw == 0:
                    sortwindslist.insert(0,(str(time_sw0) + " hr MOS", "Displayed"))
                if toggle_sw == 1:
                    sortwindslist.insert(0,(str(time_sw1) + " hr MOS", "Displayed"))
                if toggle_sw == 2:
                    sortwindslist.insert(0,(str(time_sw2) + " hr MOS", "Displayed"))
                if toggle_sw == 3:
                    sortwindslist.insert(0,(str(time_sw3) + " hr MOS", "Displayed"))
                if toggle_sw == 4:
                    sortwindslist.insert(0,(str(time_sw4) + " hr MOS", "Displayed"))
                if toggle_sw == 5:
                    sortwindslist.insert(0,(str(time_sw5) + " hr MOS", "Displayed"))
                if toggle_sw == 6:
                    sortwindslist.insert(0,(str(time_sw6) + " hr MOS", "Displayed"))
                if toggle_sw == 7:
                    sortwindslist.insert(0,(str(time_sw7) + " hr MOS", "Displayed"))
                if toggle_sw == 8:
                    sortwindslist.insert(0,(str(time_sw8) + " hr MOS", "Displayed"))
                if toggle_sw == 9:
                    sortwindslist.insert(0,(str(time_sw9) + " hr MOS", "Displayed"))
                if toggle_sw == 10:
                    sortwindslist.insert(0,(str(time_sw10) + " hr MOS", "Displayed"))
                if toggle_sw == 11:
                    sortwindslist.insert(0,(str(time_sw11) + " hr MOS", "Displayed"))
                if toggle_sw == 12:
                    sortwindslist.insert(0,(str(time_sw0) + " hr MOS", "Displayed"))

        #Display welcome message via OLED displays if 'usewelcome = 1'
        if usewelcome and toggle_sw != -1:      #if toggle_sw == -1 then this script just started. Suppress welcome message for now
            logger.info("Use Welcome Enabled")

            if oledposorder == 0:
                startnum = 0                    #values are for oleds wired normally, pos 0 thru 7
                stopnum = numofdisplays
                stepnum = 1
            else:
                startnum = numofdisplays-1      #these values are for oleds wired backwards, pos 7 thru 0
                stopnum = -1
                stepnum = -1

            font = boldfont
            arrowdir = ''                       #No arrow needed
            j = 0

            welcomelist = list(welcome.split(" ")) #create a list to use to display a welcome message if desired
            if displayIP: #will display the RPI's local IP address along with welcome message if desired.
                splitIP = re.sub(r'^(.*?(\..*?){1})\.', r'\1\n.', str(s.getsockname()[0])) #split IP into 2 lines
                logger.debug(splitIP)
                welcomelist = welcomelist + [splitIP] #[splitIP] #split into 2 lines
#               welcomelist = welcomelist + [str(s.getsockname()[0])] #all on one line

            if len(welcomelist) < numofdisplays:
                pad = int((numofdisplays - len(welcomelist))/2)
                welcomelist = ([''] * pad) + welcomelist

            blanks = [''] * numofdisplays       #add blanks to end of message to clean display after message
            welcomelist = welcomelist + blanks

            if GPIO.input(4) == 1:              #Set dimming level
                dimming = 1                     #1 = full dim
            else:
                dimming = dimswitch             #Brightess setting. dimswitch can be 0,1 or 2. 1 is most dim, 2 medium dim.

            logger.debug(welcomelist)

            while j < len(welcomelist):
                for ch in range(startnum, stopnum, stepnum):
                    if j < len(welcomelist):
                        word = welcomelist[j]
                    else:
                        word = ''
                    oledcenter(word, ch, font, arrowdir, dimming, toggle, 0)

                    if numofdisplays == 1:
                        time.sleep(oledpause)
                    else:
                        time.sleep(oledpause/4)

                    j += 1

    #Loop through the airports and display the winds till its time to update the weather from the FAA
    #Setup timed loop for updating FAA Weather that will run based on the value of update_interval which is a user setting
    k = 0                                       #counter for displaying local time is desired.
    if toggle_sw  != -1:                        #check to see if this is the first time through and bypass if it is.
        if oledused:
            clearoleddisplays()

        if lcddisplay:
            lcd.clear()

    timeout_start = time.time()                 #When timer hits user-defined value, go back to outer loop to update FAA Weather.
    while time.time() < timeout_start + (update_interval * 60): #take "update_interval" which is in minutes and turn into seconds

        #If the rotary switch is in Heat Map Mode, display such on the displays.
        if metar_taf_mos == 3:
            if lcddisplay:
                lcd.clear()
                lcd.cursor_mode = 'hide'
                loop_string("Heat Map Mode", lcd, framebuffer, 1, 16, lcdpause)

            if oledused:                        #Display top AP Landings list on oleds
                arrowdir = ''
                dimming = 0
                toggle = 0
                j = 0
                ch = 0

                logger.debug(hmdata_sorted)

                while j < 10:
                    for ch in range(startnum, stopnum, stepnum): #numofdisplays-1, -1, -1):
                        if j == 0:
                            val = hmdata_sorted[j]
                        elif j > 10:
                            val = ''
                        else:
                            hmap, numland = hmdata_sorted[j]
                            val = hmap + "\n" + '#' + str(j)

                        oledcenter(val, ch, font, arrowdir, dimming, toggle, 0) #send airport and winds to proper oled display

                        j += 1

                        if numofdisplays == 1:
                            time.sleep(oledpause)
                        else:
                            time.sleep(oledpause/4)

        #Routine to restart this script if config.py is changed while this script is running.
        for f, mtime in WATCHED_FILES_MTIMES:
            if getmtime(f) != mtime:
                logger.info("Restarting from awake" + __file__ + " in 2 sec...")
                time.sleep(2)
                os.execv(sys.executable, [sys.executable] +  [__file__]) #'/NeoSectional/metar-display-v4.py'

        #Timer routine, used to turn off LED's at night if desired. Use 24 hour time in settings.
        if usetimer:                            #check to see if the user wants to use a timer.
            if time_in_range(timeoff, end_time, datetime.now().time()): #Part of Timer Fix - Thank You to Matthew G

                # If temporary lights-on period from refresh button has expired, restore the original light schedule
                #Part of Timer Fix
                if temp_lights_on == 1:
                    end_time = lights_on
                    timeoff = lights_out
                    temp_lights_on = 0

                logger.info("Display Going to Sleep")

                if lcddisplay:
                    lcd.clear()

                if oledused:
                    tmp1 = border
                    border = 0
                    clearoleddisplays()         #clear displays with no borders
                    border = tmp1

                while time_in_range(timeoff, end_time, datetime.now().time()): #Part of timer fix
#                    sys.stdout.write ("z")
#                    sys.stdout.flush ()

                    if sleepmsg == 1:                #Display "Sleeping" message on first oled if desired. 0 = No, 1 = Yes

                        rch = random.randint(0,numofdisplays-1)
                        oledcenter("Sleeping", rch, font, "", 1, toggle) #send airport and winds to proper oled display
                        time.sleep(2)
                        clearoleddisplays()

                    temp_timeoff = timeoff      #store original timeoff time and restore later.
                    time.sleep(1)

                    if GPIO.input(22) == False: #Pushbutton for Refresh. check to see if we should turn on temporarily during sleep mo$
                        # Set to turn lights on two seconds ago to make sure we hit the loop next time through - Part of Timer Fix
                        end_time = (datetime.now()-timedelta(seconds=2)).time()
                        timeoff = (datetime.now()+timedelta(minutes=tempsleepon)).time()
                        temp_lights_on = 1 #Set this to 1 if button is pressed
                        logger.info("Sleep interrupted by button push")

                    #Routine to restart this script if config.py is changed while this script is running.
                    for f, mtime in WATCHED_FILES_MTIMES:
                        if getmtime(f) != mtime:
                            logger.info("Restarting from sleep " + __file__ + " in 2 sec...")
                            time.sleep(2)
                            os.execv(sys.executable, [sys.executable] +  [__file__]) #'/NeoSectional/metar-display-v4.py'

#                    print ("\033[0;0m\n")       #Turn off Purple text.

        #Check if rotary switch is used, and what position it is in. This will determine what to display, METAR or TAF data.
        #If TAF data, what time offset should be displayed, i.e. 0 hour, 1 hour, 2 hour etc.
        #If there is no rotary switch installed, then all these tests will fail and will display the defaulted data from Switch Position 0
        if GPIO.input(0) == False and toggle_sw != 0:
            toggle_sw = 0
            hour_to_display = time_sw0          #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw0            #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 0. Breaking out of loop for METARs')
            break

        elif GPIO.input(5) == False and toggle_sw != 1:
            toggle_sw = 1
            hour_to_display = time_sw1          #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw1            #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 1. Breaking out of loop for TAF/MOS + ' + str(time_sw1) + " hour")
            break

        elif GPIO.input(6) == False and toggle_sw != 2:
            toggle_sw = 2
            hour_to_display = time_sw2          #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw2            #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 2. Breaking out of loop for TAF/MOS + ' + str(time_sw2) + " hours")
            break

        elif GPIO.input(13) == False and toggle_sw != 3:
            toggle_sw = 3
            hour_to_display = time_sw3          #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw3            #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 3. Breaking out of loop for TAF/MOS + ' + str(time_sw3) + " hours")
            break

        elif GPIO.input(19) == False and toggle_sw != 4:
            toggle_sw = 4
            hour_to_display = time_sw4          #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw4            #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 4. Breaking out of loop for TAF/MOS + ' + str(time_sw4) + " hours")
            break

        elif GPIO.input(26) == False and toggle_sw != 5:
            toggle_sw = 5
            hour_to_display = time_sw5          #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw5            #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 5. Breaking out of loop for TAF/MOS + ' + str(time_sw5) + " hours")
            break

        elif GPIO.input(21) == False and toggle_sw != 6:
            toggle_sw = 6
            hour_to_display = time_sw6          #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw6            #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 6. Breaking out of loop for TAF/MOS + ' + str(time_sw6) + " hours")
            break

        elif GPIO.input(20) == False and toggle_sw != 7:
            toggle_sw = 7
            hour_to_display = time_sw7          #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw7            #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 7. Breaking out of loop for TAF/MOS + ' + str(time_sw7) + " hours")
            break

        elif GPIO.input(16) == False and toggle_sw != 8:
            toggle_sw = 8
            hour_to_display = time_sw8          #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw8            #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 8. Breaking out of loop for TAF/MOS + ' + str(time_sw8) + " hours")
            break

        elif GPIO.input(12) == False and toggle_sw != 9:
            toggle_sw = 9
            hour_to_display = time_sw9          #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw9            #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 9. Breaking out of loop for TAF/MOS + ' + str(time_sw9) + " hours")
            break

        elif GPIO.input(1) == False and toggle_sw != 10:
            toggle_sw = 10
            hour_to_display = time_sw10         #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw10           #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 10. Breaking out of loop for TAF/MOS + ' + str(time_sw10) + " hours")
            break

        elif GPIO.input(7) == False and toggle_sw != 11:
            toggle_sw = 11
            hour_to_display = time_sw11         #Offset in HOURS to choose which TAF/MOS to display. Not used with Metars/Heat Map
            metar_taf_mos = data_sw11           #0 = Display TAF. 1 = Display METAR. 2 = MOS. 3 = Heat Map
            logger.info('Switch in position 11. Breaking out of loop for TAF/MOS + ' + str(time_sw11) + " hours")
            break

        elif toggle_sw == -1:                   #Used if no Rotary Switch is installed
            toggle_sw = 12                      #12 designates that no Rotary Switch is installed
            hour_to_display = time_sw0          #Value set above in default position 0
            metar_taf_mos = data_sw0            #Value set above in default position 0
            logger.info('Rotary Switch Not Installed. Using Switch Position 0 as Default')
            break

        #Check to see if pushbutton is pressed to force an update of FAA Weather
        #If no button is connected, then this is bypassed and will only update when 'update_interval' is met
        if GPIO.input(22) == False:
            logger.info('Breaking out of loop to refresh FAA Data')
            break

        #Bright light will provide a low state (0) on GPIO. Dark light will provide a high state (1).
        #Full brightness will be used if no light sensor is installed. IC238 Light Sensor.
        if GPIO.input(4) == 1:
            dimming = 1                         #1 = full dim
        else:
            dimming = dimswitch                 #Brightess setting. dimswitch can be 0,1 or 2. 1 is most dim, 2 medium dim.

        if lcddisplay:
            print ("Display on a LCD display")

            #Below creates a scrolling effect of the X highest winds, updated every 15 minutes (update_interval)
            lcd.clear()
            lcd.cursor_mode = 'hide'
            loop_string(long_string, lcd, framebuffer, 1, 16, lcdpause)

        #Display information via OLED
        if oledused and metar_taf_mos != 3 and toggle_sw != -1:
            logger.debug("Display on a OLED display") #debug

            if temp == len(sortwindslist)-1:    #Check to see if display should be inverted after each group of airports
                if toginv:
                    toggle = not(toggle)
                temp = 0
            else:
                temp += 1

            if invert:                          #If invert is set to 1 then display black text on white background
                toggle = 1

            for ch in range(startnum, stopnum, stepnum):    #numofdisplays-1, -1, -1):
                ap,wnd = sortwindslist[ch]      #Grab airport and its winds to display
                dir = wnddirdict.get(ap)        #get wind direction by airport
                gust = wndgustdict.get(ap)      #get wind gust by airport - Mez

                if dir is None:
                    dir = 361

                logger.debug(str(ch) + ' ' + str(ap) + ' ' + str(dir) + ' ' + str(wnd) + ' ' + str(gust) + ' ' + str(dir)) #debug

                val = ap + "\n" + str(wnd)      #Provide a starting value that will get modified by oledcenter function

                if ap == hiap and boldhiap:     #Highlight the airport with the highest winds in bold text.
                    font = boldfont
                else:
                    font = regfont

                oledcenter(val, ch, font, dir, dimming, toggle, 0) #send airport and winds to proper oled display

            # %%%  shift list 1 position then redisplay. Creates scrolling effect.
            if scrolldis == 1:                  #Determine if display should scroll right=1 or left=0
                sortwindslist = (sortwindslist[-1:] + sortwindslist[:-1]) #From; https://www.geeksforgeeks.org/python-program-right-rotate-list-n/
            if scrolldis == 0:
                sortwindslist = (sortwindslist[1:] + sortwindslist[:1])
            else:
                pass                            # If any other value other than 1 or 0 then don't scroll.

            time.sleep(oledpause)               #pause between scroll effect

            if k == len(sortwindslist)-1 and displaytime: #Display current and zulu time if displaytime = 1
                now = datetime.now()
                zulu = datetime.utcnow()
                localtime = now.strftime("%I:%M %p\n Local") #12:00 PM format
                zulutime = zulu.strftime("%H:%M\n Zulu") #12:00 PM format

                pos = int((numofdisplays-3)/2)  #Calculate position to display the time. Needs 3 screens minimum.

                logger.debug(localtime)         #debug
                logger.debug(zulutime)          #debug

                arrowdir = ''                   #No Arrow needed
                clearoleddisplays()             #clear displays

                if numofdisplays % 2 == 0:      #Check if we have a odd or even num of displays
                    pass
                else:
                    oledcenter('Current\nTime', pos, font, arrowdir, dimming, toggle) #send Current Time to proper oled display

                    if numofdisplays < 2:       #Check to see if there is only 1 oled and pause between screens if there is.
                        time.sleep(oledpause)

                oledcenter(localtime, pos+1, font, arrowdir, dimming, toggle) #send Local Time to proper oled display
                if numofdisplays < 2:           #Check to see if there is only 1 oled and pause between screens if there is.
                    time.sleep(oledpause)

                oledcenter(zulutime, pos+2, font, arrowdir, dimming, toggle) #send Zulu Time to proper oled display

                k = 0

                if numofdisplays < 2:
                    time.sleep(oledpause)
                else:
                    time.sleep(oledpause*2) #long pause
            else:
                k = k + 1
