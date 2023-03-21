# shutoff.py - by Mark Harris
#     Updated to work with Python 3.7
#     shutoff the LED's and if equipped the Oled display
#     Added Logging capabilities which is stored in /NeoSectional/logfile.log

#import libraries
from rpi_ws281x import * #works with python 3.7. sudo pip3 install rpi_ws281x
import config   #holds user settings shared among scripts
import admin

#OLED libraries
import smbus2
from Adafruit_GPIO import I2C
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
import RPi.GPIO as GPIO
import logging
import logzero
from logzero import logger

#LCD Libraries
import RPLCD as RPLCD
from RPLCD.gpio import CharLCD

# Setup rotating logfile with 3 rotations, each with a maximum filesize of 1MB:
version = admin.version                         #Software version
loglevel = config.loglevel
loglevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
logzero.loglevel(loglevels[loglevel])           #Choices in order; DEBUG, INFO, WARNING, ERROR
logzero.logfile('/NeoSectional/logfile.log', maxBytes=1e6, backupCount=1)
logger.info('\n\nStartup of shutoff.py Script, Version ' + version)
logger.info("Log Level Set To: " + str(loglevels[loglevel]))

# LED strip configuration:
LED_COUNT = config.LED_COUNT                    #from config.py. Number of LED pixels.

LED_PIN        = 18                             #GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000                         #LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5                              #DMA channel to use for generating signal (try 5)#
LED_BRIGHTNESS = 255                            #Set to 0 for darkest and 255 for brightest
LED_INVERT     = False                          #True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0                              #set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB            #Strip type and colour ordering

#Setup Display
lcdused = config.lcddisplay                     #from config.py. 1 = Yes, 0 = No.
oledused = config.oledused                      #from config.py. 1 = Yes, 0 = No.
numofdisplays = config.numofdisplays            #from config.py. Number of OLED displays used.

RST = None                                      #on the PiOLED this pin isnt used
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST) #128x64 or 128x32 - disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
TCA_ADDR = 0x70                                 #use cmd i2cdetect -y 1 to ensure multiplexer shows up at addr 0x70
tca = I2C.get_i2c_device(address=TCA_ADDR)
port = 1                                        #Default port. set to 0 for original RPi or Orange Pi, etc
bus = smbus2.SMBus(port)                        #From smbus2 set bus number
border = 0                                      #Set border to black
backcolor = 0                                   #Set backcolor to black

#Create blank image for drawing.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))         #Make sure to create image with mode '1' for 1-bit color.

#Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

logger.info('Shutoff Settings Loaded')

# Define functions
def turnoff(strip):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0,0,0))
    strip.show()

#Functions for OLED display
def tca_select(channel):
    if channel > 7:
        return
    if numofdisplays == 1:
        return

    tca.writeRaw8(1 << channel)                 #from Adafruit_GPIO I2C

#Initialize library.
def initializeoleds():
    for j in range(numofdisplays):
        tca_select(j)                           #select display to write to
        disp.begin()

def clearoleddisplays():
    for j in range(numofdisplays):
        tca_select(j)
        disp.clear()
        draw.rectangle((0,0,width-1,height-1), outline=border, fill=backcolor)
        disp.image(image)
        disp.display()

# Main program
if __name__ == '__main__':
    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
    # Intialize the library (must be called once before other functions).
    strip.begin()
#    turnoff(strip) 
    logger.info("LED's Have Been Turned Off")

    if oledused:                                #check to see if oleds are used
        initializeoleds()
        clearoleddisplays()
        logger.info('OLED Display Has Been Turned Off')

    if lcdused:                                 #check to see if LCD is displayed
        lcd = CharLCD(numbering_mode=GPIO.BCM, cols=16, rows=2, pin_rs=26, pin_e=19, pins_data=[13, 6, 5 ,11], compat_mode = True)
        lcd.clear()
        logger.info('LCD Display Has Been Turned Off')

    logger.info('shutoff.py Completed')
