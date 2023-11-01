#!/usr/bin/python3
#metar-v4.py - by Mark Harris. Capable of displaying METAR data, TAF or MOS data. Using a rotary switch to select 1 of 12 positions
#    Updated to work with New FAA API: 10-2023. Thank you to user Marty for all the hardwork.
#    Updated to run under Python 3.7
#    Added Sleep Timer routine to turn-off map at night if desired.
#    Added the ability to display TAF or MOS data along with METAR's
#    Note: MOS data is only available for United States, Puerto Rico, and the U.S. Virgin Islands.
#    The timeframe of the TAF, MOS data to display can be selected via the rotary switch. A switch with up to 12 positions can be used.
#    If no Rotary Switch is used, this script's config will set default data to display.
#    Added routine by by Nick Cirincione to decode flight category if flight category is not provided by the FAA.
#    Fixed bug that wouldn't allow the last airport to be 'NULL' without causing all LED's to show white.
#    Added auto restart when config.py is changed, so settings will be automatically re-loaded.
#    Added internet availability check and retry if necessary. This should help when power is disrupted and board reboots before router does.
#    Added Logging capabilities which is stored in /NeoSectional/logfile.log with 3 backup files for older logfile data.
#    Added ability to specify specific LED pins to reverse the normal rgb_grb setting. For mixing models of LED strings.
#    Added a Heat Map of what airports the user has landed at. Not available through Rotary switch. Only Web interface.
#    Added new wipes, some based on lat/lon of airports
#    Fixed bug where wipes would execute twice on map startup.
#    Added admin.py for behinds the scenes variables to be stored. i.e. use_mos=1 to determine if bash files should or should not download MOS data.
#    Added ability to detect a Rotary Switch is NOT installed and react accordingly.
#    Added logging of Current RPI IP address whenever FAA weather update is retrieved
#    Fixed bug where TAF XML reports OVC without a cloud level agl. It uses vert_vis_ft as a backup.
#    Fixed bug when debug mode is changed to 'Debug'.
#    Switch Version control over to Github at https://github.com/markyharris/livesectional
#    Fixed METAR Decode routine to handle FAA results that don't include flight_category and forecast fields.
#    Added routine to check time and reboot each night if setting in admin.py are set accordingly.
#    Fixed bug that missed lowest sky_condition altitude on METARs not reporting flight categories.
#    Thank you Daniel from pilotmap.co for the change the routine that handles maps with more than 300 airports.

#This version retains the features included in metar-v3.py, including hi-wind blinking and lightning when thunderstorms are reported.
#However, this version adds representations for snow, rain, freezing rain, dust sand ash, and fog when reported in the metar.
#The LED's will show the appropriate color for the reported flight category (vfr, mvfr, ifr, lifr) then blink a specific color for the weather
#For instance, an airport reporting IFR with snow would display Red then blink white for a short period to denote snow. Blue for rain,
#purple for freezing rain, brown for dust sand ash, and silver for fog. This makes for a colorful map when weather is in the area.
#A home airport feature has been added as well. When enabled, the map can be dimmed in relation to the home airport as well as
#have the home alternate between weather color and a user defined marker color(s).
#Most of these features can be disabled to downgrade the map display in the user-defined variables below.

#For detailed instructions on building an Aviation Map, visit http://www.livesectional.com
#Hardware features are further explained on this site as well. However, this software allows for a power-on/update weather switch,
#and Power-off/Reboot switch. The use of a display is handled by metar-display.py and not this script.

#Flight Category Definitions. (https://aviationweather-cprk.ncep.noaa.gov/taf/help?page=plot)
#+--------------------------------------+---------------+-------------------------------+-------+----------------------------+
#|Category                              |Color          |Ceiling                        |       |Visibility                  |
#|--------------------------------------+---------------+-------------------------------+-------+----------------------------+
#|VFR   Visual Flight Rules             |Green          |greater than 3,000 feet AGL    |and    |greater than 5 miles        |
#|MVFR  Marginal Visual Flight Rules    |Blue           |1,000 to 3,000 feet AGL        |and/or |3 to 5 miles                |
#|IFR   Instrument Flight Rules         |Red            |500 to below 1,000 feet AGL    |and/or |1 mile to less than 3 miles |
#|LIFR  Low Instrument Flight Rules     |Magenta        |       below 500 feet AGL      |and-or |less than 1 mile            |
#+--------------------------------------+---------------+-------------------------------+-------+----------------------------+
#AGL = Above Ground Level

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
import urllib.request, urllib.error, urllib.parse
import socket
import xml.etree.ElementTree as ET
import time
from datetime import datetime
from datetime import timedelta
from datetime import time as time_
from rpi_ws281x import * #works with python 3.7. sudo pip3 install rpi_ws281x
import sys
import os
from os.path import getmtime
import RPi.GPIO as GPIO
import collections
import re
import logging
import logzero #had to manually install logzero. https://logzero.readthedocs.io/en/latest/
from logzero import logger
import config #Config.py holds user settings used by the various scripts
import admin

# Setup rotating logfile with 3 rotations, each with a maximum filesize of 1MB:
version = admin.version                 #Software version
loglevel = 1#config.loglevel
loglevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
logzero.loglevel(loglevels[loglevel])   #Choices in order; DEBUG, INFO, WARNING, ERROR
logzero.logfile("/NeoSectional/logfile.log", maxBytes=1e6, backupCount=3)
logger.info("\n\nStartup of metar-v4.py Script, Version " + version)
logger.info("Log Level Set To: " + str(loglevels[loglevel]))

#****************************************************************************
#* User defined items to be set below - Make changes to config.py, not here *
#****************************************************************************

#list of pins that need to reverse the rgb_grb setting. To accommodate two different models of LED's are used.
rev_rgb_grb = config.rev_rgb_grb        #[] #['1', '2', '3', '4', '5', '6', '7', '8']

#Specific Variables to default data to display if Rotary Switch is not installed.
hour_to_display = config.time_sw0       #hour_to_display #Offset in HOURS to choose which TAF/MOS to display
metar_taf_mos = config.data_sw0         #metar_taf_mos    #0 = Display TAF, 1 = Display METAR, 2 = Display MOS, 3 = Heat Map (Heat map not controlled by rotary switch)
toggle_sw = -1                          #Set toggle_sw to an initial value that forces rotary switch to dictate data displayed

#MOS/TAF Config settings
prob = config.prob                      #probability threshhold in Percent to assume reported weather will be displayed on map or not. MOS Only.

data_sw0 = config.data_sw0              #User selectable source of data on Rotary Switch position 0. 0 = TAF, 1 = METAR, 2 = MOS
data_sw1 = config.data_sw1              #User selectable source of data on Rotary Switch position 1. 0 = TAF, 1 = METAR, 2 = MOS
data_sw2 = config.data_sw2              #User selectable source of data on Rotary Switch position 2. 0 = TAF, 1 = METAR, 2 = MOS
data_sw3 = config.data_sw3              #User selectable source of data on Rotary Switch position 3. 0 = TAF, 1 = METAR, 2 = MOS
data_sw4 = config.data_sw4              #User selectable source of data on Rotary Switch position 4. 0 = TAF, 1 = METAR, 2 = MOS
data_sw5 = config.data_sw5              #User selectable source of data on Rotary Switch position 5. 0 = TAF, 1 = METAR, 2 = MOS
data_sw6 = config.data_sw6              #User selectable source of data on Rotary Switch position 6. 0 = TAF, 1 = METAR, 2 = MOS
data_sw7 = config.data_sw7              #User selectable source of data on Rotary Switch position 7. 0 = TAF, 1 = METAR, 2 = MOS
data_sw8 = config.data_sw8              #User selectable source of data on Rotary Switch position 8. 0 = TAF, 1 = METAR, 2 = MOS
data_sw9 = config.data_sw9              #User selectable source of data on Rotary Switch position 9. 0 = TAF, 1 = METAR, 2 = MOS
data_sw10 = config.data_sw10            #User selectable source of data on Rotary Switch position 10. 0 = TAF, 1 = METAR, 2 = MOS
data_sw11 = config.data_sw11            #User selectable source of data on Rotary Switch position 11. 0 = TAF, 1 = METAR, 2 = MOS

time_sw0 = config.time_sw0              #0 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw1 = config.time_sw1              #1 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw2 = config.time_sw2              #2 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw3 = config.time_sw3              #3 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw4 = config.time_sw4              #4 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw5 = config.time_sw5              #5 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw6 = config.time_sw6              #6 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw7 = config.time_sw7              #7 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw8 = config.time_sw8              #8 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw9 = config.time_sw9              #9 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw10 = config.time_sw10            #10 = number of hours ahead to display. Time equals time period of TAF/MOS to display.
time_sw11 = config.time_sw11            #11 = number of hours ahead to display. Time equals time period of TAF/MOS to display.

#Heat Map settings
bin_grad = config.bin_grad              #0 = Binary display, 1 = Gradient display
fade_yesno = config.fade_yesno          #0 = No, 1 = Yes, if using gradient display, fade in/out the home airport color. will override use_homeap.
use_homeap = config.use_homeap          #0 = No, 1 = Yes, Use a separate color to denote home airport.
fade_delay = config.fade_delay          #delay in fading the home airport if used

#MOS Config settings
prob = config.prob                      #probability threshhold in Percent to assume reported weather will be displayed on map or not.

#Specific settings for on/off timer. Used to turn off LED's at night if desired.
#Verify Raspberry Pi is set to the correct time zone, otherwise the timer will be off.
usetimer = config.usetimer              #0 = No, 1 = Yes. Turn the timer on or off with this setting
offhour = config.offhour                #Use 24 hour time. Set hour to turn off display
offminutes = config.offminutes          #Set minutes to turn off display
onhour = config.onhour                  #Use 24 hour time. Set hour to turn on display
onminutes = config.onminutes            #Set minutes to on display
tempsleepon = config.tempsleepon        #Set number of MINUTES to turn map on temporarily during sleep mode

