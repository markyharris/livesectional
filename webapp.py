#!/usr/bin/env python3
"""

# webapp.py - v4, by Mark Harris. Web Based Configurator for LiveSectional - Using Flask and Python
#     Updated to work with Python 3
#     3 editors for Config.py, Airports, and Heat Map.
#     This version includes color picker
#     This version adds ability to TAB between airport textboxes.
#     Added Logging capabilities which is stored in /NeoSectional/logs/logfile.log
#     Added routine to grab airport details, i.e. City and State to display.
#     Added admin feature that will list IP address of running RPI to ftp server with drop down to pick from.
#     Added ability to load a profile into Settings Editor/
#     Added System Info Page Display
#     Added internet check and recheck if not currently available
#     Added User App to control map that doesn't have a Rotary Switch.
#     Added QR Code generator to help user load app on phone.
#     Fixed bug where the url was getting appended to rather than replaced.
#     Added Web based software update checker and file updater
#     Added import file ability for Airports and Heat Map Data
#     Fixed bug when page is loaded directly from URL box rather than the loaded page.
#     Added menu item to manually check for an update
#     Added menu items to display logfile.log, and console output (requires modified version of seashells
#     Added LiveSectional Web Map, which recreates the builders map online.
#     Fixed bug where get_led_map_info() would not get lat/Lon from XML file.

"""
# print test #force bug to cause webapp.py to error out

# import needed libraries
#    if URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] try;
#    $ sudo update-ca-certificates --fresh
#    $ export SSL_CERT_DIR=/etc/ssl/certs
from datetime import datetime
import time
import os
import sys
import subprocess
import shutil
import zipfile
import json
import urllib.request, urllib.error, urllib.parse
import socket
import logging

import xml.etree.ElementTree as ET

import folium
import folium.plugins
from folium.features import CustomIcon
from folium.features import DivIcon
from folium.vector_layers import Circle, CircleMarker, PolyLine, Polygon, Rectangle

import requests

import wget

#   sudo pip3 install flask
from flask import Flask, render_template, request, flash, redirect, url_for, send_file, Response
from werkzeug.utils import secure_filename

# from neopixel import * # works with python 2.7
from rpi_ws281x import * # works with python 3.7. sudo pip3 install rpi_ws281x
import logzero
from logzero import logger

import confsettings
import utils

import config
import admin
import scan_network

# Setup rotating logfile with 3 rotations, each with a maximum filesize of 1MB:
version = admin.version          # Software version
loglevel = config.loglevel
loglevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
logzero.loglevel(loglevels[loglevel])  # Choices in order; DEBUG, INFO, WARNING, ERROR
logzero.logfile("/NeoSectional/logs/logfile.log", maxBytes=1e6, backupCount=3)
logger.info("\n\nStartup of metar-v4.py Script, Version " + version)
logger.info("Log Level Set To: " + str(loglevels[loglevel]))

# setup variables
# useip2ftp = admin.use_ftp           
# OBSOLETE 0 = No, 1 = Yes. Use IP to FTP for multiple boards 
#  on local network admin.
#
# Moved to config statement
## airports_file = '/NeoSectional/data/airports'
#
# airports_bkup = '/NeoSectional/airports-bkup'
settings_file = '/NeoSectional/config.py'
settings_bkup = '/NeoSectional/config-bkup.py'
# heatmap_file = '/NeoSectional/data/hmdata'
settings = {}
airports = []
hmdata = []
datalist = []
newlist = []
ipaddresses = []
current_timezone = ''
loc = {}
machines = []
lat_list = []
lon_list = []
max_lat = ''
min_lat = ''
max_lon = ''
min_lon = ''

# Settings for web based file updating
src = '/NeoSectional'                           # Main directory, /NeoSectional
dest = '../previousversion'                     # Directory to store currently run version of software
verfilename = 'version.py'                      # Version Filename
zipfilename = 'ls.zip'                          # File that holds the names of all the files that need to be updated
source_path = 'http://www.livesectional.com/liveupdate/neoupdate/'
target_path = '/NeoSectional/'
update_available = 0                            # 0 = No update available, 1 = Yes update available
update_vers = "4.000"                           # initiate variable

# Used to capture staton information for airport id decode for tooltip display in web pages.
apinfo_dict = {}
orig_apurl = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=stations&requestType=retrieve&format=xml&stationString="
logger.debug(orig_apurl)

#Used to display weather and airport locations on a map
led_map_dict = {}
led_map_url = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=2.5&mostRecentForEachStation=constraint&stationString="
logger.debug(led_map_url)

# LED strip configuration:
LED_COUNT      = 500            # Max Number of LED pixels.
LED_PIN        = 18             # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000         # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5              # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255            # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False          # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0              # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_RGB   # Strip type and colour ordering

# instantiate strip
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
strip.begin()

# misc variables
color = Color(255,255,255)      # Color to display when cycling through LED's. White is the default.
black_color = Color(0,0,0)      # Color Black used to turn off the LED.
num = 0
now = datetime.now()
loc_timestr = (now.strftime("%H:%M:%S - %b %d, %Y"))
logger.debug(loc_timestr)
delay_time = 5                  # Delay in seconds between checking for internet availablility.
num = 0                         # initialize num for airports editor
ipadd = ''

# Initiate flash session
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

logger.info("Settings and Flask Have Been Setup")


##########
# Routes #
##########

# Routes for Map Display - Testing
@app.route('/map1', methods=["GET", "POST"])
def map1():
    """Flask Route: /map1"""
    start_coords = (35.1738, -111.6541)
    folium_map = folium.Map(location=start_coords, \
      zoom_start = 6, height='80%', width='100%', \
      control_scale = True, \
      zoom_control = True, \
      tiles = 'OpenStreetMap')

    folium_map.add_child(folium.LatLngPopup())
    folium_map.add_child(folium.ClickForMarker(popup='Marker'))
    folium.plugins.Geocoder().add_to(folium_map)

    folium.TileLayer('http://wms.chartbundle.com/tms/1.0.0/sec/{z}/{x}/{y}.png?origin=nw', \
            attr='chartbundle.com', name='ChartBundle Sectional').add_to(folium_map)
    folium.TileLayer('Stamen Terrain', name='Stamen Terrain').add_to(folium_map)
    folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(folium_map)
    # other mapping code (e.g. lines, markers etc.)
    folium.LayerControl().add_to(folium_map)

    folium_map.save('../../NeoSectional/templates/map.html')
    return render_template('mapedit.html', title='Map', num = 5)
#    return folium_map._repr_html_()


@app.route('/touchscr', methods=["GET", "POST"])
def touchscr():
    """Flask Route: /touchscr - Touch Screen template"""
    return render_template('touchscr.html', title = 'Touch Screen', num = 5, machines = machines, ipadd = ipadd)


# Route to open live console display window using seashells dependency - TESTING
# Uses the dependency, 'seashells' to display console data to web page. Follow the steps at
# https://seashells.io/ to install. THEN MUST ADD THE FOLLOWING CODE to copy seashell url to file.
# AT FILE LOCATION; sudo nano -c /usr/local/lib/python3.7/dist-packages/seashells/__init__.py
# On line 50 add this to the parser routine
#        parser.add_argument('-s', '--script', type=str, default='webapp',
#            help='Capture console stream from livesectional')
#
# On line 96 add this routine
#        # write ip address to file - Mark Harris
#        ipadd = data.decode()
#        ipadd = ipadd[11:]
#        script_name = args.script
#        if script_name == 'webapp':
#            f = open("/NeoSectional/data/console_ip.txt", "w")
#            f.write(script_name + " " + ipadd)
#            f.close()
@app.route('/open_console', methods=["GET", "POST"])
def open_console():
    """Flask Route: /open_console - Launching Console in discrete window"""
    console_ips = []
    with open("/NeoSectional/data/console_ip.txt", "r") as file:
        for line in (file.readlines() [-1:]):
            line = line.rstrip()
            console_ips.append(line)
    logger.info("Opening open_console in separate window")
    return render_template('open_console.html', urls = console_ips, title = 'Display Console Output-'+version, num = 5, machines = machines, ipadd = ipadd, timestr = loc_timestr)


