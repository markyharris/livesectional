#wipes-v4.py - by Mark Harris.
#    Updated to work with Python 3.7
#    Custom wipes using airport's lat/lon so any map should be able to utilize these custom wipes.
#    This is run from metar-v4.py if builder would like to use a wipe when weather is updated
#    Includes the following patterns;
#       Rainbow
#       Square
#       Circle
#       Radar
#       Up/Down and Side to Side
#       All One Color
#       Fader
#       Shuffle
#       Morse Code
#       Rabbit Chase
#
#    Fixed wipes that turned on NULL and LGND Leds
#    Fixed dimming feature when a wipe is executed
#    Fixed bug whereby lat/lon was miscalculated for certain wipes.

#Import needed libraries
import urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree as ET
import time
from rpi_ws281x import *                        #works with python 3.7. sudo pip3 install rpi_ws281x
import math
import random
import logging
import logzero                                  #had to manually install logzero. https://logzero.readthedocs.io/en/latest/
from logzero import logger
import config
import admin

# Setup rotating logfile with 3 rotations, each with a maximum filesize of 1MB:
version = admin.version                         #Software version
loglevel = config.loglevel
loglevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
logzero.loglevel(loglevels[loglevel])           #Choices in order; DEBUG, INFO, WARNING, ERROR
logzero.logfile("/NeoSectional/logfile.log", maxBytes=1e6, backupCount=3)
logger.info("\n\nStartup of wipes-v4.py Script, Version " + version)
logger.info("Log Level Set To: " + str(loglevels[loglevel]))

#Setup for IC238 Light Sensor for LED Dimming, does not need to be commented out if sensor is not used, map will remain at full brightness.
#For more info on the sensor visit; http://www.uugear.com/portfolio/using-light-sensor-module-with-raspberry-pi/
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)  #set mode to BCM and use BCM pin numbering, rather than BOARD pin numbering.
GPIO.setup(4, GPIO.IN)  #set pin 4 as input for light sensor, if one is used. If no sensor used board remains at high brightness always.
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP) #set pin 22 to momentary push button to force FAA Weather Data update if button is used.

#LED strip configuration YOU MUST CHANGE LED_COUNT VALUE TO MATCH YOUR SETUP:
LED_COUNT      = config.LED_COUNT               #Number of LED pixels. Change this value to match the number of LED's being used on map
LED_PIN        = 18                             #GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000                         #LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5                              #DMA channel to use for generating signal (try 5)
LED_INVERT     = False                          #True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0                              #set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB            #Strip type and color ordering
LED_BRIGHTNESS = config.bright_value            #starting brightness. It will be changed below.

#Misc settings
rgb_grb = config.rgb_grb #1 = RGB color codes. 0 = GRB color codes. Populate color codes below with normal RGB codes and script will change it as necessary
metar_age = config.metar_age                    #age of metar to retrieve
wait = config.wait                              #wait time in seconds. .01 typical
rev_rgb_grb = config.rev_rgb_grb                #list of pins whose color code needs to be reversed
morse_msg = config.morse_msg

#Wipe number of times to execute a particular wipe
num_radar = config.num_radar
num_allsame = config.num_allsame
num_circle = config.num_circle
num_square = config.num_square
num_updn = config.num_updn
num_rainbow = config.num_rainbow
num_fade = config.num_fade
num_shuffle = config.num_shuffle
num_morse = config.num_morse
num_rabbit = config.num_rabbit

#Wipe Colors - either random colors or specify an on and off color for each wipe.
rand = config.rand                              #0 = No, 1 = Yes, Randomize the colors used in wipes
black_color = (0,0,0)
radar_color1 = config.radar_color1
radar_color2 = config.radar_color2
allsame_color1 = config.allsame_color1
allsame_color2 = config.allsame_color2
circle_color1 = config.circle_color1
circle_color2 = config.circle_color2
square_color1 = config.square_color1
square_color2 = config.square_color2
updn_color1 = config.updn_color1
updn_color2 = config.updn_color2
fade_color1 = config.fade_color1
shuffle_color1 = config.shuffle_color1
shuffle_color2 = config.shuffle_color2
morse_color1 = config.morse_color1
morse_color2 = config.morse_color2
rabbit_color1 = config.rabbit_color1
rabbit_color2 = config.rabbit_color2