LED_COUNT = config.LED_COUNT            #Number of LED pixels. Change this value to match the number of LED's being used on map

hiwindblink = config.hiwindblink        #1 = Yes, 0 = No. Blink the LED for high wind Airports.
lghtnflash = config.lghtnflash          #1 = Yes, 0 = No. Flash the LED for an airport reporting severe weather like TSRA.
rainshow = config.rainshow              #1 = Yes, 0 = No. Change colors to denote rain reported.
frrainshow = config.frrainshow          #1 = Yes, 0 = No. Change colors to denote freezing rain reported.
snowshow = config.snowshow              #1 = Yes, 0 = No. Change colors to denote snow reported.
dustsandashshow = config.dustsandashshow        #1 = Yes, 0 = No. Change colors to denote dust, sand, or ash reported.
fogshow = config.fogshow                #1 = Yes, 0 = No. Change colors to denote fog reported.
homeport = config.homeport              #1 = Yes, 0 = No. Turn on/off home airport feature. The home airport will use a marker color on every other pass

# if 'homeport = 1' be sure to set these variables appropriately
homeport_pin = config.homeport_pin      #Pin number of the home airport to display a marker color every other pass
homeport_display = config.homeport_display      #2 = no color change, 1 = changing colors - user defined below by homeport_colors[], 0 = Solid color denoted by homeport_color below.
dim_value = config.dim_value            #Percentage of brightness to dim all other airports if homeport is being used. 0 = No dimming. 100 = completely off

# Misc settings
usewipes = config.usewipes              #0 = No, 1 = Yes, use wipes. Defined by configurator
rgb_grb = config.rgb_grb                #1 = RGB color codes. 0 = GRB color codes. Populate color codes below with normal RGB codes and script will change if necessary
max_wind_speed = config.max_wind_speed  #In Knots. Any speed at or above will flash the LED for the appropriate airport if hiwindblink=1
update_interval = config.update_interval        #Number of MINUTES between FAA updates - 15 minutes is a good compromise. A pushbutton switch can be used to force update.
dimmed_value = config.dimmed_value      #Range is 0 - 255. This sets the value of LED brightness when light sensor detects low ambient light. Independent of homeport dimming.
bright_value = config.bright_value      #Range is 0 - 255. This sets the value of LED brightness when light sensor detects high ambient light
metar_age = config.metar_age            #Metar Age in HOURS. This will pull the latest metar that has been published within the timeframe listed here.
                                        #If no Metar has been published within this timeframe, the LED will default to the color specified by color_nowx.
use_reboot = admin.use_reboot           # Used to determine if board should reboot every day at time set in setting below.
time_reboot = admin.time_reboot         # 24 hour time in this format, '2400' = midnight. Change these 2 settings in the admin.py file if desired.
autorun = config.autorun                # Check to be sure Autorun on reboot is set to yes.

# Set Colors in RGB. Change numbers in paranthesis as desired. The order should be (Red,Green,Blue). This setup works for the WS2812 model of LED strips.
# WS2811 strips uses GRB colors, so change "rgb_grb = 0" above if necessary. Range is 0-255. (https://www.rapidtables.com/web/color/RGB_Color.html)
color_vfr = config.color_vfr            #Full bright Green for VFR
color_mvfr = config.color_mvfr          #Full bright Blue for MVFR
color_ifr = config.color_ifr            #Full bright Red for IFR
color_lifr = config.color_lifr          #Full bright Magenta for LIFR
color_nowx = config.color_nowx          #No weather for NO WX
color_black = config.color_black        #Black/Off
color_lghtn = config.color_lghtn        #Full bright Yellow to represent lightning strikes
color_snow1 = config.color_snow1        #White for Snow etc.
color_snow2 = config.color_snow2        #Grey for Snow etc.
color_rain1 = config.color_rain1        #Dark Blue for Rain etc.
color_rain2 = config.color_rain2        #Blue for rain etc.
color_frrain1 = config.color_frrain1    #Light Purple
color_frrain2 = config.color_frrain2    #Purple for freezing rain etc.
color_dustsandash1 = config.color_dustsandash1  #Tan/Brown for Dust and Sand
color_dustsandash2 = config.color_dustsandash2  #Dark Brown for Dust and Sand
color_fog1 = config.color_fog1          #Silver for Fog
color_fog2 = config.color_fog2          #Silver for Fog
color_homeport = config.color_homeport  #Color to denote home airport every other LED cycle. Used if 'homeport_display = 0'
homeport_colors = config.homeport_colors        #if 'homeport_display=1'. Change these colors as desired.

# Legend on/off. The setting 'legend' must be set to 1 for any legend LED's to be enabled. But you can disable the other
# legend types by defining it with a 0. No legend LED's, 5 basic legends LED's, 6, 7, 8, 9, 10, 11 or 12 total legend LED's can be used.
legend = config.legend                  #1 = Yes, 0 = No. Provides for basic vfr, mvfr, ifr, lifr, nowx legend. If 'legend=0' then no legends will be enabled.
legend_hiwinds = config.legend_hiwinds  #1 = Yes, 0 = No. With this enabled high winds legend will be displayed.
legend_lghtn = config.legend_lghtn      #1 = Yes, 0 = No. With this enabled Lightning/Thunderstorm legend will be displayed as well
legend_snow = config.legend_snow        #1 = Yes, 0 = No. Snow legend
legend_rain = config.legend_rain        #1 = Yes, 0 = No. Rain legend
legend_frrain = config.legend_frrain    #1 = Yes, 0 = No. Freezing Rain legend
legend_dustsandash = config.legend_dustsandash  #1 = Yes, 0 = No. Dust, Sand and/or Ash legend
legend_fog = config.legend_fog          #1 = Yes, 0 = No. Fog legend

# Legend Pins assigned if used. Be sure that the 'airports' file has 'LGND' at these LED positions otherwise the legend will not display properly.
leg_pin_vfr = config.leg_pin_vfr        #Set LED pin number for VFR Legend LED
leg_pin_mvfr = config.leg_pin_mvfr      #Set LED pin number for MVFR Legend LED
leg_pin_ifr = config.leg_pin_ifr        #Set LED pin number for IFR Legend LED
leg_pin_lifr = config.leg_pin_lifr      #Set LED pin number for LIFR Legend LED
leg_pin_nowx = config.leg_pin_nowx      #Set LED pin number for No Weather Legend LED
leg_pin_hiwinds = config.leg_pin_hiwinds        #Set LED pin number for High Winds Legend LED
leg_pin_lghtn = config.leg_pin_lghtn    #Set LED pin number for Thunderstorms Legend LED
leg_pin_snow = config.leg_pin_snow      #Set LED pin number for Snow Legend LED
leg_pin_rain = config.leg_pin_rain      #Set LED pin number for Rain Legend LED
leg_pin_frrain = config.leg_pin_frrain  #Set LED pin number for Freezing Rain Legend LED
leg_pin_dustsandash = config.leg_pin_dustsandash #Set LED pin number for Dust/Sand/Ash Legend LED
leg_pin_fog = config.leg_pin_fog        #Set LED pin number for Fog Legend LED

#************************************************************
#* End of User defined settings. Normally shouldn't change  *
#* any thing under here unless you are confident in change. *
#************************************************************

turnoffrefresh = 1                      #0 = do not turn refresh off, 1 = turn off the blanking refresh of the LED string between FAA updates.

#LED Cycle times - Can change if necessary.
cycle0_wait = .9        #These cycle times all added together will equal the total amount of time the LED takes to finish displaying one cycle.
cycle1_wait = .9        #Each  cycle, depending on flight category, winds and weather reported will have various colors assigned.
cycle2_wait = .08       #For instance, VFR with 20 kts winds will have the first 3 cycles assigned Green and the last 3 Black for blink effect.
cycle3_wait = .1        #The cycle times then reflect how long each color cycle will stay on, producing blinking or flashing effects.
cycle4_wait = .08       #Lightning effect uses the short intervals at cycle 2 and cycle 4 to create the quick flash. So be careful if you change them.
cycle5_wait = .5

#List of METAR weather categories to designate weather in area. Many Metars will report multiple conditions, i.e. '-RA BR'.
#The code pulls the first/main weather reported to compare against the lists below. In this example it uses the '-RA' and ignores the 'BR'.
#See https://aviationweather-cprk.ncep.noaa.gov/metar/symbol for descriptions. Add or subtract codes as desired.
#Thunderstorm and lightning
wx_lghtn_ck = ["TS", "TSRA", "TSGR", "+TSRA", "TSRG", "FC", "SQ", "VCTS", "VCTSRA", "VCTSDZ", "LTG"]
#Snow in various forms
wx_snow_ck = ["BLSN", "DRSN", "-RASN", "RASN", "+RASN", "-SN", "SN", "+SN", "SG", "IC", "PE", "PL", "-SHRASN", "SHRASN", "+SHRASN", "-SHSN", "SHSN", "+SHSN"]
#Rain in various forms
wx_rain_ck = ["-DZ", "DZ", "+DZ", "-DZRA", "DZRA", "-RA", "RA", "+RA", "-SHRA", "SHRA", "+SHRA", "VIRGA", "VCSH"]
#Freezing Rain
wx_frrain_ck = ["-FZDZ", "FZDZ", "+FZDZ", "-FZRA", "FZRA", "+FZRA"]
#Dust Sand and/or Ash
wx_dustsandash_ck = ["DU", "SA", "HZ", "FU", "VA", "BLDU", "BLSA", "PO", "VCSS", "SS", "+SS",]
#Fog
wx_fog_ck = ["BR", "MIFG", "VCFG", "BCFG", "PRFG", "FG", "FZFG"]

