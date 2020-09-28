#OLED Test Program - Mark Harris
# Used to test that OLEDs are wired and working properly

import time
from Adafruit_GPIO import I2C
import Adafruit_SSD1306                         #sudo pip3 install Adafruit-SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import smbus2                                   #Install smbus2; sudo pip3 install smbus2
import config

numofdisplays = config.numofdisplays
iterations = 5
dimswitch = 0
ch = 1
fontsize = 24
j = 0

fontindex = 0                                   #Font selected may have various versions that are indexed. 0 = Normal. Leave at 0 unless you know otherwise.
backcolor = 0                                   #0 = Black, background color for OLED display. Shouldn't need to change
fontcolor = 255                                 #255 = White, font color for OLED display. Shouldn't need to change
arrowdir = ''
dimming = dimswitch
toggle = 0
border = 0
offset = 3

#Setup Adafruit library for OLED display.
RST = None
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST) #128x64 or 128x32 - disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
TCA_ADDR = 0x70                                 #use cmd i2cdetect -y 1 to ensure multiplexer shows up at addr 0x70
tca = I2C.get_i2c_device(address=TCA_ADDR)
port = 1                                        #Default port. set to 0 for original RPi or Orange Pi, etc
bus = smbus2.SMBus(port)                        #From smbus2 set bus number

#Functions for OLED display
def tca_select(channel):                        #Used to tell the multiplexer which oled display to send data to.
    #Select an individual channel
    if channel > 7 or numofdisplays < 2:        #Verify we need to use the multiplexer.
        return
    tca.writeRaw8(1 << channel)                 #from Adafruit_GPIO I2C

def oledcenter(txt, ch, font, wndir=0, dim=dimswitch, onoff = 0, pause = 0): #Center text vertically and horizontally
    tca_select(ch)                              #Select the display to write to
#    oleddim(dim)                               #Set brightness, 0 = Full bright, 1 = medium bright, 2 = low brightdef oledcenter(txt): #Center text vertically and horizontally
    draw.rectangle((0, 0, width-1, height-1), outline=border, fill=backcolor) #blank the display
    x1, y1, x2, y2 = 0, 0, width, height        #create boundaries of display

    if wndir == "" or txt == '\n' or 'Updated' in txt or 'Calm' in txt: #Setup and print wind direction arrow
        pass                                    #don't print any arrow in certain conditions

    elif wind_numorarrow == 0:                  #draw wind direction using arrows
        draw.text((96, 37), wndir, font=arrows, fill=fontcolor) #lower right of oled

    else:                                       #draw wind direction using numbers
#        txt = txt + ' @' + str(dir) + chr(176) #chr(176) = degree symbol - '21kts @360' layout
        ap, wndsp = txt.split('\n')
        txt = ap + '\n' + str(dir) + chr(176) + '@' + wndsp #'360@21kts' layout

    w, h = draw.textsize(txt, font=font)        #get textsize of what is to be displayed
    x = (x2 - x1 - w)/2 + x1                    #calculate center for text
    y = (y2 - y1 - h)/2 + y1 - offset

    draw.text((x, y), txt, align='center', font=font, fill=fontcolor) #Draw the text to buffer

#    invertoled(onoff)                          #invert display if set
    disp.image(image)                           #Display image
    disp.display()                              #display text in buffer
    time.sleep(.3)                              #pause long enough to be read

def clearoleddisplays():
    for j in range(numofdisplays):
        tca_select(j)
#               disp.clear()                    #commenting this out sped up the display refresh.
        draw.rectangle((0,0,width-1,height-1), outline=border, fill=backcolor)
        disp.image(image)
        disp.display()

#Executed Code
disp.display()

#Create blank image for drawing.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))         #Make sure to create image with mode '1' for 1-bit color.

#Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

boldfont = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf', fontsize, fontindex)
regfont = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf', fontsize, fontindex)
arrows = ImageFont.truetype('/usr/share/fonts/truetype/misc/Arrows.ttf', fontsize, fontindex)
font = regfont                                  #initialize font to start

clearoleddisplays()

while j < iterations:
    for ch in range(numofdisplays):
        val = 'Test\nOLED ' + str(ch)
        oledcenter(val, ch, font, arrowdir, dimming, toggle) #send airport and winds to proper oled display
    j += 1

    clearoleddisplays()