# Routes to display logfile live, and hopefully for a dashboard
@app.route('/stream_log', methods=["GET", "POST"])
def stream_log():
    """Flask Route: /stream_log - Watch logs live"""
    global ipadd
    global loc_timestr
    logger.info("Opening stream_log in separate window")
    return render_template('stream_log.html', title = 'Display Logfile-'+version, num = 5, machines = machines, ipadd = ipadd, timestr = loc_timestr)


@app.route('/stream_log1', methods=["GET", "POST"]) # Alternate route. Not currently used
def stream_log1():
    """Flask Route: /stream_log1 - UNUSED ALTERNATE LOGS ROUTE"""
    def generate():
        with open('/NeoSectional/logs/logfile.log') as f:
            while True:
                yield "{}\n".format(f.read())
                time.sleep(1)

    return app.response_class(generate(), mimetype='text/plain')


# Route to manually check for update using menu item
@app.route('/test_for_update', methods=["GET", "POST"])
def test_for_update():
    """Flask Route: /test_for_update - Run new software update checks"""
    global update_available
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  # Use index if called from URL and not page.

    temp = url.split('/')

    testupdate()

    if update_available == 0:
        flash('No Update Available')

    elif update_available == 1:
        flash('UPDATE AVAILABLE, Use Map Utilities to Update')

    else:
        flash('New Image Available -  Use Map Utilities to Download')

    logger.info('Checking to see if there is an update available')
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Route to update Software if one is available and user chooses to update
@app.route('/update_info', methods=["GET", "POST"])
def update_info():
    """Flask Route: /update_info - Display Software Updates"""
    global ipadd
    global loc_timestr
    with open("/NeoSectional/update_info.txt","r") as file:
        content = file.readlines()
        logger.debug(content)
    return render_template("update_info.html", content = content, title = 'Update Info-'+version, num = 5, machines = machines, ipadd = ipadd, timestr = loc_timestr)


@app.route('/update', methods=["GET", "POST"])
def update():
    """Flask Route: /update - Execute Update for files"""
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  # Use index if called from URL and not page.

    temp = url.split('/')
    updatefiles()
    flash('Software has been updated to v' + update_vers)
    logger.info('Updated Software to version ' + update_vers)
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


@app.route('/update_page', methods=["GET", "POST"])
def update_page():
    """Flask Route: /update_page"""
    global ipadd
    global loc_timestr
    return render_template("update_page.html", title = 'Software Update Information-'+version, num = 5, machines = machines, ipadd = ipadd, timestr = loc_timestr)


# Route to display map's airports on a digital map.
@app.route('/led_map', methods=["GET", "POST"])
def led_map():
    """Flask Route: /led_map - Display LED Map showing existing airports on MAP"""
    global hmdata
    global airports
    global led_map_dict
    global settings
    global strip
    global num
    global ipadd
    global strip
    global ipaddresses
    global loc_timestr
    global version
    global current_timezone

    templateData = {
        'title': 'LiveSectional Map-'+version,
        'hmdata': hmdata,
        'airports': airports,
        'settings': settings,
        'ipadd': ipadd,
        'strip': strip,
        'ipaddresses': ipaddresses,
        'timestr': loc_timestr,
        'num': num,
        'apinfo_dict': apinfo_dict,
        'led_map_dict': led_map_dict,
        'version': version,
        'update_available': update_available,
        'update_vers': update_vers,
        'current_timezone': current_timezone,
        'machines': machines,
        'max_lat': max_lat,
        'min_lat': min_lat,
        'max_lon': max_lon,
        'min_lon': min_lon,
        }

    # Update flight categories
    get_led_map_info()

    points = []
    title_coords = (max_lat,(float(max_lon)+float(min_lon))/2)
    start_coords = ((float(max_lat)+float(min_lat))/2, (float(max_lon)+float(min_lon))/2)

    # Initialize Map
    folium_map = folium.Map(location=start_coords, \
      zoom_start = 5, height='100%', width='100%', \
      control_scale = True, \
      zoom_control = True, \
      tiles = 'OpenStreetMap')

    # Place map within bounds of screen
    folium_map.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    # Set Marker Color by Flight Category
    for j,led_ap in enumerate(led_map_dict):
        if led_map_dict[led_ap][2] == "VFR":
            loc_color = 'green'
        elif led_map_dict[led_ap][2] == "MVFR":
            loc_color = 'blue'
        elif led_map_dict[led_ap][2] == "IFR":
            loc_color = 'red'
        elif led_map_dict[led_ap][2] == "LIFR":
            loc_color = 'violet'
        else:
            loc_color = 'black'

        # Get Pin Number to display in popup
        if led_ap in airports:
            pin_num = airports.index(led_ap)
        else:
            pin_num = None

        pop_url = '<a href="https://nfdc.faa.gov/nfdcApps/services/ajv5/airportDisplay.jsp?airportId='+led_ap+'"target="_blank">'
        popup = pop_url+"<b>"+led_ap+"</b><br>"+apinfo_dict[led_ap][0]+',&nbsp'+apinfo_dict[led_ap][1]\
                +"</a><br>Pin&nbspNumber&nbsp=&nbsp"+str(pin_num)+"<br><b><font size=+2 color="+loc_color+">"+led_map_dict[led_ap][2]+"</font></b>"

        # Add airport markers with proper color to denote flight category
        folium.CircleMarker(
            radius=7,
            fill=True,
            color=loc_color,
            location=[led_map_dict[led_ap][0], led_map_dict[led_ap][1]],
            popup=popup,
            tooltip=str(led_ap)+"<br>Pin "+str(pin_num),
            weight=6,
        ).add_to(folium_map)


#    Custom Icon Code - Here for possible future use
#    url = "../../NeoSectional/static/{}".format
#    icon_image = url("dot1.gif")

#    icon = CustomIcon(
#        icon_image,
#        icon_size=(48, 48),
#    )

#    marker = folium.Marker(
#        location=[45.3288, -121.6625], icon=icon, popup="Mt. Hood Meadows"
#    )

#    folium_map.add_child(marker)


    # Add lines between airports. Must make lat/lons floats otherwise recursion error occurs.
    for pin_ap in airports:
        if pin_ap in led_map_dict:
            pin_index = airports.index(pin_ap)
            points.insert(pin_index, [float(led_map_dict[pin_ap][0]), float(led_map_dict[pin_ap][1])])

    logger.debug(points)
    folium.PolyLine(points, color='grey', weight=2.5, opacity=1, dash_array='10').add_to(folium_map)

    # Add Title to the top of the map
    folium.map.Marker(
        title_coords,
        icon=DivIcon(
            icon_size=(500,36),
            icon_anchor=(150,64),
            html='<div style="font-size: 24pt"><b>LiveSectional Map Layout</b></div>',
            )
        ).add_to(folium_map)

    # Extra features to add if desired
    folium_map.add_child(folium.LatLngPopup())
#    folium.plugins.Terminator().add_to(folium_map)
#    folium_map.add_child(folium.ClickForMarker(popup='Marker'))
    folium.plugins.Geocoder().add_to(folium_map)

    folium.plugins.Fullscreen(
        position="topright",
        title="Full Screen",
        title_cancel="Exit Full Screen",
        force_separate_button=True,
    ).add_to(folium_map)

    folium.TileLayer('http://wms.chartbundle.com/tms/1.0.0/sec/{z}/{x}/{y}.png?origin=nw', attr='chartbundle.com', name='ChartBundle Sectional').add_to(folium_map)
    folium.TileLayer('Stamen Terrain', name='Stamen Terrain').add_to(folium_map)
    folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(folium_map)

    folium.LayerControl().add_to(folium_map)

    folium_map.save('../../NeoSectional/templates/map.html')
    logger.info("Opening led_map in separate window")
    return render_template('led_map.html', **templateData)