#list definitions
cycle_wait = [cycle0_wait, cycle1_wait, cycle2_wait, cycle3_wait, cycle4_wait, cycle5_wait] #Used to create weather designation effects.
cycles = [0,1,2,3,4,5] #Used as a index for the cycle loop.
legend_pins = [leg_pin_vfr, leg_pin_mvfr, leg_pin_ifr, leg_pin_lifr, leg_pin_nowx, leg_pin_hiwinds, leg_pin_lghtn, leg_pin_snow, leg_pin_rain, leg_pin_frrain, leg_pin_dustsandash, leg_pin_fog] #Used to build legend display

#Setup for IC238 Light Sensor for LED Dimming, does not need to be commented out if sensor is not used, map will remain at full brightness.
#For more info on the sensor visit; http://www.uugear.com/portfolio/using-light-sensor-module-with-raspberry-pi/
GPIO.setmode(GPIO.BCM)  #set mode to BCM and use BCM pin numbering, rather than BOARD pin numbering.
GPIO.setup(4, GPIO.IN)  #set pin 4 as input for light sensor, if one is used. If no sensor used board remains at high brightness always.
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 22 to momentary push button to force FAA Weather Data update if button is used.

#Setup GPIO pins for rotary switch to choose between Metars, or Tafs and which hour of TAF
#Not all the pins are required to be used. If only METARS are desired, then no Rotary Switch is needed.
GPIO.setup(0, GPIO.IN, pull_up_down=GPIO.PUD_UP)        #set pin 0 to ground for METARS
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_UP)        #set pin 5 to ground for TAF + 1 hour
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_UP)        #set pin 6 to ground for TAF + 2 hours
GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_UP)       #set pin 13 to ground for TAF + 3 hours
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP)       #set pin 19 to ground for TAF + 4 hours
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)       #set pin 26 to ground for TAF + 5 hours
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)       #set pin 21 to ground for TAF + 6 hours
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)       #set pin 20 to ground for TAF + 7 hours
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_UP)       #set pin 16 to ground for TAF + 8 hours
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_UP)       #set pin 12 to ground for TAF + 9 hours
GPIO.setup(1, GPIO.IN, pull_up_down=GPIO.PUD_UP)        #set pin 1 to ground for TAF + 10 hours
GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_UP)        #set pin 7 to ground for TAF + 11 hours

#LED strip configuration:
LED_PIN        = 18                     #GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000                 #LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5                      #DMA channel to use for generating signal (try 5)
LED_INVERT     = False                  #True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0                      #set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB    #Strip type and color ordering
LED_BRIGHTNESS = bright_value           #255    #starting brightness. It will be changed below.

#Setup paths for restart on change routine. Routine from;
#https://blog.petrzemek.net/2014/03/23/restarting-a-python-script-within-itself
LOCAL_CONFIG_FILE_PATH = '/NeoSectional/config.py'
WATCHED_FILES = [LOCAL_CONFIG_FILE_PATH, __file__]
WATCHED_FILES_MTIMES = [(f, getmtime(f)) for f in WATCHED_FILES]
logger.info('Watching ' + LOCAL_CONFIG_FILE_PATH + ' For Change')

#Timer calculations
now = datetime.now()                    #Get current time and compare to timer setting
lights_out = time_(offhour, offminutes, 0)
timeoff = lights_out
lights_on = time_(onhour, onminutes, 0)
end_time = lights_on
delay_time = 10                         #Number of seconds to delay before retrying to connect to the internet.
temp_lights_on = 0                      #Set flag for next round if sleep timer is interrupted by button push.

#MOS Data Settings
mos_filepath = '/NeoSectional/GFSMAV'      #location of the downloaded local MOS file.
categories = ['HR', 'CLD', 'WDR', 'WSP', 'P06', 'T06', 'POZ', 'POS', 'TYP', 'CIG','VIS','OBV']
obv_wx = {'N': 'None', 'HZ': 'HZ','BR': 'RA','FG': 'FG','BL': 'HZ'} #Decode from MOS to TAF/METAR
typ_wx = {'S': 'SN','Z': 'FZRA','R': 'RA'}      #Decode from MOS to TAF/METAR
mos_dict = collections.OrderedDict()    #Outer Dictionary, keyed by airport ID
hour_dict = collections.OrderedDict()   #Middle Dictionary, keyed by hour of forcast. Will contain a list of data for categories.
ap_flag = 0                             #Used to determine that an airport from our airports file is currently being read.

#Used by Heat Map. Do not change - assumed by routines below.
low_visits = (0, 0, 255)                #Start with Blue - Do Not Change
high_visits = (255, 0, 0)               #Increment to Red as visits get closer to 100 - Do Not Change
fadehome = -1                           #start with neg number
homeap = color_vfr                      #If 100, then home airport - designate with Green
no_visits = (20, 20, 20)        #color_fog2                     #(10, 10, 10)        #dk grey to denote airports never visited
black = color_black                     #(0,0,0)

# Misc Settings
ambient_toggle = 0                      # Toggle used for logging when ambient sensor changes from bright to dim.

logger.info("metar-v4.py Settings Loaded")

#Create an instance of NeoPixel
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
strip.begin()


# Functions
def turnoff(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0,0,0))
    strip.show()

#Reduces the brightness of the colors for every airport except for the "homeport_pin" designated airport, which remains at the brightness set by
#"bright_value" above in user setting. "data" is the airport color to display and "value" is the percentage of the brightness to be dimmed.
#For instance if full bright white (255,255,255) is provided and the desired dimming is 50%, then the color returned will be (128,128,128),
#or half as bright. The dim_value is set in the user defined area.
def dim(data,value):
    red = data[0] - ((value * data[0])/100)
    if red < 0:
        red = 0

    grn = data[1] - ((value * data[1])/100)
    if grn < 0:
        grn = 0

    blu = data[2] - ((value * data[2])/100)
    if blu < 0:
        blu = 0

    data =[red,grn,blu]
    return data

#Change color code to work with various led strips. For instance, WS2812 model strip uses RGB where WS2811 model uses GRB
#Set the "rgb_grb" user setting above. 1 for RGB LED strip, and 0 for GRB strip.
#If necessary, populate the list rev_rgb_grb with pin numbers of LED's that use the opposite color scheme.
def rgbtogrb(pin, data, order=0):
    global rev_rgb_grb #list of pins that need to use the reverse of the normal order setting.
    if str(pin) in rev_rgb_grb: #This accommodates the use of both models of LED strings on one map.
        order = not order
        logger.debug('Reversing rgb2grb Routine Output for PIN ' + str(pin))

    red = data[0]
    grn = data[1]
    blu = data[2]

    if order:
        data = [red,grn,blu]
    else:
        data =[grn,red,blu]
    return data

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

# See if a time falls within a range
def time_in_range(start, end, x):
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end

#Used by MOS decode routine. This routine builds mos_dict nested with hours_dict
def set_data():
    global hour_dict
    global mos_dict
    global dat0, dat1, dat2, dat3, dat4, dat5, dat6, dat7
    global apid
    global temp
    global keys

    #Clean up line of MOS data.
    if len(temp) >= 0: #this check is unneeded. Put here to vary length of list to clean up.
        temp1 = []
        tmp_sw = 0

        for val in temp: #Check each item in the list
            val = val.lstrip() #remove leading white space
            val = val.rstrip('/') #remove trailing /

            if len(val) == 6: #this is for T06 to build appropriate length list
                temp1.append('0') #add a '0' to the front of the list. T06 doesn't report data in first 3 hours.
                temp1.append(val) #add back the original value taken from T06
                tmp_sw = 1 #Turn on switch so we don't go through it again.

            elif len(val) > 2 and tmp_sw == 0: # and tmp_sw == 0: #if item is 1 or 2 chars long, then bypass. Otherwise fix.
                pos = val.find('100') #locate first 100
                tmp = val[0:pos] #capture the first value which is not a 100
                temp1.append(tmp) #and store it in temp list.

                k = 0
                for j in range(pos, len(val), 3): #now iterate through remainder
                    temp1.append(val[j:j+3]) #and capture all the 100's
                    k += 1
            else:
                temp1.append(val) #Store the normal values too.

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
    for key in keys: #add cat data to the hour_dict by hour

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

        mos_dict[apid] = hour_dict #marry the hour_dict to the proper key in mos_dict

#For Heat Map. Based on visits, assign color. Using a 0 to 100 scale where 0 is never visted and 100 is home airport.
#Can choose to display binary colors with homeap.
def assign_color(visits):
    if visits == '0':
        color = no_visits

    elif visits == '100':
        if fade_yesno == 1 and bin_grad == 1:
            color = black
        elif use_homeap != 1:
            color = high_visits
        else:
            color = homeap

    elif '1' <= visits <= '50': #Working
        if bin_grad == 1:
            red = low_visits[0]
            grn = low_visits[1]
            blu = low_visits[2]
            red = int(int(visits) * 5.1)
            color = (red,grn,blu)
        else:
            color = high_visits

    elif '51' <= visits <= '99': #Working
        if bin_grad == 1:
            red = high_visits[0]
            grn = high_visits[1]
            blu = high_visits[2]
            blu = (255 - int((int(visits)-50) * 5.1))
            color = (red,grn,blu)
        else:
            color = high_visits

    else:
        color = black

    return color