#List definitions
ap_id = []                                      #Airport ID List. Used for screen wipes
latlist = []                                    #Latitude of airport. Used for screen wipes
lonlist = []                                    #Longitude of airport. Used for screen wipes

#Dictionary definitions.
stationiddict = {}
latdict = {}                                    #airport id and its latitude
londict = {}                                    #airport id and its longitude
pindict = {}                                    #Stores airport id and led pin number
apinfodict = {}                                 #Holds pin num as key and a list to include [airport id, lat, lon]

#Morse Code Dictionary
CODE = {'A':'.-', 'B':'-...', 'C':'-.-.', 'D':'-..', 'E':'.', 'F':'..-.', 'G':'--.', 'H':'....',
        'I':'..', 'J':'.---', 'K':'-.-', 'L':'.-..', 'M':'--', 'N':'-.', 'O':'---', 'P':'.--.', 'Q':'--.-',
        'R':'.-.', 'S':'...', 'T':'-', 'U':'..-', 'V':'...-', 'W':'.--', 'X':'-..-', 'Y':'-.--', 'Z':'--..',
        '1':'.----', '2':'..---', '3':'...--', '4':'....-', '5':'.....', '6':'-....', '7':'--...', '8':'---..', '9':'----.',
        '0':'-----', ', ':'--..--', '.':'.-.-.-', '?':'..--..', '/':'-..-.', '-':'-....-', '(':'-.--.', ')':'-.--.-'
       }

#Create an instance of NeoPixel
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
strip.begin()

#Bright light will provide a low state (0) on GPIO. Dark light will provide a high state (1).
#Full brightness will be used if no light sensor is installed.
if GPIO.input(4) == 1:
    LED_BRIGHTNESS = config.dimmed_value
else:
    LED_BRIGHTNESS = config.bright_value
strip.setBrightness(LED_BRIGHTNESS)