# Route to expand RPI's file system.
# @app.route('/expandfs', methods=["GET", "POST"])
# def expandfs():
#     global hmdata
#     global airports
#     global settings
#     global strip
#     global num
#     global ipadd
#     global strip
#     global ipaddresses
#     global timestr
#     global version
#     global current_timezone
#
#     if request.method == "POST":
#         os.system('sudo raspi-config --expand-rootfs')
#         flash('File System has been expanded')
#         flash('NOTE: Select "Reboot RPI" from "Map Functions" Menu for changes to take affect')
#
#         return redirect('expandfs')
#
#     else:
#         templateData = {
#             'title': 'Expand File System-'+version,
#             'hmdata': hmdata,
#             'airports': airports,
#             'settings': settings,
#             'ipadd': ipadd,
#             'strip': strip,
#             'ipaddresses': ipaddresses,
#             'num': num,
#             'apinfo_dict': apinfo_dict,
#             'timestr': loc_timestr,
#             'version': version,
#             'update_available': update_available,
#             'update_vers': update_vers,
#             'current_timezone': current_timezone,
#             'machines': machines
#             }
#         logger.info("Opening expand file system page")
#         return render_template('expandfs.html', **templateData)


# Route to display and change Time Zone information.
@app.route('/tzset', methods=["GET", "POST"])
def tzset():
    """Flask Route: /tzset - Display and Set Timezone Information"""
    global hmdata
    global airports
    global settings
    global strip
    global num
    global ipadd
    global strip
    global ipaddresses
    global loc_timestr
    global version
    global current_timezone

    loc_now = datetime.now()
    loc_timestr = (loc_now.strftime("%H:%M:%S - %b %d, %Y"))
    loc_currtzinfolist = []

    if request.method == "POST":
        timezone = request.form['tzselected']
        flash('Timezone set to ' + timezone)
        flash('NOTE: Select "Reboot RPI" from "Map Functions" Menu for changes to take affect')
        os.system('sudo timedatectl set-timezone ' + timezone)
        return redirect('tzset')

    tzlist = subprocess.run(['timedatectl', 'list-timezones'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    tzoptionlist = tzlist.split()

    loc_currtzinfo = subprocess.run(['timedatectl', 'status'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    loc_tztemp = loc_currtzinfo.split('\n')
    for j in range(len(loc_tztemp)):
        if j==0 or j==1 or j==3:
            loc_currtzinfolist.append(loc_tztemp[j])
    current_timezone = loc_tztemp[3]

    templateData = {
            'title': 'Timezone Set-'+version,
            'hmdata': hmdata,
            'airports': airports,
            'settings': settings,
            'ipadd': ipadd,
            'strip': strip,
            'ipaddresses': ipaddresses,
            'timestr': loc_timestr,
            'num': num,
            'apinfo_dict': apinfo_dict,
            'version': version,
            'update_available': update_available,
            'update_vers': update_vers,
            'tzoptionlist': tzoptionlist,
            'currtzinfolist': loc_currtzinfolist,
            'current_timezone': current_timezone,
            'machines': machines
            }

    logger.info("Opening Time Zone Set page")
    return render_template('tzset.html', **templateData)


# Route to display system information.
@app.route('/yield')
def yindex():
    """Flask Route: /yield - Display System Info"""
    def inner():
        proc = subprocess.Popen(
            ['/NeoSectional/info-v4.py'],             # 'dmesg' call something with a lot of output so we can see it
            shell=True,
            stdout=subprocess.PIPE
        )

        for line in iter(proc.stdout.readline,b''):
            time.sleep(.01)                           # Don't need this just shows the text streaming
            line = line.decode("utf-8")
            yield line.strip() + '<br/>\n'

    logger.info("Opening yeild to display system info in separate window")
    return Response(inner(), mimetype='text/html')  # text/html is required for most browsers to show this info.


# Route to create QR Code to display next to map so user can use an app to control the map
@app.route('/qrcode', methods=["GET", "POST"])
def qrcode():
    """Flask Route: /qrcode - Generate QRcode for site URL"""
    global ipadd
    qraddress = 'http://' + ipadd.strip() + ':5000/lsremote'
    logger.info("Opening qrcode in separate window")
    return render_template('qrcode.html', qraddress = qraddress)


#Routes for homepage
@app.route('/', methods=["GET", "POST"])
@app.route('/index', methods=["GET", "POST"])
def index ():
    """Flask Route: / and /index - Homepage"""
    global hmdata
    global airports
    global settings
    global strip
    global num
    global ipadd
    global strip
    global ipaddresses
    global loc_timestr
    global version

    loc_now = datetime.now()
    loc_timestr = (loc_now.strftime("%H:%M:%S - %b %d, %Y"))

    templateData = {
            'title': 'LiveSectional Home-'+version,
            'hmdata': hmdata,
            'airports': airports,
            'settings': settings,
            'ipadd': ipadd,
            'strip': strip,
            'ipaddresses': ipaddresses,
            'timestr': loc_timestr,
            'num': num,
            'apinfo_dict': apinfo_dict,
            'current_timezone': current_timezone,
            'update_available': update_available,
            'update_vers': update_vers,
            'version': version,
            'machines': machines
            }

#    flash(machines) # Debug
    logger.info("Opening Home Page/Index")
    return render_template('index.html', **templateData)


# Routes to download airports, logfile.log and config.py to local computer
@app.route('/download_ap', methods=["GET", "POST"])
def downloadairports ():
    """Flask Route: /download_ap - Export airports file"""
    logger.info("Downloaded Airport File")
    path = "data/airports"
    return send_file(path, as_attachment=True)


@app.route('/download_cf', methods=["GET", "POST"])
def downloadconfig ():
    """Flask Route: /download_cf - Export configuration file"""
    logger.info("Downloaded Config File")
    path = "config.ini"
    return send_file(path, as_attachment=True)


@app.route('/download_log', methods=["GET", "POST"])
def downloadlog ():
    """Flask Route: /download_log - Export log file"""
    logger.info("Downloaded Logfile")
    path = "logs/logfile.log"
    return send_file(path, as_attachment=True)


@app.route('/download_hm', methods=["GET", "POST"])
def downloadhm ():
    """Flask Route: /download_hm - Export heatmap data file"""
    logger.info("Downloaded Heat Map data file")
    path = "data/hmdata"
    return send_file(path, as_attachment=True)


# Routes for Heat Map Editor
@app.route("/hmedit", methods=["GET", "POST"])
def hmedit():
    """Flask Route: /hmedit - Heat Map Editor"""
    logger.info("Opening hmedit.html")
    global strip
    global num
    global ipadd
    global strip
    global ipaddresses
    global loc_timestr
    loc_now = datetime.now()
    loc_timestr = (loc_now.strftime("%H:%M:%S - %b %d, %Y"))

    readhmdata(confsettings.get_string("filenames","heatmap_file"))  # read Heat Map data file

    logger.debug(ipadd)  # debug to display ip address on console

    templateData = {
            'title': 'Heat Map Editor-'+version,
            'hmdata': hmdata,
            'ipadd': ipadd,
            'strip': strip,
            'ipaddresses': ipaddresses,
            'timestr': loc_timestr,
            'num': num,
            'current_timezone': current_timezone,
            'update_available': update_available,
            'update_vers': update_vers,
            'apinfo_dict': apinfo_dict,
            'machines': machines
            }
    return render_template('hmedit.html', **templateData)


@app.route("/hmpost", methods=["GET", "POST"])
def handle_hmpost_request():
    """Flask Route: /hmpost - Upload HeatMap Data"""
    logger.info("Saving Heat Map Data File")
    global hmdata
    global strip
    global num
    global ipadd
    global ipaddresses
    global loc_timestr
    loc_newlist = []

    if request.method == "POST":
        data = request.form.to_dict()
        logger.debug(data)  # debug

        j = 0
        for key in data:
            value = data.get(key)

            if value == '':
                value = '0'

            loc_newlist.append(airports[j] + " " + value)
            j += 1

        writehmdata(loc_newlist, confsettings.get_string("filenames","heatmap_file"))
        get_apinfo()

    flash('Heat Map Data Successfully Saved')
    return redirect("hmedit")


# Import a file to populate Heat Map Data. Must Save Airports to keep
@app.route("/importhm", methods=["GET", "POST"])
def importhm():
    """Flask Route: /importhm - Importing Heat Map"""
    logger.info("Importing Heat Map File")
    global ipaddresses
    global airports
    global loc_timestr
    global hmdata
    hmdata = []

    if 'file' not in request.files:
        flash('No File Selected')
        return redirect('./hmedit')

    file = request.files['file']

    if file.filename == '':
        flash('No File Selected')
        return redirect('./hmedit')

    filedata = file.read()
    tmphmdata = bytes.decode(filedata)
    logger.debug(tmphmdata)
    hmdata = tmphmdata.split('\n')
    hmdata.pop()
    logger.debug(hmdata)

    templateData = {
            'title': 'Heat Map Editor-'+version,
            'hmdata': hmdata,
            'ipadd': ipadd,
            'strip': strip,
            'ipaddresses': ipaddresses,
            'timestr': loc_timestr,
            'num': num,
            'current_timezone': current_timezone,
            'update_available': update_available,
            'update_vers': update_vers,
            'apinfo_dict': apinfo_dict,
            'machines': machines
            }
    flash('Heat Map Imported - Click "Save Heat Map File" to save')
    return render_template("hmedit.html", **templateData)


# Routes for Airport Editor
@app.route("/apedit", methods=["GET", "POST"])
def apedit():
    """Flask Route: /apedit - Airport Editor"""
    logger.info("Opening apedit.html")
    global airports
    global strip
    global num
    global ipadd
    global strip
    global ipaddresses
    global loc_timestr
    loc_now = datetime.now()
    loc_timestr = (loc_now.strftime("%H:%M:%S - %b %d, %Y"))

    readairports(confsettings.get_string("filenames","airports_file"))  # Read airports file.

    logger.debug(ipadd)  # debug to display ip address on console

    templateData = {
            'title': 'Airports Editor-'+version,
            'airports': airports,
            'ipadd': ipadd,
            'strip': strip,
            'ipaddresses': ipaddresses,
            'timestr': loc_timestr,
            'num': num,
            'current_timezone': current_timezone,
            'update_available': update_available,
            'update_vers': update_vers,
            'apinfo_dict': apinfo_dict,
            'machines': machines
            }
    return render_template('apedit.html', **templateData)


@app.route("/numap", methods=["GET", "POST"])
def numap():
    """Flask Route: /numap"""
    logger.info("Updating Number of Airports in airport file")
    global ipaddresses
    global airports
    global loc_timestr

    if request.method == "POST":
        loc_numap = int(request.form["numofap"])
        print (loc_numap)

    readairports(confsettings.get_string("filenames","airports_file"))

    newnum = loc_numap - int(len(airports))
    if newnum < 0:
        airports = airports[:newnum]
    else:
        for n in range(len(airports), loc_numap):
            airports.append("NULL")

    templateData = {
            'title': 'Airports Editor-'+version,
            'airports': airports,
            'ipadd': ipadd,
            'strip': strip,
            'ipaddresses': ipaddresses,
            'timestr': loc_timestr,
            'num': num,
            'current_timezone': current_timezone,
            'update_available': update_available,
            'update_vers': update_vers,
            'apinfo_dict': apinfo_dict,
            'machines': machines
            }

    flash('Number of LEDs Updated - Click "Save Airports" to save.')
    return render_template('apedit.html', **templateData)


@app.route("/appost", methods=["GET", "POST"])
def handle_appost_request():
    """Flask Route: /appost"""
    logger.info("Saving Airport File")
    global airports
    global hmdata
    global strip
    global num
    global ipadd
    global ipaddresses
    global loc_timestr

    if request.method == "POST":
        data = request.form.to_dict()
        logging.debug(data)  # debug
        writeairports(data, confsettings.get_string("filenames","airports_file"))

        readairports(confsettings.get_string("filenames","airports_file"))
        get_apinfo()  # decode airports to get city and state to display

        # update size and data of hmdata based on saved airports file.
        readhmdata(confsettings.get_string("filenames","heatmap_file"))  # get heat map data to update with newly edited airports file
        if len(hmdata) > len(airports):  # adjust size of hmdata list if length is larger than airports
            num = len(hmdata) - len(airports)
            hmdata = hmdata[:-num]

        elif len(hmdata) < len(airports):  # adjust size of hmdata list if length is smaller than airports
            for n in range(len(hmdata), len(airports)):
                hmdata.append('NULL 0')

        for loc_index, airport in enumerate(airports):  # now that both lists are same length, be sure the data matches
            ap, *_ = hmdata[loc_index].split()
            if ap != airport:
                hmdata[loc_index] = (airport + ' 0')  # save changed airport and assign zero landings to it in hmdata
        writehmdata(hmdata, confsettings.get_string("filenames","heatmap_file"))

    flash('Airports Successfully Saved')
    return redirect("apedit")


@app.route("/ledonoff", methods=["GET", "POST"])
def ledonoff():
    """Flask Route: /ledonoff"""
    logger.info("Controlling LED's on/off")
    global airports
    global strip
    global num
    global ipadd
    global ipaddresses
    global loc_timestr

    if request.method == "POST":

        readairports(confsettings.get_string("filenames","airports_file"))

        if "buton" in request.form:
            num = int(request.form['lednum'])
            logger.info("LED " + str(num) + " On")
            strip.setPixelColor(num, Color(155,155,155))
            strip.show()
            flash('LED ' + str(num) + ' On')

        elif "butoff" in request.form:
            num = int(request.form['lednum'])
            logger.info("LED " + str(num) + " Off")
            strip.setPixelColor(num, Color(0,0,0))
            strip.show()
            flash('LED ' + str(num) + ' Off')

        elif "butup" in request.form:
            logger.info("LED UP")
            num = int(request.form['lednum'])
            strip.setPixelColor(num, Color(0,0,0))
            num = num + 1

            if num > len(airports):
                num = len(airports)

            strip.setPixelColor(num, Color(155,155,155))
            strip.show()
            flash('LED ' + str(num) + ' should be On')

        elif "butdown" in request.form:
            logger.info("LED DOWN")
            num = int(request.form['lednum'])
            strip.setPixelColor(num, Color(0,0,0))

            num = num - 1
            if num < 0:
                num = 0

            strip.setPixelColor(num, Color(155,155,155))
            strip.show()
            flash('LED ' + str(num) + ' should be On')

        elif "butall" in request.form:
            logger.info("LED All ON")
            num = int(request.form['lednum'])

            for num in range(len(airports)):
                strip.setPixelColor(num, Color(155,155,155))
            strip.show()
            flash('All LEDs should be On')
            num=0

        elif "butnone" in request.form:
            logger.info("LED All OFF")
            num = int(request.form['lednum'])

            for num in range(len(airports)):
                strip.setPixelColor(num, Color(0,0,0))
            strip.show()
            flash('All LEDs should be Off')
            num=0

        else:  # if tab is pressed
            logger.info("LED Edited")
            num = int(request.form['lednum'])
            flash('LED ' + str(num) + ' Edited')

    templateData = {
            'title': 'Airports File Editor-'+version,
            'airports': airports,
            'ipadd': ipadd,
            'strip': strip,
            'ipaddresses': ipaddresses,
            'timestr': loc_timestr,
            'num': num,
            'update_available': update_available,
            'update_vers': update_vers,
            'apinfo_dict': apinfo_dict,
            'machines': machines
            }

    return render_template("apedit.html", **templateData)


# Import a file to populate airports. Must Save Airports to keep
@app.route("/importap", methods=["GET", "POST"])
def importap():
    """Flask Route: /importap - Import Airports File"""
    logger.info("Importing Airports File")
    global ipaddresses
    global airports
    global loc_timestr

    if 'file' not in request.files:
        flash('No File Selected')
        return redirect('./apedit')

    file = request.files['file']

    if file.filename == '':
        flash('No File Selected')
        return redirect('./apedit')

    filedata = file.read()
    fdata = bytes.decode(filedata)
    logger.debug(fdata)
    airports = fdata.split('\n')
    airports.pop()
    logger.debug(airports)

    templateData = {
            'title': 'Airports Editor-'+version,
            'airports': airports,
            'ipadd': ipadd,
            'strip': strip,
            'ipaddresses': ipaddresses,
            'timestr': loc_timestr,
            'num': num,
            'current_timezone': current_timezone,
            'update_available': update_available,
            'update_vers': update_vers,
            'apinfo_dict': apinfo_dict,
            'machines': machines
            }
    flash('Airports Imported - Click "Save Airports" to save')
    return render_template("apedit.html", **templateData)


# Routes for Config Editor
@app.route("/confedit", methods=["GET", "POST"])
def confedit():
    """Flask Route: /confedit - Configuration Editor"""
    logger.info("Opening confedit.html")
    global ipaddresses
    global ipadd
    global loc_timestr
    global settings

    loc_now = datetime.now()
    loc_timestr = (loc_now.strftime("%H:%M:%S - %b %d, %Y"))

    logger.debug(ipadd)  # debug

    # change rgb code to hex for html color picker
    color_vfr_hex = rgb2hex(settings["color_vfr"])
    color_mvfr_hex = rgb2hex(settings["color_mvfr"])
    color_ifr_hex = rgb2hex(settings["color_ifr"])
    color_lifr_hex = rgb2hex(settings["color_lifr"])
    color_nowx_hex = rgb2hex(settings["color_nowx"])
    color_black_hex = rgb2hex(settings["color_black"])
    color_lghtn_hex = rgb2hex(settings["color_lghtn"])
    color_snow1_hex = rgb2hex(settings["color_snow1"])
    color_snow2_hex = rgb2hex(settings["color_snow2"])
    color_rain1_hex = rgb2hex(settings["color_rain1"])
    color_rain2_hex = rgb2hex(settings["color_rain2"])
    color_frrain1_hex = rgb2hex(settings["color_frrain1"])
    color_frrain2_hex = rgb2hex(settings["color_frrain2"])
    color_dustsandash1_hex = rgb2hex(settings["color_dustsandash1"])
    color_dustsandash2_hex = rgb2hex(settings["color_dustsandash2"])
    color_fog1_hex = rgb2hex(settings["color_fog1"])
    color_fog2_hex = rgb2hex(settings["color_fog2"])
    color_homeport_hex = rgb2hex(settings["color_homeport"])

    # color picker for transitional wipes
    fade_color1_hex = rgb2hex(settings["fade_color1"])
    allsame_color1_hex = rgb2hex(settings["allsame_color1"])
    allsame_color2_hex = rgb2hex(settings["allsame_color2"])
    shuffle_color1_hex = rgb2hex(settings["shuffle_color1"])
    shuffle_color2_hex = rgb2hex(settings["shuffle_color2"])
    radar_color1_hex = rgb2hex(settings["radar_color1"])
    radar_color2_hex = rgb2hex(settings["radar_color2"])
    circle_color1_hex = rgb2hex(settings["circle_color1"])
    circle_color2_hex = rgb2hex(settings["circle_color2"])
    square_color1_hex = rgb2hex(settings["square_color1"])
    square_color2_hex = rgb2hex(settings["square_color2"])
    updn_color1_hex = rgb2hex(settings["updn_color1"])
    updn_color2_hex = rgb2hex(settings["updn_color2"])
    morse_color1_hex = rgb2hex(settings["morse_color1"])
    morse_color2_hex = rgb2hex(settings["morse_color2"])
    rabbit_color1_hex = rgb2hex(settings["rabbit_color1"])
    rabbit_color2_hex = rgb2hex(settings["rabbit_color2"])
    checker_color1_hex = rgb2hex(settings["checker_color1"])
    checker_color2_hex = rgb2hex(settings["checker_color2"])

    # Pass data to html document
    templateData = {
            'title': 'Settings Editor-'+version,
            'settings': settings,
            'ipadd': ipadd,
            'ipaddresses': ipaddresses,
            'timestr': loc_timestr,
            'num': num,
            'current_timezone': current_timezone,
            'update_available': update_available,
            'update_vers': update_vers,
            'machines': machines,

            # Color Picker Variables to pass
            'color_vfr_hex': color_vfr_hex,
            'color_mvfr_hex': color_mvfr_hex,
            'color_ifr_hex': color_ifr_hex,
            'color_lifr_hex': color_lifr_hex,
            'color_nowx_hex': color_nowx_hex,
            'color_black_hex': color_black_hex,
            'color_lghtn_hex': color_lghtn_hex,
            'color_snow1_hex': color_snow1_hex,
            'color_snow2_hex': color_snow2_hex,
            'color_rain1_hex': color_rain1_hex,
            'color_rain2_hex': color_rain2_hex,
            'color_frrain1_hex': color_frrain1_hex,
            'color_frrain2_hex': color_frrain2_hex,
            'color_dustsandash1_hex': color_dustsandash1_hex,
            'color_dustsandash2_hex': color_dustsandash2_hex,
            'color_fog1_hex': color_fog1_hex,
            'color_fog2_hex': color_fog2_hex,
            'color_homeport_hex': color_homeport_hex,

            # Color Picker Variables to pass
            'fade_color1_hex': fade_color1_hex,
            'allsame_color1_hex': allsame_color1_hex,
            'allsame_color2_hex': allsame_color2_hex,
            'shuffle_color1_hex': shuffle_color1_hex,
            'shuffle_color2_hex': shuffle_color2_hex,
            'radar_color1_hex': radar_color1_hex,
            'radar_color2_hex': radar_color2_hex,
            'circle_color1_hex': circle_color1_hex,
            'circle_color2_hex': circle_color2_hex,
            'square_color1_hex': square_color1_hex,
            'square_color2_hex': square_color2_hex,
            'updn_color1_hex': updn_color1_hex,
            'updn_color2_hex': updn_color2_hex,
            'morse_color1_hex': morse_color1_hex,
            'morse_color2_hex': morse_color2_hex,
            'rabbit_color1_hex': rabbit_color1_hex,
            'rabbit_color2_hex': rabbit_color2_hex,
            'checker_color1_hex': checker_color1_hex,
            'checker_color2_hex': checker_color2_hex
            }
    return render_template('confedit.html', **templateData)


@app.route("/post", methods=["GET", "POST"])
def handle_post_request():
    """Flask Route: /post"""
    logger.info("Saving Config File")
    global ipaddresses
    global loc_timestr

    if request.method == "POST":
        data = request.form.to_dict()

        # convert hex value back to rgb string value for storage
        data["color_vfr"] = str(hex2rgb(data["color_vfr"]))
        data["color_mvfr"] = str(hex2rgb(data["color_mvfr"]))
        data["color_ifr"] = str(hex2rgb(data["color_ifr"]))
        data["color_lifr"] = str(hex2rgb(data["color_lifr"]))
        data["color_nowx"] = str(hex2rgb(data["color_nowx"]))
        data["color_black"] = str(hex2rgb(data["color_black"]))
        data["color_lghtn"] = str(hex2rgb(data["color_lghtn"]))
        data["color_snow1"] = str(hex2rgb(data["color_snow1"]))
        data["color_snow2"] = str(hex2rgb(data["color_snow2"]))
        data["color_rain1"] = str(hex2rgb(data["color_rain1"]))
        data["color_rain2"] = str(hex2rgb(data["color_rain2"]))
        data["color_frrain1"] = str(hex2rgb(data["color_frrain1"]))
        data["color_frrain2"] = str(hex2rgb(data["color_frrain2"]))
        data["color_dustsandash1"] = str(hex2rgb(data["color_dustsandash1"]))
        data["color_dustsandash2"] = str(hex2rgb(data["color_dustsandash2"]))
        data["color_fog1"] = str(hex2rgb(data["color_fog1"]))
        data["color_fog2"] = str(hex2rgb(data["color_fog2"]))
        data["color_homeport"] = str(hex2rgb(data["color_homeport"]))

        # convert hex value back to rgb string value for storage for Transitional wipes
        data["fade_color1"] = str(hex2rgb(data["fade_color1"]))
        data["allsame_color1"] = str(hex2rgb(data["allsame_color1"]))
        data["allsame_color2"] = str(hex2rgb(data["allsame_color2"]))
        data["shuffle_color1"] = str(hex2rgb(data["shuffle_color1"]))
        data["shuffle_color2"] = str(hex2rgb(data["shuffle_color2"]))
        data["radar_color1"] = str(hex2rgb(data["radar_color1"]))
        data["radar_color2"] = str(hex2rgb(data["radar_color2"]))
        data["circle_color1"] = str(hex2rgb(data["circle_color1"]))
        data["circle_color2"] = str(hex2rgb(data["circle_color2"]))
        data["square_color1"] = str(hex2rgb(data["square_color1"]))
        data["square_color2"] = str(hex2rgb(data["square_color2"]))
        data["updn_color1"] = str(hex2rgb(data["updn_color1"]))
        data["updn_color2"] = str(hex2rgb(data["updn_color2"]))
        data["morse_color1"] = str(hex2rgb(data["morse_color1"]))
        data["morse_color2"] = str(hex2rgb(data["morse_color2"]))
        data["rabbit_color1"] = str(hex2rgb(data["rabbit_color1"]))
        data["rabbit_color2"] = str(hex2rgb(data["rabbit_color2"]))
        data["checker_color1"] = str(hex2rgb(data["checker_color1"]))
        data["checker_color2"] = str(hex2rgb(data["checker_color2"]))

        # check and fix data with leading zeros.
        for key in data:
            if data[key]=='0' or data[key]=='00':
                data[key] = '0'

            elif data[key][:1] == '0':  # Check if first character is a 0. i.e. 01, 02 etc.
                data[key] = data[key].lstrip('0')  # if so, then strip the leading zero before writing to file.

        writeconf(data, settings_file)
        readconf(settings_file)
        flash('Settings Successfully Saved')

        url = request.referrer
        if url is None:
            url = 'http://' + ipadd + ':5000/index'  # Use index if called from URL and not page.

        temp = url.split('/')
        return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Routes for LSREMOTE - Allow Mobile Device Remote. Thank Lance
# @app.route('/', methods=["GET", "POST"])
@app.route('/lsremote', methods=["GET", "POST"])
def confeditmobile():
    """Flask Route: /lsremote - Mobile Device API"""
    logger.info("Opening lsremote.html")
    global ipaddresses
    global ipadd
    global loc_timestr
    global settings

    loc_now = datetime.now()
    loc_timestr = (loc_now.strftime("%H:%M:%S - %b %d, %Y"))

    logger.debug(ipadd)  # debug

    # change rgb code to hex for html color picker
    color_vfr_hex = rgb2hex(settings["color_vfr"])
    color_mvfr_hex = rgb2hex(settings["color_mvfr"])
    color_ifr_hex = rgb2hex(settings["color_ifr"])
    color_lifr_hex = rgb2hex(settings["color_lifr"])
    color_nowx_hex = rgb2hex(settings["color_nowx"])
    color_black_hex = rgb2hex(settings["color_black"])
    color_lghtn_hex = rgb2hex(settings["color_lghtn"])
    color_snow1_hex = rgb2hex(settings["color_snow1"])
    color_snow2_hex = rgb2hex(settings["color_snow2"])
    color_rain1_hex = rgb2hex(settings["color_rain1"])
    color_rain2_hex = rgb2hex(settings["color_rain2"])
    color_frrain1_hex = rgb2hex(settings["color_frrain1"])
    color_frrain2_hex = rgb2hex(settings["color_frrain2"])
    color_dustsandash1_hex = rgb2hex(settings["color_dustsandash1"])
    color_dustsandash2_hex = rgb2hex(settings["color_dustsandash2"])
    color_fog1_hex = rgb2hex(settings["color_fog1"])
    color_fog2_hex = rgb2hex(settings["color_fog2"])
    color_homeport_hex = rgb2hex(settings["color_homeport"])

    # color picker for transitional wipes
    fade_color1_hex = rgb2hex(settings["fade_color1"])
    allsame_color1_hex = rgb2hex(settings["allsame_color1"])
    allsame_color2_hex = rgb2hex(settings["allsame_color2"])
    shuffle_color1_hex = rgb2hex(settings["shuffle_color1"])
    shuffle_color2_hex = rgb2hex(settings["shuffle_color2"])
    radar_color1_hex = rgb2hex(settings["radar_color1"])
    radar_color2_hex = rgb2hex(settings["radar_color2"])
    circle_color1_hex = rgb2hex(settings["circle_color1"])
    circle_color2_hex = rgb2hex(settings["circle_color2"])
    square_color1_hex = rgb2hex(settings["square_color1"])
    square_color2_hex = rgb2hex(settings["square_color2"])
    updn_color1_hex = rgb2hex(settings["updn_color1"])
    updn_color2_hex = rgb2hex(settings["updn_color2"])
    morse_color1_hex = rgb2hex(settings["morse_color1"])
    morse_color2_hex = rgb2hex(settings["morse_color2"])
    rabbit_color1_hex = rgb2hex(settings["rabbit_color1"])
    rabbit_color2_hex = rgb2hex(settings["rabbit_color2"])
    checker_color1_hex = rgb2hex(settings["checker_color1"])
    checker_color2_hex = rgb2hex(settings["checker_color2"])

    # Pass data to html document
    templateData = {
            'title': 'Settings Editor-'+version,
            'settings': settings,
            'ipadd': ipadd,
            'ipaddresses': ipaddresses,
            'num': num,
            'timestr': loc_timestr,
            'current_timezone': current_timezone,
            'update_available': update_available,
            'update_vers': update_vers,
            'machines': machines,

            # Color Picker Variables to pass
            'color_vfr_hex': color_vfr_hex,
            'color_mvfr_hex': color_mvfr_hex,
            'color_ifr_hex': color_ifr_hex,
            'color_lifr_hex': color_lifr_hex,
            'color_nowx_hex': color_nowx_hex,
            'color_black_hex': color_black_hex,
            'color_lghtn_hex': color_lghtn_hex,
            'color_snow1_hex': color_snow1_hex,
            'color_snow2_hex': color_snow2_hex,
            'color_rain1_hex': color_rain1_hex,
            'color_rain2_hex': color_rain2_hex,
            'color_frrain1_hex': color_frrain1_hex,
            'color_frrain2_hex': color_frrain2_hex,
            'color_dustsandash1_hex': color_dustsandash1_hex,
            'color_dustsandash2_hex': color_dustsandash2_hex,
            'color_fog1_hex': color_fog1_hex,
            'color_fog2_hex': color_fog2_hex,
            'color_homeport_hex': color_homeport_hex,

            # Color Picker Variables to pass
            'fade_color1_hex': fade_color1_hex,
            'allsame_color1_hex': allsame_color1_hex,
            'allsame_color2_hex': allsame_color2_hex,
            'shuffle_color1_hex': shuffle_color1_hex,
            'shuffle_color2_hex': shuffle_color2_hex,
            'radar_color1_hex': radar_color1_hex,
            'radar_color2_hex': radar_color2_hex,
            'circle_color1_hex': circle_color1_hex,
            'circle_color2_hex': circle_color2_hex,
            'square_color1_hex': square_color1_hex,
            'square_color2_hex': square_color2_hex,
            'updn_color1_hex': updn_color1_hex,
            'updn_color2_hex': updn_color2_hex,
            'morse_color1_hex': morse_color1_hex,
            'morse_color2_hex': morse_color2_hex,
            'rabbit_color1_hex': rabbit_color1_hex,
            'rabbit_color2_hex': rabbit_color2_hex,
            'checker_color1_hex': checker_color1_hex,
            'checker_color2_hex': checker_color2_hex
            }
    return render_template('lsremote.html', **templateData)


# Import Config file. Must Save Config File to make permenant
@app.route("/importconf", methods=["GET", "POST"])
def importconf():
    """Flask Route: /importconf - Flask Config Uploader"""
    logger.info("Importing Config File")
    global ipaddresses
    global airports
    global settings
    global loc_timestr
    tmp_settings = []

    if 'file' not in request.files:
        flash('No File Selected')
        return redirect('./confedit')

    file = request.files['file']

    if file.filename == '':
        flash('No File Selected')
        return redirect('./confedit')

    filedata = file.read()
    fdata = bytes.decode(filedata)
    logger.debug(fdata)
    tmp_settings = fdata.split('\n')

    for set_line in tmp_settings:
        if set_line[0:1]=="#" or set_line[0:1]=="\n" or set_line[0:1]=="":
            pass
        else:
            (key, val) = set_line.split("=",1)
            val = val.split("#",1)
            val = val[0]
            key = key.strip()
            val = str(val.strip())
            settings[(key)] = val

    logger.debug(settings)
    flash('Config File Imported - Click "Save Config File" to save')
    return redirect('./confedit')


# Restore config.py settings
@app.route("/restoreconf", methods=["GET", "POST"])
def restoreconf():
    """Flask Route: /restoreconf"""
    logger.info("Restoring Config Settings")
    readconf(settings_file)  # read config file
    return redirect('./confedit')


# Loads the profile into the Settings Editor, but does not save it.
@app.route("/profiles", methods=["GET", "POST"])
def profiles():
    """Flask Route: /profiles - Load from Multiple Config Profiles"""
    global settings
    config_profiles = {'b1': 'config-basic.py', 'b2': 'config-basic2.py', 'b3': 'config-basic3.py', 'a1': 'config-advanced-1oled.py', 'a2': 'config-advanced-lcd.py', 'a3': 'config-advanced-8oledsrs.py', 'a4': 'config-advanced-lcdrs.py'}

    req_profile = request.form['profile']
    print(req_profile)
    print(config_profiles)
    tmp_profile = config_profiles[req_profile]
    stored_profile = '/NeoSectional/profiles/' + tmp_profile

    flash(tmp_profile + ' Profile Loaded. Review And Tweak The Settings As Desired. Must Be Saved!')
    readconf(stored_profile)    # read profile config file
    logger.info("Loading a Profile into Settings Editor")
    return redirect('confedit')


# Route for Reboot of RPI
@app.route("/reboot1", methods=["GET", "POST"])
def reboot1():
    """Flask Route: /reboot1 - Request host reboot"""
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  # Use index if called from URL and not page.

    temp = url.split('/')
#    flash("Rebooting Map ")
    logger.info("Rebooting Map from " + url)
    os.system('sudo shutdown -r now')
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Route to startup map and displays
@app.route("/startup1", methods=["GET", "POST"])
def startup1():
    """Flask Route: /startup1 - Trigger process startup"""
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  #Use index if called from URL and not page.

    temp = url.split('/')
    logger.info("Startup Map from " + url)
    os.system('sudo python3 /NeoSectional/startup.py run &')
    flash("Map Turned On ")
    time.sleep(1)
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Route to turn off the map and displays
@app.route("/shutdown1", methods=["GET", "POST"])
def shutdown1():
    """Flask Route: /shutdown1 - Trigger process shutdown"""
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index' #Use index if called from URL and not page.

    temp = url.split('/')
    logger.info("Shutoff Map from " + url)
    os.system("ps -ef | grep '/NeoSectional/metar-display-v4.py' | awk '{print $2}' | xargs sudo kill")
    os.system("ps -ef | grep '/NeoSectional/metar-v4.py' | awk '{print $2}' | xargs sudo kill")
    os.system("ps -ef | grep '/NeoSectional/check-display.py' | awk '{print $2}' | xargs sudo kill")
    os.system('sudo python3 /NeoSectional/shutoff.py &')
    flash("Map Turned Off ")
    time.sleep(1)
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Route to power down the RPI
@app.route("/shutoffnow1", methods=["GET", "POST"])
def shutoffnow1():
    """Flask Route: /shutoffnow1 - Turn Off RPI"""
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  # Use index if called from URL and not page.

    temp = url.split('/')
 #   flash("RPI is Shutting Down ")
    logger.info("Shutdown RPI from " + url)
    os.system('sudo shutdown -h now')
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Route to run LED test
@app.route("/testled", methods=["GET", "POST"])
def testled():
    """Flask Route: /testled - Run LED Test scripts"""
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index'  #Use index if called from URL and not page.

    temp = url.split('/')

#    flash("Testing LED's")
    logger.info("Running testled.py from " + url)
    os.system('sudo python3 /NeoSectional/testled.py')
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


# Route to run OLED test
@app.route("/testoled", methods=["GET", "POST"])
def testoled():
    """Flask Route: /testoled - Run OLED Test sequence"""
    url = request.referrer
    if url is None:
        url = 'http://' + ipadd + ':5000/index' # Use index if called from URL and not page.

    temp = url.split('/')
    if config.displayused!=1 or config.oledused!=1:
        return redirect(temp[3])  # temp[3] holds name of page that called this route.

#    flash("Testing OLEDs ")
    logger.info("Running testoled.py from " + url)
    os.system('sudo python3 /NeoSectional/testoled.py')
    return redirect(temp[3])  # temp[3] holds name of page that called this route.


#############
# Functions #
#############

# create backup of config.py
def copy():
    """Create copy of old configuration file"""
    logger.debug('In Copy Config file Routine')
    f = open(settings_file, "r")
    contents = f.read()
    f.close()

    f = open(settings_bkup, "w+")
    f.write(contents)
    f.close()


# open and read config.py into settings dictionary
def readconf(config_file):
    """Load old configuration file """
    logger.debug('In ReadConf Routine')
    try:
        with open(config_file) as f:
            for line in f:
                if line[0] == "#" or line[0] == "\n":
                    pass
                else:
                    (key, val) = line.split("=",1)
                    val = val.split("#",1)
                    val = val[0]
                    key = key.strip()
                    val = str(val.strip())
                    logger.debug(key + ", " + val)  # debug
                    settings[(key)] = val
            logger.debug(settings)  # debug
    except IOError as error:
        logger.error('Config file could not be loaded.')
        logger.error(error)


# write config.py file
def writeconf(loc_settings, file):
    """Save old style configuration file"""
    logger.debug('In WriteConf Routine')
    f = open(file, "w+")
    f.write('#config.py - use web based configurator to make changes unless you are comfortable doing it manually')
    f.write('\n\n')
    for key in loc_settings:
#        logger.debug(key, settings[key]) # debug
        f.write(key + " = " + loc_settings[key])
        f.write('\n')
    f.close()


# write airports file
def writeairports(loc_settings, file):
    """Save settings key data - FIXME - Why settings and not airports here"""
    logger.debug('In WriteAirports Routine')
    f = open(file, "w")  # "w+")
#       print(loc_settings)
    for key in loc_settings:
        value = loc_settings.get(key)
        logger.debug(value)  # debug
        f.write(value)
        f.write('\n')
    f.close()


# Read airports file
def readairports(filename):
    """Load airport data from airports file"""
    logger.debug('In ReadAirports Routine')
    global airports
    airports = []
    try:
        with open(filename) as f:
            for line in f:
                airports.append(line.rstrip())
            logger.debug(airports)  # debug
    except IOError as error:
        logger.error('Airports file could not be loaded.')
        logger.error(error)


# Read heat map file
def readhmdata(hmdata_file):
    """Load heatmap data from hmdata file"""
    logger.debug('In ReadHMdata Routine')
    global hmdata
    hmdata = []
    try:
        with open(hmdata_file) as f:
            for line in f:
                hmdata.append(line.rstrip())
            logger.debug(hmdata)  # debug
    except IOError as error:
        logger.error('Heat Map File Not Available. Creating Default Heat Map File')
        logger.error(error)

        for airport in airports:
            hmdata.append(airport + " 0")
        print (hmdata)  # debug
        writehmdata(hmdata, confsettings.get_string("filenames","heatmap_file"))


# Write heat map file
def writehmdata(loc_hmdata,filename):
    """Save hmdata to hmdata file"""
    logger.debug('In WriteHMdata Routine')
    f = open(filename, "w+")

    for key in loc_hmdata:
        logger.debug(key)  # debug
        f.write(key)
        f.write('\n')
    f.close()


# routine to capture airport information and pass along to web pages.
def get_led_map_info():
    """Routine to capture airport information and pass along to web pages"""
    logger.debug('In get_led_map_info Routine')

    global led_map_url
    global led_map_dict
    global lat_list
    global lon_list
    global max_lat
    global min_lat
    global max_lon
    global min_lon

    for airportcode in airports:
        led_map_url = led_map_url + airportcode + ","
    led_map_url = led_map_url[:-1]
    logger.debug(led_map_url) # debug url if neccessary

    while True:  # check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
        try:
            content = urllib.request.urlopen(led_map_url).read()
            logger.info('FAA Data Downloaded')
            logger.info(led_map_url)
            break
        except:
            logger.warning('FAA Data Not Available')
            logger.warning(led_map_url)
            time.sleep(delay_time)
            content = ''
            pass

    if content  == '':  # if FAA data not available bypass getting apinfo
        return

    root = ET.fromstring(content)  # Process XML data returned from FAA

    for led_map_info in root.iter('METAR'):
        stationId = led_map_info.find('station_id').text

        try:
            lat = led_map_info.find('latitude').text
            lon = led_map_info.find('longitude').text
        except:
            lat = '0'
            lon = '0'

        lat_list.append(lat)
        lon_list.append(lon)

        if led_map_info.find('flight_category') is None:
            fl_cat = 'Not Reported'
        else:
            fl_cat = led_map_info.find('flight_category').text
        led_map_dict[stationId] = [lat,lon,fl_cat]

    max_lat = max(lat_list)
    min_lat = min(lat_list)
    max_lon = max(lon_list)
    min_lon = min(lon_list)


# routine to capture airport information and pass along to web pages.
def get_apinfo():
    """routine to capture airport information and pass along to web pages."""
    logger.debug('In Get_Apinfo Routine')

    global orig_apurl
    global apinfo_dict

    apurl = orig_apurl  # Assign base FAA url to temp variable
    for airportcode in airports:
        apurl = apurl + airportcode + ","
    apurl = apurl[:-1]

    while True:  # check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
        try:
#            s.connect(("8.8.8.8", 80))
            content = urllib.request.urlopen(apurl).read()
            logger.info('FAA Airport Data Available')
            logger.info(apurl)
            break
        except:
            logger.warning('FAA Data Not Available')
            logger.warning(apurl)
            time.sleep(delay_time)
            content = ''
            pass

    if content  == '':  # if FAA data not available bypass getting apinfo
        return

    root = ET.fromstring(content)  # Process XML data returned from FAA

    for apinfo in root.iter('Station'):
        stationId = apinfo.find('station_id').text

        if stationId[0] != 'K':
            site = apinfo.find('site').text
            country = apinfo.find('country').text
            apinfo_dict[stationId] = [site,country]

        else:
            site = apinfo.find('site').text
            state = apinfo.find('state').text
            apinfo_dict[stationId] = [site,state]


# rgb and hex routines
def rgb2hex(rgb):
    """Convert RGB to HEX"""
    logger.debug(rgb)
    (r,g,b) = eval(rgb)
    hexval = '#%02x%02x%02x' % (r, g, b)
    return hexval


def hex2rgb(value):  # from; https://www.codespeedy.com/convert-rgb-to-hex-color-code-in-python/
    """Hex to RGB"""
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))


# functions for updating software via web
def delfile(filename):
    """Delete File""" # FIXME - Check to make sure filename is not relative
    try:
        os.remove(target_path + filename)
        logger.info('Deleted ' + filename)
    except:
        logger.error("Error while deleting file ", target_path + filename)


def unzipfile(filename):
    """Unzip file""" # FIXME - Check to make sure that filename isn't outside target_path
    with zipfile.ZipFile(target_path + filename, 'r') as zip_ref:
        zip_ref.extractall(target_path)
    logger.info('Unzipped ls.zip')


def copytoprevdir(src_dir, dest_dir):
    """Delete target; clone src""" # FIXME Error handling for rmtree
    shutil.rmtree(dest)
    shutil.copytree(src,dest)
    logger.info('Copied current version to ../previousversion')


def dlftpfile(url, filename):
    """ Download file """ # FIXME - Error handling for wget
    wget.download(url, filename)
    print('\n')
    logger.info('Downloaded ' + filename + ' from neoupdate')


def updatefiles():
    """ Deploy updates """ # FIXME - Make software update process more robust - or replace with .deb update
    copytoprevdir(src, dest)                       # This copies current version to ../previousversion before updating files.
    dlftpfile(source_path + zipfilename, target_path + zipfilename) # Download zip file that contains updated files
    unzipfile(zipfilename)                         # Unzip files and overwrite existing older files
    delfile(zipfilename)                           # Delete zip file
    logger.info('Updated New Files')


def checkforupdate():
    """ Download updates ; check for version info """
    global update_vers
#    get_loc()
#    print(loc)  # debug

    dlftpfile(source_path + verfilename, target_path + verfilename)  # download version file from neoupdate

    with open(target_path + verfilename) as file:  # Read version number of latest version
        update_vers = file.read()

    logger.info('Latest Version = ' + str(update_vers) + ' - ' + 'Current Version = ' + str(admin.version))

    delfile(verfilename)  # Delete the downloaded version file.
    logger.info('Checked for Software Update')

    if float(admin.version[1:])<float(admin.min_update_ver):  # Check to see if a newer Image is available
        return "image"

    if float(update_vers) > float(admin.version[1:]):  # Strip leading 'v' can compare as floats to determine if an update available.
        return True
    else:
        return False


def testupdate():
    """ Check to see if an newer version of the software is available, and update if user so chooses"""
    global update_available
    if checkforupdate() is True:
        logger.info('Update Available')
        update_available = 1                    # Update is available

    elif checkforupdate() is False:
        logger.info('No Updates Available')
        update_available = 0                    # No update available

    elif checkforupdate() == "image":
        logger.info('Newer Image Available for Download')
        update_available = 2                    # Newer image available


# May be used to display user location on map in user interface. - TESTING Not working consistently, not used
def get_loc():
    """ Try figure out approximate location from IP data """
    loc_data = {}
    global loc

    url_loc = 'https://extreme-ip-lookup.com/json/'
    r = requests.get(url_loc)
    data = json.loads(r.content.decode())

    ip_data = data['query']
    loc_data['city'] = data['city']
    loc_data['region'] = data['region']
    loc_data['lat'] = data['lat']
    loc_data['lon'] = data['lon']
    loc[ip_data] = loc_data


# executed code
if __name__ == '__main__':
    # Display active IP address for builder to open up web browser to configure.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    confsettings.init()

    if utils.waitForInternet():  # check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
        logger.info("Internet Available")
    else:
        logger.warning("Internet NOT Available")

    ipaddr = utils.getLocalIP()
    logger.info('Startup - Current RPI IP Address = ' + ipaddr)

    logger.info('Base Directory :' + confsettings.get_string("filenames", "basedir"))
    logger.info('Airports File  :' + confsettings.get_string("filenames", "airports_file"))

    # Get Current Time Zone
    currtzinfo = subprocess.run(['timedatectl', 'status'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    tztemp = currtzinfo.split('\n')
    current_timezone = tztemp[3]

    # Check to see if an newer version of the software is available, and update if user so chooses
    # testupdate() # temp fix for server error. More to come

    # Get system info and display
    python_ver = ("Python Version = " + sys.version)
    logger.info(python_ver)
    print()
    print(python_ver)
    print('LiveSectional Version - ' + version)
    print("\033[1;32;40m***********************************************")
    print("       My IP Address is = "+ utils.getLocalIP())
    print("***********************************************")
    print("  Configure your LiveSectional by opening a   ")
    print("    browser to http://"+ utils.getLocalIP() +":5000")
    print("***********************************************")
    print("\033[0;0m\n")
    print("Raspberry Pi System Time - " + loc_timestr)

    # Load files and back up the airports file, then run flask templates

## This code is obsolete, but left here for posperity's sake.
##    if useip2ftp ==  1:
##        exec(compile(open("/NeoSectional/ftp-v4.py", "rb").read(), "/NeoSectional/ftp-v4.py", 'exec'))  #Get latest ip's to display in editors
##        logger.info("Storing " + str(ipaddresses) + " on ftp server")

    copy()  # make backup of config file
    readconf(settings_file)  # read config file
    readairports(confsettings.get_string("filenames","airports_file"))  # read airports
    get_apinfo()  # decode airports to get city and state of each airport
    get_led_map_info() # get airport location in lat lon and flight category
    readhmdata(confsettings.get_string("filenames","heatmap_file"))  # get Heat Map data

    if admin.use_scan_network == 1:
        print("One Moment - Scanning for Other LiveSectional Maps on Local Network")
        machines = scan_network.scan_network()
        print(machines) # Debug

    logger.info("IP Address = " + utils.getLocalIP())
    logger.info("Starting Flask Session")
    app.run(debug=confsettings.get_bool("default","flask_debug"), host='0.0.0.0')