##########################
# Start of executed code #
##########################
toggle = 0                      #used for homeport display
outerloop = 1                   #Set to TRUE for infinite outerloop
display_num = 0
while (outerloop):
    display_num = display_num + 1

    #Time calculations, dependent on 'hour_to_display' offset. this determines how far in the future the TAF data should be.
    #This time is recalculated everytime the FAA data gets updated
    zulu = datetime.utcnow() + timedelta(hours=hour_to_display)     #Get current time plus Offset
    current_zulu = zulu.strftime('%Y-%m-%dT%H:%M:%SZ')              #Format time to match whats reported in TAF. ie. 2020-03-24T18:21:54Z
    current_hr_zulu = zulu.strftime('%H')                           #Zulu time formated for just the hour, to compare to MOS data

    #Dictionary definitions. Need to reset whenever new weather is received
    stationiddict = {}
    windsdict = {"":""}
    wxstringdict = {"":""}

    #Call script and execute desired wipe(s) while data is being updated.
    if usewipes ==  1 and toggle_sw != -1:
        exec(compile(open("/NeoSectional/wipes-v4.py", "rb").read(), "/NeoSectional/wipes-v4.py", 'exec')) #Get latest ip's to display in editors
        logger.info("Calling wipes script")

    #read airports file - read each time weather is updated in case a change to "airports" file was made while script was running.
    try:
        with open('/NeoSectional/airports') as f:
            airports = f.readlines()
    except IOError as error:
        logger.error('Airports file could not be loaded.')
        logger.error(error)
        break

    airports = [x.strip() for x in airports]
    logger.info('Airports File Loaded')

    #depending on what data is to be displayed, either use an URL for METARs and TAFs or read file from drive (pass).
    if metar_taf_mos == 1: #Check to see if the script should display TAF data (0), METAR data (1) or MOS data (2)
        #Define URL to get weather METARS. If no METAR reported withing the last 2.5 hours, Airport LED will be white (nowx).
        #url = "https://aviationweather-cprk.ncep.noaa.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&mostRecentForEachStation=constraint&hoursBeforeNow="+str(metar_age)+"&stationString="
        url = "https://aviationweather.gov/api/data/metar?format=xml&hours=" +str(metar_age)+ "&ids="
        logger.info("METAR Data Loading")

    elif metar_taf_mos == 0:
        #Define URL to get weather URL for TAF. If no TAF reported for an airport, the Airport LED will be white (nowx).
        #url = "https://aviationweather-cprk.ncep.noaa.gov/adds/dataserver_current/httpparam?dataSource=tafs&requestType=retrieve&format=xml&mostRecentForEachStation=constraint&hoursBeforeNow="+str(metar_age)+"&stationString="
        url = "https://aviationweather.gov/api/data/taf?format=xml&hours=" +str(metar_age)+ "&ids="
        logger.info("TAF Data Loading")

    elif metar_taf_mos == 2: #MOS data is not accessible in the same way as METARs and TAF's. A large file is downloaded by crontab everyday that gets read.
        pass             #This elif is not strictly needed and is only here for clarity
        logger.info("MOS Data Loading")

    elif metar_taf_mos == 3: #Heat Map
        pass
        logger.info("Heat Map Data Loading")

    #Build URL to submit to FAA with the proper airports from the airports file for METARs and TAF's but not MOS data
    # Thank you Daniel from pilotmap.co for the change to this routine that handles maps with more than 300 airports.
    if metar_taf_mos != 2 and metar_taf_mos != 3:
        contentStart = ['<response xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.2" xsi:noNamespaceSchemaLocation="https://aviationweather.gov/data/schema/metar1_3.xsd">']
        content = []
        chunk = 0;
        stationList = ''
        for airportcode in airports:
          if airportcode == "NULL" or airportcode == "LGND":
             continue
          stationList += airportcode + ','
          chunk += 1
          #logger.info('Chunk size: ' + str(chunk))
          if(chunk >= 300):
             stationList = stationList[:-1] #strip trailing comma from string

             while True: #check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
              s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
              s.connect(("8.8.8.8", 80))
              ipadd = s.getsockname()[0] #get IP Address
              logger.info('RPI IP Address = ' + ipadd) #log IP address when ever FAA weather update is retreived.
              logger.info('API URL Chunk: ' + url + stationList)
              result = ''
              try:
                result = urllib.request.urlopen(url + stationList).read()
                r = result.decode('UTF-8').splitlines()
                xmlStr = r[8:len(r)-2]
                content.extend(xmlStr)
                c = ['<x>']
                c.extend(content)
                root = ET.fromstringlist(c + ['</x>'])
                logger.info('Internet Available')
                break
              except Exception as e:
                print(str(e))
                logger.warning('FAA Data is Not Available')
                logger.warning(url + stationList)
                logger.warning(result)
                time.sleep(delay_time)
                pass

             stationList = ''
             chunk = 0


        stationList = stationList[:-1] #strip trailing comma from string

        url = url + stationList
        logger.debug(url) #debug

        while True: #check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ipadd = s.getsockname()[0] #get IP Address
            logger.info('RPI IP Address = ' + ipadd) #log IP address when ever FAA weather update is retreived.
            logger.info('API URL No chunk: ' + url)
            try:
                result = urllib.request.urlopen(url).read()
                logger.info('Internet Available')
                logger.info(url)
                r = result.decode('UTF-8').splitlines()
                xmlStr = r[8:len(r)-2]
                content.extend(xmlStr)
                c = ['<x>']
                c.extend(content)
                root = ET.fromstringlist(c + ['</x>'])
                break
            except:
                logger.warning('FAA Data is Not Available')
                logger.warning(url)
                time.sleep(delay_time)
                pass

        c = ['<x>']
        c.extend(content)
        root = ET.fromstringlist(c + ['</x>'])


    if turnoffrefresh == 0:
        turnoff(strip) #turn off led before repainting them. If Rainbow stays on, it has hung up before this.

    #Heat Map routine
    #This will allow the user to display which airports on the map have been landed at. There are 2 display modes;
    #Binary and Gradient. Binary simply uses Red for visited airports and grey for not visited.
    #Gradient display will starts with cool blue for airports rarely visited to hot red to those visited alot.
    #The home airport can be denoted using Green. It can also fade in/out for some animation.
    if metar_taf_mos == 3:
        #read hmdata file - read each time weather is updated in case a change to "airports" file was made while script was running.
        j = 0
        logger.info("Starting Heat Map")
        with open('/NeoSectional/hmdata') as f:
            for line in f:
                (apid, visits) = line.split(' ')
                apid = apid.strip()
                visits = visits.strip()
                pin = str(j)
                j += 1
                if apid != 'NULL' and apid != 'LGND':
                    stationiddict[pin] = (apid,visits)

            #set all the airport their correct color.
            for pin in stationiddict:
                apid = stationiddict[pin][0]
                visits = stationiddict[pin][1]
                if visits == '100':
                    fadehome = pin
                color = assign_color(visits)
                logger.debug(str(pin) + str(apid) + str(visits) + str(color)) #debug

                xcolor = rgbtogrb(pin, color, rgb_grb)
                color = Color(xcolor[0], xcolor[1], xcolor[2])
                strip.setPixelColor(int(pin), color) #set color to display on a specific LED for the current cycle_num cycle.

            strip.show() #Display strip with newly assigned colors for the current cycle_num cycle.

        while True:
            #Routine to restart this script if config.py is changed while this script is running.
            for f, mtime in WATCHED_FILES_MTIMES:
                if getmtime(f) != mtime:
                    logger.info("Restarting from awake" + __file__ + " in 2 sec...")
                    time.sleep(2)
                    os.execv(sys.executable, [sys.executable] +  [__file__]) #'/NeoSectional/metar-v4.py'])

            #Bright light will provide a low state (0) on GPIO. Dark light will provide a high state (1).
            #Full brightness will be used if no light sensor is installed.
            if GPIO.input(4) == 1:
                LED_BRIGHTNESS = dimmed_value
            else:
                LED_BRIGHTNESS = bright_value
            strip.setBrightness(LED_BRIGHTNESS)
            strip.show()

            #fade in/out the home airport
            if int(fadehome) >= 0 and fade_yesno == 1 and bin_grad == 1:
                pin = fadehome
                for i in range(256):
                    time.sleep(fade_delay)
                    red = homeap[0]
                    grn = homeap[1]
                    blu = homeap[2]
                    color = [red, i, blu]
                    xcolor = rgbtogrb(pin, color, rgb_grb)
                    color = Color(xcolor[0], xcolor[1], xcolor[2])
                    strip.setPixelColor(int(pin), color) #set color to display on a specific LED for the current cycle_num cycle.
                    strip.show()

                time.sleep(fade_delay *50) #Keep light full bright for a moment.

                for j in range(255,-1,-1):
                    time.sleep(fade_delay)
                    red = homeap[0]
                    grn = homeap[1]
                    blu = homeap[2]
                    color = [red, j, blu]
                    xcolor = rgbtogrb(pin, color, rgb_grb)
                    color = Color(xcolor[0], xcolor[1], xcolor[2])
                    strip.setPixelColor(int(pin), color) #set color to display on a specific LED for the current cycle_num cycle.
                    strip.show()

            #Check if rotary switch is used, and what position it is in. This will determine what to display, METAR, TAF and MOS data.
            #If TAF or MOS data, what time offset should be displayed, i.e. 0 hour, 1 hour, 2 hour etc.
            #If there is no rotary switch installed, then all these tests will fail and will display the defaulted data from switch position 0
            if GPIO.input(0) == False and toggle_sw != 0:
                toggle_sw = 0
                hour_to_display = time_sw0              #Offset in HOURS not used to display METAR
                metar_taf_mos = data_sw0                #1 = Display METAR.
                logger.info('Switch in position 0. Breaking out of loop for METARs')
                break

            elif GPIO.input(5) == False and toggle_sw != 1:
                toggle_sw = 1
                hour_to_display = time_sw1              #Offset in HOURS to choose which TAF to display
                metar_taf_mos = data_sw1                #0 = Display TAF.
                logger.info('Switch in position 1. Breaking out of loop for TAF/MOS + ' + str(time_sw1) + ' hour')
                break

            elif GPIO.input(6) == False and toggle_sw != 2:
                toggle_sw = 2
                hour_to_display = time_sw2              #Offset in HOURS to choose which TAF to display
                metar_taf_mos = data_sw2                #0 = Display TAF.
                logger.info('Switch in position 2. Breaking out of loop for MOS/TAF + ' + str(time_sw2) + '  hours')
                break

            elif GPIO.input(13) == False and toggle_sw != 3:
                toggle_sw = 3
                hour_to_display = time_sw3              #Offset in HOURS to choose which TAF to display
                metar_taf_mos = data_sw3                #0 = Display TAF.
                logger.info('Switch in position 3. Breaking out of loop for MOS/TAF + ' + str(time_sw3) + '  hours')
                break

            elif GPIO.input(19) == False and toggle_sw != 4:
                toggle_sw = 4
                hour_to_display = time_sw4              #Offset in HOURS to choose which TAF to display
                metar_taf_mos = data_sw4                #0 = Display TAF.
                logger.info('Switch in position 4. Breaking out of loop for MOS/TAF + ' + str(time_sw4) + '  hours')
                break

            elif GPIO.input(26) == False and toggle_sw != 5:
                toggle_sw = 5
                hour_to_display = time_sw5              #Offset in HOURS to choose which TAF to display
                metar_taf_mos = data_sw5                #0 = Display TAF.
                logger.info('Switch in position 5. Breaking out of loop for MOS/TAF + ' + str(time_sw5) + '  hours')
                break

            elif GPIO.input(21) == False and toggle_sw != 6:
                toggle_sw = 6
                hour_to_display = time_sw6              #Offset in HOURS to choose which TAF to display
                metar_taf_mos = data_sw6                #0 = Display TAF.
                logger.info('Switch in position 6. Breaking out of loop for MOS/TAF + ' + str(time_sw6) + '  hours')
                break

            elif GPIO.input(20) == False and toggle_sw != 7:
                toggle_sw = 7
                hour_to_display = time_sw7              #Offset in HOURS to choose which TAF to display
                metar_taf_mos = data_sw7                #0 = Display TAF.
                logger.info('Switch in position 7. Breaking out of loop for MOS/TAF + ' + str(time_sw7) + '  hours')
                break

            elif GPIO.input(16) == False and toggle_sw != 8:
                toggle_sw = 8
                hour_to_display = time_sw8              #Offset in HOURS to choose which TAF to display
                metar_taf_mos = data_sw8                #0 = Display TAF.
                logger.info('Switch in position 8. Breaking out of loop for MOS/TAF + ' + str(time_sw8) + '  hours')
                break

            elif GPIO.input(12) == False and toggle_sw != 9:
                toggle_sw = 9
                hour_to_display = time_sw9              #Offset in HOURS to choose which TAF to display
                metar_taf_mos = data_sw9                #0 = Display TAF.
                logger.info('Switch in position 9. Breaking out of loop for MOS/TAF + ' + str(time_sw9) + '  hours')
                break

            elif GPIO.input(1) == False and toggle_sw != 10:
                toggle_sw = 10
                hour_to_display = time_sw10             #Offset in HOURS to choose which TAF to display
                metar_taf_mos = data_sw10               #0 = Display TAF.
                logger.info('Switch in position 10. Breaking out of loop for MOS/TAF + ' + str(time_sw10) + '  hours')
                break

            elif GPIO.input(7) == False and toggle_sw != 11:
                toggle_sw = 11
                hour_to_display = time_sw11             #Offset in HOURS to choose which TAF to display
                metar_taf_mos = data_sw11               #0 = Display TAF.
                logger.info('Switch in position 11. Breaking out of loop for MOS/TAF + ' + str(time_sw11) + '  hours')
                break

            elif toggle_sw == -1 or toggle_sw == 12:                       #used if no Rotary Switch is installed
                toggle_sw = 12
                hour_to_display = time_sw0              #Offset in HOURS not used to display METAR
                metar_taf_mos = data_sw0                    #1 = Display METAR.
                logger.info('Rotary Switch Not Installed. Using Switch Position 0 as Default')