#Functions
#Rainbow Animation functions - taken from https://github.com/JJSilva/NeoSectional/blob/master/metar.py
def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbowCycle(strip, iterations, wait=.1):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for led_pin in range(strip.numPixels()):
            if str(led_pin) in nullpins:        #exclude NULL and LGND pins from wipe
                strip.setPixelColor(led_pin, Color(0,0,0))
            else:
                strip.setPixelColor(led_pin, wheel((int(led_pin * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait/100)

#Generate random RGB color
def randcolor():
    r = int(random.randint(0,255))
    g = int(random.randint(0,255))
    b = int(random.randint(0,255))
    return (r,g,b)

#Change color code to work with various led strips. For instance, WS2812 model strip uses RGB where WS2811 model uses GRB
#Set the "rgb_grb" user setting above. 1 for RGB LED strip, and 0 for GRB strip.
#If necessary, populate the list rev_rgb_grb with pin numbers of LED's that use the opposite color scheme.
def rgbtogrb_wipes(led_pin, data, order=0):
    global rev_rgb_grb                          #list of pins that need to use the reverse of the normal order setting.
    if str(led_pin) in rev_rgb_grb:             #This accommodates the use of both models of LED strings on one map.
        order = not order
        logger.debug('Reversing rgb2grb Routine Output for LED PIN ' + str(led_pin))

    red = data[0]
    grn = data[1]
    blu = data[2]

    if order:
        data = [red,grn,blu]
    else:
        data =[grn,red,blu]

    xcolor = Color(data[0], data[1], data[2])
    return xcolor

#range to loop through floats, rather than integers. Used to loop through lat/lons.
def frange(start, stop, step):
    if start != stop:
        i = start
        if i < stop:
            while i < stop:
                yield round(i,2)
                i += step
        else:
            while i > stop:
                yield round(i,2)
                i -= step

#Wipe routines based on Lat/Lons of airports on map.
#Need to pass name of dictionary with coordinates, either latdict or londict
#Also need to pass starting value and ending values to iterate through. These are floats for Lat/Lon. ie. 36.23
#Pass Step value to iterate through the values provided in start and end. Typically needs to be .01
#pass the start color and ending color. Pass a wait time or delay, ie. .01
def wipe(dict_name, start, end, step, color1, color2, wait_mult):
    #Need to find duplicate values (lat/lons) from dictionary using flip technique
    flipped = {}
    for key, value in list(dict_name.items()):  #create a dict where keys and values are swapped
        if value not in flipped:
            flipped[value] = [key]
        else:
            flipped[value].append(key)

    for i in frange(start,end,step):
        key = str(i)

        if key in flipped:                      #Grab latitude from dict
            num_elem = (len(flipped[key]))      #Determine the number of duplicates

            for j in range(num_elem):           #loop through each duplicate to get led number
                id = (flipped[key][j])
                led_pin = ap_id.index(id)       #Assign the pin number to the led to turn on/off

                color = rgbtogrb_wipes(led_pin, color1, rgb_grb)
                strip.setPixelColor(led_pin, color)
                strip.show()
                time.sleep(wait*wait_mult)

                color = rgbtogrb_wipes(led_pin, color2, rgb_grb)
                strip.setPixelColor(led_pin, color)
                strip.show()
                time.sleep(wait*wait_mult)


#Circle wipe
def circlewipe(centerlat, centerlon, color1, color2):
    global apinfodict
    circle_x = centerlon
    circle_y = centerlat
    rad_inc = 4
    rad = rad_inc
    iter = int(sizelat/rad_inc) #attempt to figure number of iterations necessary to cover whole map

    for j in range(iter):
        for key in apinfodict:
            x = float(apinfodict[key][2])
            y = float(apinfodict[key][1])
            led_pin = int(apinfodict[key][0])

            if ((x - circle_x) * (x - circle_x) + (y - circle_y) * (y - circle_y) <= rad * rad):
#               print("Inside")
                color = rgbtogrb_wipes(led_pin, color1, rgb_grb)
            else:
#               print("Outside")
                color = rgbtogrb_wipes(led_pin, color2, rgb_grb)

            strip.setPixelColor(led_pin, color)
            strip.show()
            time.sleep(wait)
        rad = rad + rad_inc

    for j in range(iter):
        rad = rad - rad_inc
        for key in apinfodict:
            x = float(apinfodict[key][2])
            y = float(apinfodict[key][1])
            led_pin = int(apinfodict[key][0])

            if ((x - circle_x) * (x - circle_x) + (y - circle_y) * (y - circle_y) <= rad * rad):
#               print("Inside")
                color = rgbtogrb_wipes(led_pin, color1, rgb_grb)
            else:
#               print("Outside")
                color = rgbtogrb_wipes(led_pin, color2, rgb_grb)

            strip.setPixelColor(led_pin, color)
            strip.show()
            time.sleep(wait)

    allonoff_wipes((0,0,0),.1)


#radar wipe - Needs area calc routines to determine areas of triangles
def area(x1, y1, x2, y2, x3, y3):
    return abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2.0)

def isInside(x1, y1, x2, y2, x3, y3, x, y):
    # Calculate area of triangle ABC
    A = area (x1, y1, x2, y2, x3, y3)
    # Calculate area of triangle PBC
    A1 = area (x, y, x2, y2, x3, y3)
    # Calculate area of triangle PAC
    A2 = area (x1, y1, x, y, x3, y3)
    # Calculate area of triangle PAB
    A3 = area (x1, y1, x2, y2, x, y)
    # Check if sum of A1, A2 and A3 is same as A

    if(((A1 + A2 + A3)-1) >= A <= ((A1 + A2 + A3)+1)):
        return True
    else:
        return False

def radarwipe(centerlat,centerlon,iter,color1,color2,sweepwidth=175,radius=50,angleinc=.05):
    global apinfodict
    PI = 3.141592653
    angle = 0

    for k in range(iter):
        # Calculate the x1,y1 for the end point of our 'sweep' based on
        # the current angle. Then do the same for x2,y2
        x1 = round(radius * math.sin(angle) + centerlon,2)
        y1 = round(radius * math.cos(angle) + centerlat,2)
        x2 = round(radius * math.sin(angle + sweepwidth) + centerlon,2)
        y2 = round(radius * math.cos(angle + sweepwidth) + centerlat,2)

        for key in apinfodict:
            px1 = float(apinfodict[key][2])     #Lon
            py1 = float(apinfodict[key][1])     #Lat
            led_pin = int(apinfodict[key][0])   #LED Pin Num
#           print (centerlon, centerlat, x1, y1, x2, y2, px1, py1, pin) #debug

            if (isInside(centerlon, centerlat, x1, y1, x2, y2, px1, py1)):
#               print('Inside')
                color = rgbtogrb_wipes(led_pin, color1, rgb_grb)
                strip.setPixelColor(led_pin, color)
            else:
                color = rgbtogrb_wipes(led_pin, color2, rgb_grb)
                strip.setPixelColor(led_pin, color)
#               print('Not Inside')
        strip.show()
        time.sleep(wait)

        # Increase the angle by angleinc radians
        angle = angle + angleinc

        # If we have done a full sweep, reset the angle to 0
        if angle > 2 * PI:
            angle = angle - (2 * PI)

#Square wipe
#findpoint in a given rectangle or not.   Example -114.87, 37.07, -109.07, 31.42, -114.4, 32.87
def findpoint(x1, y1, x2, y2, x, y):
    if (x > x1 and x < x2 and y > y1 and y < y2):
        return True
    else:
        return False

def center(max,min):
    z = ((max-min)/2) + min
    return round(z,2)

def squarewipe(minlon, minlat, maxlon, maxlat, iter, color1, color2, step=.5, wait_mult=10):
    global apinfodict
    declon = minlon
    declat = minlat
    inclon = maxlon
    inclat = maxlat
    centlon = (center(maxlon,minlon))
    centlat = (center(maxlat,minlat))

    for j in range(iter):
        for inclon in frange(maxlon, centlon, step):
            #declon, declat = Upper Left of box.
            #inclon, inclat = Lower Right of box
            for key in apinfodict:
                px1 = float(apinfodict[key][2]) #Lon
                py1 = float(apinfodict[key][1]) #Lat
                led_pin = int(apinfodict[key][0]) #LED Pin Num

#                print((declon, declat, inclon, inclat, px1, py1)) #debug
                if findpoint(declon, declat, inclon, inclat, px1, py1):
#                    print('Inside') #debug
                    color = rgbtogrb_wipes(led_pin, color1, rgb_grb)
                else:
#                    print('Not Inside') #debug
                    color = rgbtogrb_wipes(led_pin, color2, rgb_grb)

                strip.setPixelColor(led_pin, color)

            inclat = round(inclat - step,2)
            declon = round(declon + step,2)
            declat = round(declat + step,2)

            strip.show()
            time.sleep(wait*wait_mult)

        for inclon in frange(centlon, maxlon, step):
            #declon, declat = Upper Left of box.
            #inclon, inclat = Lower Right of box
            for key in apinfodict:
                px1 = float(apinfodict[key][2]) #Lon
                py1 = float(apinfodict[key][1]) #Lat
                led_pin = int(apinfodict[key][0]) #LED Pin Num

#                print((declon, declat, inclon, inclat, px1, py1)) #debug
                if findpoint(declon, declat, inclon, inclat, px1, py1):
#                    print('Inside') #debug
                    color = rgbtogrb_wipes(led_pin, color1, rgb_grb)
                else:
#                   print('Not Inside') #debug
                    color = rgbtogrb_wipes(led_pin, color2, rgb_grb)

                strip.setPixelColor(led_pin, color)

            inclat = round(inclat + step,2)
            declon = round(declon - step,2)
            declat = round(declat - step,2)

            strip.show()
            time.sleep(wait*wait_mult)


#Turn on or off all the lights using the same color.
def allonoff_wipes(color1, wait):
    for led_pin in range(strip.numPixels()):
        if str(led_pin) in nullpins:            #exclude NULL and LGND pins from wipe
            strip.setPixelColor(led_pin, Color(0,0,0))
        else:
            color = rgbtogrb_wipes(led_pin, color1, rgb_grb)
            strip.setPixelColor(led_pin, color)
    strip.show()
    time.sleep(wait)

#Fade LED's in and out using the same color.
def fade(color1, wait):
    global LED_BRIGHTNESS

    for val in range(0,LED_BRIGHTNESS,1):       #strip.numPixels()):
        for led_pin in range(strip.numPixels()): #LED_BRIGHTNESS,0,-1):
            if str(led_pin) in nullpins:        #exclude NULL and LGND pins from wipe
                strip.setPixelColor(led_pin, Color(0,0,0))
            else:
                color2 = dimwipe(color1,val)
                color = rgbtogrb_wipes(led_pin, color2, rgb_grb)
                strip.setPixelColor(led_pin, color)
        strip.show()
        time.sleep(wait*.5)

    for val in range(LED_BRIGHTNESS,0,-1):      #strip.numPixels()):
        for led_pin in range(strip.numPixels()): #0,LED_BRIGHTNESS,1):
            if str(led_pin) in nullpins:        #exclude NULL and LGND pins from wipe
                strip.setPixelColor(led_pin, Color(0,0,0))
            else:
                color2 = dimwipe(color1,val)
                color = rgbtogrb_wipes(led_pin, color2, rgb_grb)
                strip.setPixelColor(led_pin, color)
        strip.show()
        time.sleep(wait*.5)
    time.sleep(wait*1)

#Dim LED's
def dimwipe(data,value):
    red = int(data[0] - value)
    if red < 0:
        red = 0

    grn = int(data[1] - value)
    if grn < 0:
        grn = 0

    blu = int(data[2] - value)
    if blu < 0:
        blu = 0

    data =[red,grn,blu]
    return data

#Shuffle LED Wipe
def shuffle(color1, color2, wait):
    l = list(range(strip.numPixels()))
    random.shuffle(l)
    for led_pin in l:
        if str(led_pin) in nullpins:            #exclude NULL and LGND pins from wipe
            strip.setPixelColor(led_pin, Color(0,0,0))
        else:
            color = rgbtogrb_wipes(led_pin, color1, rgb_grb)
            strip.setPixelColor(led_pin, color)
        strip.show()
        time.sleep(wait*1)

    l = list(range(strip.numPixels()))
    random.shuffle(l)
    for led_pin in l:
        if str(led_pin) in nullpins:            #exclude NULL and LGND pins from wipe
            strip.setPixelColor(led_pin, Color(0,0,0))
        else:
            color = rgbtogrb_wipes(led_pin, color2, rgb_grb)
            strip.setPixelColor(led_pin, color)
        strip.show()
        time.sleep(wait*1)

#Morse Code Wipe
#There are rules to help people distinguish dots from dashes in Morse code.
#   The length of a dot is 1 time unit.
#   A dash is 3 time units.
#   The space between symbols (dots and dashes) of the same letter is 1 time unit.
#   The space between letters is 3 time units.
#   The space between words is 7 time units.
def morse(color1,color2,msg,wait):
    #define timing of morse display
    dot_leng = wait * 1
    dash_leng = wait * 3
    bet_symb_leng = wait * 1
    bet_let_leng = wait * 3
    bet_word_leng = wait * 4                    #logic will add bet_let_leng + bet_word_leng = 7

    for char in morse_msg:
        letter = []
        if char.upper() in CODE:
            letter = list(CODE[char.upper()])
            logger.debug(letter) #debug

            for val in letter:                  #display individual dot/dash with proper timing
                if val == '.':
                    delay = dot_leng
                else:
                    delay = dash_leng

                for led_pin in range(strip.numPixels()): #turn LED's on
                    if str(led_pin) in nullpins: #exclude NULL and LGND pins from wipe
                        strip.setPixelColor(led_pin, Color(0,0,0))
                    else:
                        color = rgbtogrb_wipes(led_pin, color1, rgb_grb)
                        strip.setPixelColor(led_pin, color)
                strip.show()
                time.sleep(delay)               #time on depending on dot or dash

                for led_pin in range(strip.numPixels()): #turn LED's off
                    if str(led_pin) in nullpins: #exclude NULL and LGND pins from wipe
                        strip.setPixelColor(led_pin, Color(0,0,0))
                    else:
                        color = rgbtogrb_wipes(led_pin, color2, rgb_grb)
                        strip.setPixelColor(led_pin, color)
                strip.show()
                time.sleep(bet_symb_leng)       #timing between symbols
            time.sleep(bet_let_leng)            #timing between letters

        else: #if character in morse_msg is not part of the Morse Code Alphabet, substitute a '/'
            if char == ' ':
                time.sleep(bet_word_leng)

            else:
                char = '/'
                letter = list(CODE[char.upper()])

                for val in letter:              #display individual dot/dash with proper timing
                    if val == '.':
                        delay = dot_leng
                    else:
                        delay = dash_leng

                    for led_pin in range(strip.numPixels()): #turn LED's on
                        if str(led_pin) in nullpins: #exclude NULL and LGND pins from wipe
                            strip.setPixelColor(led_pin, Color(0,0,0))
                        else:
                            color = rgbtogrb_wipes(led_pin, color1, rgb_grb)
                            strip.setPixelColor(led_pin, color)
                    strip.show()
                    time.sleep(delay)           #time on depending on dot or dash

                    for led_pin in range(strip.numPixels()): #turn LED's off
                        if str(led_pin) in nullpins: #exclude NULL and LGND pins from wipe
                            strip.setPixelColor(led_pin, Color(0,0,0))
                        else:
                            color = rgbtogrb_wipes(led_pin, color2, rgb_grb)
                            strip.setPixelColor(led_pin, color)
                    strip.show()
                    time.sleep(bet_symb_leng)   #timing between symbols

                time.sleep(bet_let_leng)        #timing between letters

    time.sleep(bet_word_leng)

#Rabbit Chase
#Chase the rabbit through string.
def rabbit(color1, color2, wait):
    global LED_BRIGHTNESS

    for led_pin in range(strip.numPixels()):    #turn LED's on
        rabbit = led_pin + 1

        if str(led_pin) in nullpins or str(rabbit) in nullpins: #exclude NULL and LGND pins from wipe
            strip.setPixelColor(led_pin, Color(0,0,0))
            strip.setPixelColor(rabbit, Color(0,0,0))

        else:

            if rabbit < strip.numPixels() and rabbit > 0:
                color = rgbtogrb_wipes(rabbit, color2, rgb_grb)
                strip.setPixelColor(rabbit, color)
                strip.show()

            color = rgbtogrb_wipes(led_pin, color1, rgb_grb)
            strip.setPixelColor(led_pin, color)
            strip.show()
            time.sleep(wait)

    for led_pin in range(strip.numPixels(),-1,-1): #turn led's off
        rabbit = led_pin + 1
        erase_pin = led_pin + 2

        if str(rabbit) in nullpins or str(erase_pin) in nullpins: #exclude NULL and LGND pins from wipe
            strip.setPixelColor(rabbit, Color(0,0,0))
            strip.setPixelColor(erase_pin, Color(0,0,0))
            strip.show()
        else:

            if rabbit < strip.numPixels() and rabbit > 0:
                color = rgbtogrb_wipes(rabbit, color2, rgb_grb)
                strip.setPixelColor(rabbit, color)
                strip.show()

            if erase_pin < strip.numPixels() and erase_pin > 0:
                color = rgbtogrb_wipes(erase_pin, black_color, rgb_grb)
                strip.setPixelColor(erase_pin, color)
                strip.show()
                time.sleep(wait)

    allonoff_wipes(black_color,0)

#Start of executed code
if __name__ == '__main__':
    #read airports file - read each time weather is updated in case a change to "airports" file was made while script was running.
    with open("/NeoSectional/airports") as f:
        airports = f.readlines()
    airports = [x.strip() for x in airports]

    #Define URL to get weather METARS. This will pull only the latest METAR from the last 2.5 hours. If no METAR reported withing the last 2.5 hours, Airport LED will be white.
    url = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&mostRecentForEachStation=constraint&hoursBeforeNow="+str(metar_age)+"&stationString="
#    logger.debug(url)

    #Build URL to submit to FAA with the proper airports from the airports file and populate the pindict dictionary
    i = 0
    nullpins = []
    for airportcode in airports:
        if airportcode == "NULL" or airportcode == "LGND":
            nullpins.append(str(i))
            i += 1
            continue
        url = url + airportcode + ","
        pindict[airportcode] = str(i)           #build a dictionary of the LED pins for each airport used
        i += 1
    logger.debug('Airports = ' + str(airports))
    logger.debug('URL = ' + str(url))
    logger.debug('nullpins = ' + str(nullpins))

    try:                                        #Simple Error trap, in case FAA web site is not responding
        content = urllib.request.urlopen(url).read()
    except:                                     #End of Error trap
        pass

    root = ET.fromstring(content)               #Process XML data returned from FAA

    #grab the airport category, wind speed and various weather from the results given from FAA.
    for metar in root.iter('METAR'):
        stationId = metar.find('station_id').text

        #grab latitude of airport
        if metar.find('latitude') is None: #if weather string is blank, then bypass
#            lat = '0'
            pass
        else:
            lat = metar.find('latitude').text

        #grab longitude of airport
        if metar.find('longitude') is None:     #if weather string is blank, then bypass
#            lon = '0'
            pass
        else:
            lon = metar.find('longitude').text

        if stationId in latdict:
            print ("Duplicate, only saved the first weather")
        else:
            latdict[stationId] = lat            #build latitude dictionary

        if stationId in londict:
            print ("Duplicate, only saved the first weather")
        else:
            londict[stationId] = lon            #build longitude dictionary

        apinfodict[stationId]=[pindict[stationId],lat,lon] #Build Dictionary with structure:{airport id[pin num,lat,lon]}

    logger.debug(apinfodict)
    logger.debug(latdict)
    logger.debug(londict)

    #build necessary lists to find proper Lat/Lons (Try to eliminate and use apinfodict instead)
    for key, value in latdict.items():
        temp = float(value)
        latlist.append(temp)
    logger.debug(latlist)

    for key, value in londict.items():
        temp = float(value)
        lonlist.append(temp)
    logger.debug(lonlist)

    for airportcode in airports:
        ap_id.append(airportcode)
    logger.debug(ap_id)

    #set the maximum and minimum Lat/Lons to constrain area.
    maxlat = max(latlist)                       #Upper bounds of box
    minlat = min(latlist)                       #Lower bounds of box

    maxlon = max(lonlist)                       #Right bounds of box
    minlon = min(lonlist)                       #Left bounds of box

    sizelat = round(abs(maxlat - minlat),2)     #height of box
    sizelon = round(abs(maxlon - minlon),2)     #width of box

    centerlat = round(sizelat/2+minlat,2)       #center y coord of box
    centerlon = round(sizelon/2+minlon,2)       #center x coord of box

    logger.info('maxlat = ' + str(maxlat) + ' minlat = ' + str(minlat) + ' maxlon = ' + str(maxlon) + ' minlon = ' + str(minlon))
    logger.info('sizelat = ' + str(sizelat) + ' sizelon = ' + str(sizelon) + ' centerlat ' + str(centerlat) + ' centerlon = ' + str(centerlon))


    #Start the different wipes. Check to see how many iterations of each. Zero disables the wipe.
    time.sleep(1)                               #pause to give the string of lights a chance get catch up. Used so lights won't hang up.

    #square wipe - provide coord of box and size, iterations, and colors
    if num_square > 0:
        logger.info('Executing Square Wipe')

    for j in range(num_square):
        if rand:
            squarewipe(minlon, minlat, maxlon, maxlat, 1, randcolor(), randcolor())
        else:
            squarewipe(minlon, minlat, maxlon, maxlat, 1, square_color1, square_color2)

    #radar wipe - provide center of map and the number of times to cycle through
    if num_radar > 0:
        logger.info('Executing Radar Wipe')

    for j in range(num_radar):
        if rand:
            radarwipe(centerlat, centerlon, 130, randcolor(), randcolor())
        else:
            radarwipe(centerlat, centerlon, 130, radar_color1, radar_color2)

    #Circle wipe. provide center coordinates, provide inside of circle color then outside of circle.
    if num_circle > 0:
        logger.info('Executing Circle Wipe')

    for j in range(num_circle):
        if rand:
            circlewipe(centerlat, centerlon, randcolor(), randcolor())
        else:
            circlewipe(centerlat, centerlon, circle_color1, circle_color2)

    #Wipe from bottom to top and back, then side to side
    if num_updn > 0:
        logger.info('Executing Up/Down-Side to Side Wipe')

    for j in range(num_updn):
        if rand:
            wipe(latdict, minlat, maxlat, .01, randcolor(), randcolor(), .1)
            wipe(latdict, maxlat, minlat, .01, randcolor(), randcolor(), .1)
            wipe(londict, minlon, maxlon, .01, randcolor(), randcolor(), .1)
            wipe(londict, maxlon, minlon, .01, randcolor(), randcolor(), .1)
        else:
            wipe(latdict, minlat, maxlat, .01, updn_color1, updn_color2, .1)
            wipe(latdict, maxlat, minlat, .01, updn_color1, updn_color2, .1)
            wipe(londict, minlon, maxlon, .01, updn_color1, updn_color2, .1)
            wipe(londict, maxlon, minlon, .01, updn_color1, updn_color2, .1)

    #change colors on whole board
    if num_allsame > 0:
        logger.info('Executing Solid Color Wipe')

    for j in range(num_allsame):
        if rand:
            allonoff_wipes(randcolor(),wait*1000)
        else:
            allonoff_wipes(allsame_color1,wait*1000)

    #Fade colors in and out on whole board
    if num_fade > 0:
        logger.info('Executing Fading Color Wipe')

    for j in range(num_fade):
        if rand:
            fade(randcolor(),wait)
        else:
            fade(fade_color1,wait)

    #shuffle effect
    if num_shuffle > 0:
        logger.info('Executing Shuffle Wipe')

    for j in range(num_shuffle):
        if rand:
            shuffle(randcolor(),randcolor(), wait*10)
        else:
            shuffle(shuffle_color1, shuffle_color2, wait*10)

    #Morse code effect
    if num_morse > 0:
        logger.info('Executing Morse Code Wipe')

    for j in range(num_morse):
        if rand:
            morse(randcolor(),randcolor(), morse_msg, wait*60)
        else:
            morse(morse_color1, morse_color2, morse_msg, wait*60)

    #rainbow effect
    if num_rainbow > 0:
        logger.info('Executing Rainbow Wipe')

    for j in range(num_rainbow):
        rainbowCycle(strip, 2, wait)

    logger.info('Turning Off all LEDs')
#    allonoff_wipes((0,0,0),.1)

    #Rabbit Chase effect
    if num_rabbit > 0:
        logger.info('Executing Rabbit Chase Wipe')

    for j in range(num_rabbit):
        if rand:
            rabbit(randcolor(),randcolor(), wait*10)
        else:
            rabbit(rabbit_color1, rabbit_color2, wait*10)