#                break

        #The Heat Map routine stays within this limit and won't proceed beyond this point.

    #MOS decode routine
    #MOS data is downloaded daily from; https://www.weather.gov/mdl/mos_gfsmos_mav to the local drive by crontab scheduling.
    #Then this routine reads through the entire file looking for those airports that are in the airports file. If airport is
    #found, the data needed to display the weather for the next 24 hours is captured into mos_dict, which is nested with
    #hour_dict, which holds the airport's MOS data by 3 hour chunks. See; https://www.weather.gov/mdl/mos_gfsmos_mavcard for
    #a breakdown of what the MOS data looks like and what each line represents.
    if metar_taf_mos == 2:
        logger.info("Starting MOS Data Display")
        #Read current MOS text file
        try:
            file = open(mos_filepath, 'r')
            lines = file.readlines()
        except IOError as error:
            logger.error('MOS data file could not be loaded.')
            logger.error(error)
            break

        for line in lines:      #read the MOS data file line by line0
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
                unused, apid, mos_date = line.split(" ",2)

                #If this Airport ID is in the airports file then grab all the info needed from this MOS
                if apid in airports:
                    ap_flag = 1
                    cat_counter = 0 #used to determine if a category is being reported in MOS or not. If not, need to inject it.
                    dat0, dat1, dat2, dat3, dat4, dat5, dat6, dat7 = ([] for i in range(8)) #Clear lists
                continue

            #If we just found an airport that is in our airports file, then grab the appropriate weather data from it's MOS
            if ap_flag:
                xtra, cat, value = line.split(" ",2)    #capture the category the line read represents
                #Check if the needed categories are being read and if so, grab its data
                if cat in categories:
                    cat_counter += 1 #used to check if a category is not in mos report for airport
                    if cat == 'HR': #hour designation
                        temp = (re.findall(r'\s?(\s*\S+)', value.rstrip()))     #grab all the hours from line read
                        for j in range(8):
                            tmp = temp[j].strip()
                            hour_dict[tmp] = '' #create hour dictionary based on mos data
                        keys = list(hour_dict.keys()) #Get the hours which are the keys in this dict, so they can be properly poplulated

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
                                temp = ['9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9', '9']
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
                            last_cat = cat #store what the last read cat was.
                            temp = (re.findall(r'\s?(\s*\S+)', value.rstrip()))
                            set_data()
                            hour_dict = collections.OrderedDict() #clear out hour_dict for next airport

        #Now grab the data needed to display on map. Key: [airport][hr][j] - using nested dictionaries
        #   airport = from airport file, 4 character ID. hr = 1 of 8 three-hour periods of time, 00 03 06 09 12 15 18 21
        #   j = index to weather categories, in this order; 'CLD','WDR','WSP','P06', 'T06', 'POZ', 'POS', 'TYP','CIG','VIS','OBV'.
        #   See; https://www.weather.gov/mdl/mos_gfsmos_mavcard for description of available data.
        for airport in airports:
            if airport in mos_dict:
                logger.debug('\n' + airport) #debug
                logger.debug(categories) #debug

                mos_time = int(current_hr_zulu) + hour_to_display
                if mos_time >= 24: #check for reset at 00z
                    mos_time = mos_time - 24

                for hr in keys:
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

                        logger.debug(mos_date + hr + cld + wdr + wsp + p06 + t06 + poz + pos + typ + cig + vis + obv) #debug

                        #decode the weather for each airport to display on the livesectional map
                        flightcategory = "VFR" #start with VFR as the assumption
                        if cld in ("OV","BK"): #If the layer is OVC, BKN, set Flight category based on height of layer

                            if cig <= '2': #AGL is less than 500:
                                flightcategory = "LIFR"

                            elif cig == '3': #AGL is between 500 and 1000
                                flightcategory = "IFR"
                            elif '4' <= cig <= '5': #AGL is between 1000 and 3000:
                                flightcategory = "MVFR"

                            elif cig >= '6': #AGL is above 3000
                                flightcategory = "VFR"

                        #Check visability too.
                        if flightcategory != "LIFR": #if it's LIFR due to cloud layer, no reason to check any other things that can set fl$

                            if vis <= '2': #vis < 1.0 mile:
                                flightcategory = "LIFR"

                            elif '3' <= vis < '4': #1.0 <= vis < 3.0 miles:
                                flightcategory = "IFR"

                            elif vis == '5' and flightcategory != "IFR":  #3.0 <= vis <= 5.0 miles
                                flightcategory = "MVFR"

                        logger.debug(flightcategory + " |"),
                        logger.debug('Windspeed = ' + wsp + ' | Wind dir = ' + wdr + ' |'),

                        #decode reported weather using probabilities provided.
                        if typ == '9': #check to see if rain, freezing rain or snow is reported. If not use obv weather
                            wx = obv_wx[obv] #Get proper representation for obv designator
                        else:
                            wx = typ_wx[typ] #Get proper representation for typ designator

                            if wx == 'RA' and int(p06) < prob:
                                if obv != 'N':
                                    wx = obv_wx[obv]
                                else:
                                    wx = 'NONE'

                            if wx == 'SN' and int(pos) < prob:
                                wx = 'NONE'

                            if wx == 'FZRA' and int(poz) < prob:
                                wx = 'NONE'

#                            print (t06,apid) #debug
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
                if wsp == None: #if wind speed is blank, then bypass
                    windspeedkt = 0
                elif wsp == '99': #Check to see if MOS data is not reporting windspeed for this airport
                    windspeedkt = 0
                else:
                    windspeedkt = int(wsp)

                #grab Weather info from returned FAA data
                if wx is None: #if weather string is blank, then bypass
                    wxstring = "NONE"
                else:
                    wxstring = wx

                logger.debug(stationId + ", " + str(windspeedkt) + ", " + wxstring) #debug

                #Check for duplicate airport identifier and skip if found, otherwise store in dictionary. covers for dups in "airports" file
                if stationId in stationiddict:
                    logger.info(stationId + " Duplicate, only saved first metar category")
                else:
                    stationiddict[stationId] = flightcategory #build category dictionary

                if stationId in windsdict:
                    logger.info(stationId + " Duplicate, only saved the first winds")
                else:
                    windsdict[stationId] = windspeedkt #build windspeed dictionary

                if stationId in wxstringdict:
                    logger.info(stationId + " Duplicate, only saved the first weather")
                else:
                    wxstringdict[stationId] = wxstring #build weather dictionary
        logger.info("Decoded MOS Data for Display")


    #TAF decode routine
    if metar_taf_mos == 0: #0 equals display TAF. This routine will decode the TAF, pick the appropriate time frame to display.
        logging.info("Starting TAF Data Display")
        #start of TAF decoding routine
        for data in root.iter('data'):
            num_results = data.attrib['num_results']        #get number of airports reporting TAFs to be used for diagnosis only
            logger.debug("\nNum of Airport TAFs = " + num_results) #debug

        for taf in root.iter('TAF'):                            #iterate through each airport's TAF
            stationId = taf.find('station_id').text #debug
            logger.debug(stationId) #debug
            logger.debug('Current+Offset Zulu - ' + current_zulu) #debug
            taf_wx_string = ""
            taf_change_indicator = ""
            taf_wind_dir_degrees = ""
            taf_wind_speed_kt = ""
            taf_wind_gust_kt = ""

            for forecast in taf.findall('forecast'):        #Now look at the forecasts for the airport

                # Routine inspired by Nick Cirincione.
                flightcategory = "VFR"                  #intialize flight category
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
                    logger.debug('FROM - ' + taf_time_from)
                    logger.debug(comp_time(taf_time_from))
                    logger.debug('TO - ' + taf_time_to)
                    logger.debug(comp_time(taf_time_to))

                    #There can be multiple layers of clouds in each taf, but they are always listed lowest AGL first.
                    #Check the lowest (first) layer and see if it's overcast, broken, or obscured. If it is, then compare to cloud base height to set $
                    #This algorithm basically sets the flight category based on the lowest OVC, BKN or OVX layer.
                    for sky_condition in forecast.findall('sky_condition'): #for each sky_condition from the XML
                        sky_cvr = sky_condition.attrib['sky_cover']     #get the sky cover (BKN, OVC, SCT, etc)
                        logger.debug(sky_cvr) #debug

                        if sky_cvr in ("OVC","BKN","OVX"): #If the layer is OVC, BKN or OVX, set Flight category based on height AGL

                            try:
                                cld_base_ft_agl = sky_condition.attrib['cloud_base_ft_agl'] #get cloud base AGL from XML
                                logger.debug(cld_base_ft_agl) #debug
                            except:
                                cld_base_ft_agl = forecast.find('vert_vis_ft').text #get cloud base AGL from XML


#                            cld_base_ft_agl = sky_condition.attrib['cloud_base_ft_agl'] #get cloud base AGL from XML
#                            logger.debug(cld_base_ft_agl) #debug

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
                    if flightcategory != "LIFR": #if it's LIFR due to cloud layer, no reason to check any other things that can set flight category.
                        if forecast.find('visibility_statute_mi') is not None: #check XML if visibility value exists
                            visibility_statute_mi = forecast.find('visibility_statute_mi').text   #get visibility number
                            visibility_statute_mi = float(visibility_statute_mi.strip('+'))
                            logger.debug(visibility_statute_mi)

                            if visibility_statute_mi < 1.0:
                                flightcategory = "LIFR"

                            elif 1.0 <= visibility_statute_mi < 3.0:
                                flightcategory = "IFR"

                            elif 3.0 <= visibility_statute_mi <= 5.0 and flightcategory != "IFR":  #if Flight Category was already set to IFR $
                                flightcategory = "MVFR"

                    #Print out TAF data to screen for diagnosis only
                    logger.debug('Airport - ' + stationId)
                    logger.debug('Flight Category - ' + flightcategory)
                    logger.debug('Wind Speed - ' + taf_wind_speed_kt)
                    logger.debug('WX String - ' + taf_wx_string)
                    logger.debug('Change Indicator - ' + taf_change_indicator)
                    logger.debug('Wind Director Degrees - ' + taf_wind_dir_degrees)
                    logger.debug('Wind Gust - ' + taf_wind_gust_kt)

                    #grab flightcategory from returned FAA data
                    if flightcategory is None: #if wind speed is blank, then bypass
                        flightcategory = None

                    #grab wind speeds from returned FAA data
                    if taf_wind_speed_kt is None: #if wind speed is blank, then bypass
                        windspeedkt = 0
                    else:
                        windspeedkt = taf_wind_speed_kt

                    #grab Weather info from returned FAA data
                    if taf_wx_string is None: #if weather string is blank, then bypass
                        wxstring = "NONE"
                    else:
                        wxstring = taf_wx_string

            #Check for duplicate airport identifier and skip if found, otherwise store in dictionary. covers for dups in "airports" file
            if stationId in stationiddict:
                logger.info(stationId + " Duplicate, only saved first metar category")
            else:
                stationiddict[stationId] = flightcategory #build category dictionary

            if stationId in windsdict:
                logger.info(stationId + " Duplicate, only saved the first winds")
            else:
                windsdict[stationId] = windspeedkt #build windspeed dictionary

            if stationId in wxstringdict:
                logger.info(stationId + " Duplicate, only saved the first weather")
            else:
                wxstringdict[stationId] = wxstring #build weather dictionary
        logger.info("Decoded TAF Data for Display")


    elif metar_taf_mos == 1:
        logger.info("Starting METAR Data Display")
        #start of METAR decode routine if 'metar_taf_mos' equals 1. Script will default to this routine without a rotary switch installed.
        #grab the airport category, wind speed and various weather from the results given from FAA.
        for metar in root.iter('METAR'):
            stationId = metar.find('station_id').text


        ### METAR Decode Routine to create flight category via cloud cover and/or visability when flight category is not reported.
        # Routine contributed to project by Nick Cirincione. Thank you for your contribution.
            if metar.find('flight_category') is None or metar.find('flight_category') == 'NONE': #if category is blank, then see if there's a sky condition or vis that would dictate flight category
                flightcategory = "VFR" #intialize flight category
                sky_cvr = "SKC" # Initialize to Sky Clear
                logger.info(stationId + " Not Reporting Flight Category through the API.")

                # There can be multiple layers of clouds in each METAR, but they are always listed lowest AGL first.
                # Check the lowest (first) layer and see if it's overcast, broken, or obscured. If it is, then compare to cloud base height to set flight category.
                # This algorithm basically sets the flight category based on the lowest OVC, BKN or OVX layer.
                # First check to see if the FAA provided the forecast field, if not get the sky_condition.
                if metar.find('forecast') is None or metar.find('forecast') == 'NONE':
                    logger.info('FAA xml data is NOT providing the forecast field for this airport')
                    for sky_condition in metar.findall('./sky_condition'):   #for each sky_condition from the XML
                        sky_cvr = sky_condition.attrib['sky_cover']     #get the sky cover (BKN, OVC, SCT, etc)
                        logger.debug('Sky Cover = ' + sky_cvr)

                        if sky_cvr in ("OVC","BKN","OVX"): # Break out of for loop once we find one of these conditions
                            break

                else:
                    logger.info('FAA xml data IS providing the forecast field for this airport')
                    for sky_condition in metar.findall('./forecast/sky_condition'):   #for each sky_condition from the XML
                        sky_cvr = sky_condition.attrib['sky_cover']     #get the sky cover (BKN, OVC, SCT, etc)
                        logger.debug('Sky Cover = ' + sky_cvr)
                        logger.debug(metar.find('./forecast/fcst_time_from').text)

                        if sky_cvr in ("OVC","BKN","OVX"): # Break out of for loop once we find one of these conditions
                            break

                if sky_cvr in ("OVC","BKN","OVX"): #If the layer is OVC, BKN or OVX, set Flight category based on height AGL
                    try:
                        cld_base_ft_agl = sky_condition.attrib['cloud_base_ft_agl'] #get cloud base AGL from XML
                    except:
                        cld_base_ft_agl = forecast.find('vert_vis_ft').text #get cloud base AGL from XML

                    logger.debug('Cloud Base = ' + cld_base_ft_agl)
                    cld_base_ft_agl = int(cld_base_ft_agl)

                    if cld_base_ft_agl < 500:
                        flightcategory = "LIFR"
#                        break
                    elif 500 <= cld_base_ft_agl < 1000:
                        flightcategory = "IFR"
#                        break
                    elif 1000 <= cld_base_ft_agl <= 3000:
                        flightcategory = "MVFR"
#                        break
                    elif cld_base_ft_agl > 3000:
                        flightcategory = "VFR"
#                        break

                #visibilty can also set flight category. If the clouds haven't set the fltcat to LIFR. See if visibility will
                if flightcategory != "LIFR": #if it's LIFR due to cloud layer, no reason to check any other things that can set flight category.
                    if metar.find('./forecast/visibility_statute_mi') is not None: #check XML if visibility value exists
                        visibility_statute_mi = metar.find('./forecast/visibility_statute_mi').text   #get visibility number
                        visibility_statute_mi = float(visibility_statute_mi.strip('+'))

                        if visibility_statute_mi < 1.0:
                            flightcategory = "LIFR"

                        elif 1.0 <= visibility_statute_mi < 3.0:
                            flightcategory = "IFR"

                        elif 3.0 <= visibility_statute_mi <= 5.0 and flightcategory != "IFR":  #if Flight Category was already set to IFR by clouds, it can't be reduced to MVFR
                            flightcategory = "MVFR"

                logger.debug(stationId + " flight category is Decode script-determined as " + flightcategory)

            else:
                logger.debug(stationId + ': FAA is reporting '+metar.find('flight_category').text + ' through their API')
                flightcategory = metar.find('flight_category').text  #pull flight category if it exists and save all the algoritm above
            ### End of METAR Decode added routine to create flight category via cloud cover and/or visability when flight category is not reported.


            #grab wind speeds from returned FAA data
            if metar.find('wind_speed_kt') is None: #if wind speed is blank, then bypass
                windspeedkt = 0
            else:
                windspeedkt = metar.find('wind_speed_kt').text

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
                logger.info(stationId + " Duplicate, only saved the first winds")
            else:
                windsdict[stationId] = windspeedkt #build windspeed dictionary

            if stationId in wxstringdict:
                logger.info(stationId + " Duplicate, only saved the first weather")
            else:
                wxstringdict[stationId] = wxstring #build weather dictionary
        logger.info("Decoded METAR Data for Display")

    #Setup timed loop for updating FAA Weather that will run based on the value of 'update_interval' which is a user setting
    timeout_start = time.time() #Start the timer. When timer hits user-defined value, go back to outer loop to update FAA Weather.
    loopcount=0
    while time.time() < timeout_start + (update_interval * 60): #take 'update_interval' which is in minutes and turn into seconds
        loopcount = loopcount + 1

        # Check time and reboot machine if time equals time_reboot and if use_reboot along with autorun are both set to 1
        if use_reboot == 1 and autorun == 1:
            now = datetime.now()
            rb_time = now.strftime("%H:%M")
            logger.debug("**Current Time=" + str(rb_time) + " - **Reboot Time=" + str(time_reboot))
            print("**Current Time=" + str(rb_time) + " - **Reboot Time=" + str(time_reboot)) #debug

            if rb_time == time_reboot:
                logger.info("Rebooting at " + time_reboot)
                time.sleep(1)
                os.system("sudo reboot now")

        #Routine to restart this script if config.py is changed while this script is running.
        for f, mtime in WATCHED_FILES_MTIMES:
            if getmtime(f) != mtime:
                logger.info("Restarting from awake" + __file__ + " in 2 sec...")
                time.sleep(2)
                os.execv(sys.executable, [sys.executable] +  [__file__]) #'/NeoSectional/metar-v4.py'])

        #Timer routine, used to turn off LED's at night if desired. Use 24 hour time in settings.
        if usetimer: #check to see if the user wants to use a timer.

             if time_in_range(timeoff, end_time, datetime.now().time()):

                # If temporary lights-on period from refresh button has expired, restore the original light schedule
                if temp_lights_on == 1:
                    end_time = lights_on
                    timeoff = lights_out
                    temp_lights_on = 0

                sys.stdout.write ("\n\033[1;34;40m Sleeping-  ") #Escape codes to render Blue text on screen
                sys.stdout.flush ()
                turnoff(strip)
                logger.info("Map Going to Sleep")

                while time_in_range(timeoff, end_time, datetime.now().time()):
                    sys.stdout.write ("z")
                    sys.stdout.flush ()
                    time.sleep(1)
                    if GPIO.input(22) == False: #Pushbutton for Refresh. check to see if we should turn on temporarily during sleep mode
                        # Set to turn lights on two seconds ago to make sure we hit the loop next time through
                        end_time = (datetime.now()-timedelta(seconds=2)).time()
                        timeoff = (datetime.now()+timedelta(minutes=tempsleepon)).time()
                        temp_lights_on = 1 #Set this to 1 if button is pressed
                        logger.info("Sleep interrupted by button push")

                    #Routine to restart this script if config.py is changed while this script is running.
                    for f, mtime in WATCHED_FILES_MTIMES:
                        if getmtime(f) != mtime:
                            print ("\033[0;0m\n") #Turn off Blue text.
                            logger.info("Restarting from sleep" + __file__ + " in 2 sec...")
                            time.sleep(2)
                            os.execv(sys.executable, [sys.executable] +  [__file__]) #restart this script.

                print ("\033[0;0m\n") #Turn off Blue text.

        #Check if rotary switch is used, and what position it is in. This will determine what to display, METAR, TAF and MOS data.
        #If TAF or MOS data, what time offset should be displayed, i.e. 0 hour, 1 hour, 2 hour etc.
        #If there is no rotary switch installed, then all these tests will fail and will display the defaulted data from switch position 0
        if GPIO.input(0) == False and toggle_sw != 0:
            toggle_sw = 0
            hour_to_display = time_sw0              #Offset in HOURS not used to display METAR
            metar_taf_mos = data_sw0                #1 = Display METAR.
            logger.info('Switch in position 0. Breaking out of loop for METARs')
            break

        elif GPIO.input(5) == False and toggle_sw != 1:
            toggle_sw = 1
            hour_to_display = time_sw1              #Offset in HOURS to choose which TAF to display
            metar_taf_mos = data_sw1                #0 = Display TAF.
            logger.info('Switch in position 1. Breaking out of loop for TAF/MOS + ' + str(time_sw1) + ' hour')
            break

        elif GPIO.input(6) == False and toggle_sw != 2:
            toggle_sw = 2
            hour_to_display = time_sw2              #Offset in HOURS to choose which TAF to display
            metar_taf_mos = data_sw2                #0 = Display TAF.
            logger.info('Switch in position 2. Breaking out of loop for MOS/TAF + ' + str(time_sw2) + '  hours')
            break

        elif GPIO.input(13) == False and toggle_sw != 3:
            toggle_sw = 3
            hour_to_display = time_sw3              #Offset in HOURS to choose which TAF to display
            metar_taf_mos = data_sw3                #0 = Display TAF.
            logger.info('Switch in position 3. Breaking out of loop for MOS/TAF + ' + str(time_sw3) + '  hours')
            break

        elif GPIO.input(19) == False and toggle_sw != 4:
            toggle_sw = 4
            hour_to_display = time_sw4              #Offset in HOURS to choose which TAF to display
            metar_taf_mos = data_sw4                #0 = Display TAF.
            logger.info('Switch in position 4. Breaking out of loop for MOS/TAF + ' + str(time_sw4) + '  hours')
            break

        elif GPIO.input(26) == False and toggle_sw != 5:
            toggle_sw = 5
            hour_to_display = time_sw5              #Offset in HOURS to choose which TAF to display
            metar_taf_mos = data_sw5                #0 = Display TAF.
            logger.info('Switch in position 5. Breaking out of loop for MOS/TAF + ' + str(time_sw5) + '  hours')
            break

        elif GPIO.input(21) == False and toggle_sw != 6:
            toggle_sw = 6
            hour_to_display = time_sw6              #Offset in HOURS to choose which TAF to display
            metar_taf_mos = data_sw6                #0 = Display TAF.
            logger.info('Switch in position 6. Breaking out of loop for MOS/TAF + ' + str(time_sw6) + '  hours')
            break

        elif GPIO.input(20) == False and toggle_sw != 7:
            toggle_sw = 7
            hour_to_display = time_sw7              #Offset in HOURS to choose which TAF to display
            metar_taf_mos = data_sw7                #0 = Display TAF.
            logger.info('Switch in position 7. Breaking out of loop for MOS/TAF + ' + str(time_sw7) + '  hours')
            break

        elif GPIO.input(16) == False and toggle_sw != 8:
            toggle_sw = 8
            hour_to_display = time_sw8              #Offset in HOURS to choose which TAF to display
            metar_taf_mos = data_sw8                #0 = Display TAF.
            logger.info('Switch in position 8. Breaking out of loop for MOS/TAF + ' + str(time_sw8) + '  hours')
            break

        elif GPIO.input(12) == False and toggle_sw != 9:
            toggle_sw = 9
            hour_to_display = time_sw9              #Offset in HOURS to choose which TAF to display
            metar_taf_mos = data_sw9                #0 = Display TAF.
            logger.info('Switch in position 9. Breaking out of loop for MOS/TAF + ' + str(time_sw9) + '  hours')
            break

        elif GPIO.input(1) == False and toggle_sw != 10:
            toggle_sw = 10
            hour_to_display = time_sw10             #Offset in HOURS to choose which TAF to display
            metar_taf_mos = data_sw10               #0 = Display TAF.
            logger.info('Switch in position 10. Breaking out of loop for MOS/TAF + ' + str(time_sw10) + '  hours')
            break

        elif GPIO.input(7) == False and toggle_sw != 11:
            toggle_sw = 11
            hour_to_display = time_sw11             #Offset in HOURS to choose which TAF to display
            metar_taf_mos = data_sw11               #0 = Display TAF.
            logger.info('Switch in position 11. Breaking out of loop for MOS/TAF + ' + str(time_sw11) + '  hours')
            break

        elif toggle_sw == -1:                       #used if no Rotary Switch is installed
            toggle_sw = 12
            hour_to_display = time_sw0              #Offset in HOURS not used to display METAR
            metar_taf_mos = data_sw0                    #1 = Display METAR.
            logger.info('Rotary Switch Not Installed. Using Switch Position 0 as Default')
            break

        #Check to see if pushbutton is pressed to force an update of FAA Weather
        #If no button is connected, then this is bypassed and will only update when 'update_interval' is met
        if GPIO.input(22) == False:
            logger.info('Refresh Pushbutton Pressed. Breaking out of loop to refresh FAA Data')
            break

        #Bright light will provide a low state (0) on GPIO. Dark light will provide a high state (1).
        #Full brightness will be used if no light sensor is installed.
        if GPIO.input(4) == 1:
            LED_BRIGHTNESS = dimmed_value
            if ambient_toggle == 1:
                logger.info("Ambient Sensor set brightness to dimmed_value")
                ambient_toggle = 0
        else:
            LED_BRIGHTNESS = bright_value
            if ambient_toggle == 0:
                logger.info("Ambient Sensor set brightness to bright_value")
                ambient_toggle = 1

        strip.setBrightness(LED_BRIGHTNESS)

        toggle = not(toggle) #Used to determine if the homeport color should be displayed if "homeport = 1"

        print("\nWX Display") # "+str(display_num)+" Cycle Loop # "+str(loopcount)+": ",end="")
        #Start main loop. This loop will create all the necessary colors to display the weather one time.
        for cycle_num in cycles: #cycle through the strip 6 times, setting the color then displaying to create various effects.
            print(" " + str(cycle_num), end = '')
            sys.stdout.flush()

            i = 0 #Inner Loop. Increments through each LED in the strip setting the appropriate color to each individual LED.
            for airportcode in airports:

                flightcategory = stationiddict.get(airportcode,"NONE") #Pull the next flight category from dictionary.
                airportwinds = windsdict.get(airportcode,0) #Pull the winds from the dictionary.
                airportwx_long = wxstringdict.get(airportcode,"NONE") #Pull the weather reported for the airport from dictionary.
                airportwx = airportwx_long.split(" ",1)[0] #Grab only the first parameter of the weather reported.

                #debug print out
                if metar_taf_mos == 0:
                    logger.debug("TAF Time +" + str(hour_to_display) + " Hour")
                elif metar_taf_mos==1:
                    logger.debug("METAR")
                elif metar_taf_mos == 2:
                    logger.debug("MOS Time +" + str(hour_to_display) + " Hour")
                elif metar_taf_mos == 3:
                    logger.debug("Heat Map + ")


                logger.debug((airportcode + " " + flightcategory + " " + str(airportwinds) + " " + airportwx + " " + str(cycle_num) + " ")) #debug

                #Check to see if airport code is a NULL and set to black.
                if airportcode == "NULL" or airportcode == "LGND":
                    color = color_black


                #Build and display Legend. "legend" must be set to 1 in the user defined section and "LGND" set in airports file.
                if legend and airportcode == "LGND" and (i in legend_pins):
                    if i == leg_pin_vfr:
                        color = color_vfr

                    if i == leg_pin_mvfr:
                        color = color_mvfr

                    if i == leg_pin_ifr:
                        color = color_ifr

                    if i == leg_pin_lifr:
                        color = color_lifr

                    if i == leg_pin_nowx:
                        color = color_nowx

                    if i == leg_pin_hiwinds and legend_hiwinds:
                        if (cycle_num == 3 or cycle_num == 4 or cycle_num == 5):
                            color = color_black
                        else:
                            color=color_ifr

                    if i == leg_pin_lghtn and legend_lghtn:
                        if (cycle_num == 2 or cycle_num == 4): #Check for Thunderstorms
                            color = color_lghtn

                        elif (cycle_num == 0 or cycle_num == 1 or cycle_num == 3 or cycle_num == 5):
                            color=color_mvfr

                    if i == leg_pin_snow and legend_snow:
                        if (cycle_num == 3 or cycle_num == 5): #Check for Snow
                            color = color_snow1

                        if (cycle_num == 4):
                            color = color_snow2

                        elif (cycle_num == 0 or cycle_num == 1 or cycle_num == 2):
                            color=color_lifr

                    if i == leg_pin_rain and legend_rain:
                        if (cycle_num == 3 or cycle_num == 5): #Check for Rain
                            color = color_rain1

                        if (cycle_num == 4):
                            color = color_rain2

                        elif (cycle_num == 0 or cycle_num == 1 or cycle_num == 2):
                            color=color_vfr

                    if i == leg_pin_frrain and legend_frrain:
                        if (cycle_num == 3 or cycle_num == 5): #Check for Freezing Rain
                            color = color_frrain1

                        if (cycle_num == 4):
                            color = color_frrain2

                        elif (cycle_num == 0 or cycle_num == 1 or cycle_num == 2):
                            color = color_mvfr

                    if i == leg_pin_dustsandash and legend_dustsandash:
                        if (cycle_num == 3 or cycle_num == 5): #Check for Dust, Sand or Ash
                            color = color_dustsandash1

                        if (cycle_num == 4):
                            color = color_dustsandash2

                        elif (cycle_num == 0 or cycle_num == 1 or cycle_num == 2):
                            color=color_vfr

                    if i == leg_pin_fog and legend_fog:
                        if (cycle_num == 3 or cycle_num == 5): #Check for Fog
                            color = color_fog1

                        if (cycle_num == 4):
                            color = color_fog2

                        elif (cycle_num == 0 or cycle_num == 1 or cycle_num == 2):
                            color=color_ifr

                #Start of weather display code for each airport in the "airports" file
                #Check flight category and set the appropriate color to display
                if  flightcategory != "NONE":
                    if flightcategory == "VFR":     #Visual Flight Rules
                        color = color_vfr
                    elif flightcategory == "MVFR":  #Marginal Visual Flight Rules
                        color = color_mvfr
                    elif flightcategory == "IFR":   #Instrument Flight Rules
                        color = color_ifr
                    elif flightcategory == "LIFR":  #Low Instrument Flight Rules
                        color = color_lifr
                    else:
                        color = color_nowx

                elif flightcategory == "NONE" and airportcode != "LGND" and airportcode != "NULL": #3.01 bug fix by adding "LGND" test
                    color = color_nowx          #No Weather reported.

                #Check winds and set the 2nd half of cycles to black to create blink effect
                if hiwindblink: #bypass if "hiwindblink" is set to 0
        #          if(airportwinds != ''):
              #      print(airportcode, 'airportwinds',type(airportwinds),":".join("{:02x}".format(ord(c)) for c in airportwinds), 'max_wind_speed', max_wind_speed,'cycle_num',cycle_num)
                    if (int(airportwinds) >= max_wind_speed and (cycle_num == 3 or cycle_num == 4 or cycle_num == 5)):
                        color = color_black
                        print(("HIGH WINDS-> " + airportcode + " Winds = " + str(airportwinds) + " ")) #debug
                        logger.info(("HIGH WINDS-> " + airportcode + " Winds = " + str(airportwinds) + " ")) #debug

                #Check the wxstring from FAA for reported weather and create color changes in LED for weather effect.
                if airportwx != "NONE":
                    if  lghtnflash:
                        if (airportwx in wx_lghtn_ck and (cycle_num == 2 or cycle_num == 4)): #Check for Thunderstorms
                            color = color_lghtn

                    if snowshow:
                        if (airportwx in wx_snow_ck and (cycle_num == 3 or cycle_num == 5)): #Check for Snow
                            color = color_snow1

                        if (airportwx in wx_snow_ck and cycle_num == 4):
                            color = color_snow2

                    if rainshow:
                        if (airportwx in wx_rain_ck and (cycle_num == 3 or cycle_num == 4)): #Check for Rain
                            color = color_rain1

                        if (airportwx in wx_rain_ck and cycle_num == 5):
                            color = color_rain2

                    if frrainshow:
                        if (airportwx in wx_frrain_ck and (cycle_num == 3 or cycle_num == 5)): #Check for Freezing Rain
                            color = color_frrain1

                        if (airportwx in wx_frrain_ck and cycle_num == 4):
                            color = color_frrain2

                    if dustsandashshow:
                        if (airportwx in wx_dustsandash_ck and (cycle_num == 3 or cycle_num == 5)): #Check for Dust, Sand or Ash
                            color = color_dustsandash1

                        if (airportwx in wx_dustsandash_ck and cycle_num == 4):
                            color = color_dustsandash2

                    if fogshow:
                        if (airportwx in wx_fog_ck and (cycle_num == 3 or cycle_num == 5)): #Check for Fog
                            color = color_fog1

                        if (airportwx in wx_fog_ck and cycle_num == 4):
                            color = color_fog2

                #If homeport is set to 1 then turn on the appropriate LED using a specific color, This will toggle
                #so that every other time through, the color will display the proper weather, then homeport color(s).
                if i == homeport_pin and homeport and toggle:
                    if homeport_display == 1:
                        color = homeport_colors[cycle_num]
                    elif homeport_display == 2:
                        pass
                    else:
                        color = color_homeport

                xcolor = rgbtogrb(i, color, rgb_grb) #pass pin, color and format. Check and change color code for RGB or GRB format

                if i == homeport_pin and homeport: #if this is the home airport, don't dim out the brightness
                    norm_color = xcolor
                    xcolor = Color(norm_color[0], norm_color[1], norm_color[2])
                elif homeport: #if this is not the home airport, dim out the brightness
                    dim_color = dim(xcolor,dim_value)
                    xcolor = Color(int(dim_color[0]), int(dim_color[1]), int(dim_color[2]))
                else: #if home airport feature is disabled, then don't dim out any airports brightness
                    norm_color = xcolor
                    xcolor = Color(norm_color[0], norm_color[1], norm_color[2])

                strip.setPixelColor(i, xcolor) #set color to display on a specific LED for the current cycle_num cycle.
                i = i + 1 #set next LED pin in strip

            print("/LED.",end='')
            sys.stdout.flush()
            strip.show() #Display strip with newly assigned colors for the current cycle_num cycle.
            print(".",end='')
            wait_time = cycle_wait[cycle_num] #cycle_wait time is a user defined value
            time.sleep(wait_time) #pause between cycles. pauses are setup in user definitions.
