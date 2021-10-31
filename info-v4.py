#!/usr/bin/python3
import sys
import socket
import subprocess
import psutil
import flask
import config
import admin
from datetime import datetime
import logging
import logzero
from logzero import logger

# Setup rotating logfile with 3 rotations, each with a maximum filesize of 1MB:
version = admin.version          #Software version
loglevel = config.loglevel
loglevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
logzero.loglevel(loglevels[loglevel]) #Choices in order; DEBUG, INFO, WARNING, ERROR
logzero.logfile("/NeoSectional/logs/logfile.log", maxBytes=1e6, backupCount=3)
logger.info("\n\nStartup of info-v4.py Script, Version " + version)
logger.info("Log Level Set To: " + str(loglevels[loglevel]))

#Misc Settings
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
now = datetime.now()
timestr = (now.strftime("%H:%M:%S - %b %d, %Y"))
mos_filepath = '/NeoSectional/data/GFSMAV'      #location of the downloaded local MOS file.

#Functions
def get_mos_date():
    #Read current MOS text file
    try:
        file = open(mos_filepath, 'r')
        lines = file.readlines()
    except IOError as error:
        logger.error('MOS data file could not be loaded.')
        logger.error(error)
        mos_date = ' No MOS Date Reported\n'
        return mos_date

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
            return mos_date


#Executed code
#Output to web page
print('<head><link rel="shortcut icon" href="static/tab.ico"></head>')
print('<div style=font-family:Courier;><h2>LiveSectional System Information - ' + timestr + '</h2>')
print('<b>Note:</b> To view the installed Libaries and their version number, select the Debug option for Logging Level in Basic Settings\n')
print('<b>LiveSectional Version = </b>' + version)
#print('My IP Address is = ' + s.getsockname()[0])
with open("/proc/device-tree/model") as f:
    for line in f:
        line = line.strip()
        print (line)
print('Python Version = ' + sys.version)
print('Flask Version = ' + flask.__version__)
print('Flask Path = ' + flask.__file__)
print('Current MOS Data ='+get_mos_date())

wifi = subprocess.run(['iwgetid', '-r'], stdout=subprocess.PIPE)
dec_wifi = wifi.stdout.decode(encoding='UTF-8')
wifi_f = subprocess.run(['iwgetid', '-f'], stdout=subprocess.PIPE)
dec_wifi_f = wifi_f.stdout.decode(encoding='UTF-8')
wifi_c = subprocess.run(['iwgetid', '-c'], stdout=subprocess.PIPE)
dec_wifi_c = wifi_c.stdout.decode(encoding='UTF-8')
print('<b>WiFi Info</b>')
print('My IP Address is = ' + s.getsockname()[0])
print('Wifi SSID = ' + dec_wifi, end="")
print('Wifi Frequency = ' + dec_wifi_f, end="")
print('Wifi Channel = ' + dec_wifi_c)

print('<b>Memory Info</b>')
mem_info = subprocess.run(['free', '-h'], stdout=subprocess.PIPE)
dec_mem_info = mem_info.stdout.decode(encoding='UTF-8')
print(dec_mem_info)

print('<b>Disk Usage</b>')
obj_Disk = psutil.disk_usage('/')
print ('Disk Total Size = ' + str("{:.2f}".format(obj_Disk.total / (1024.0 ** 3))) + ' GiB')
print ('Disk Space Used = ' + str("{:.2f}".format(obj_Disk.used / (1024.0 ** 3))) + ' GiB')
print ('Disk Space Free = ' + str("{:.2f}".format(obj_Disk.free / (1024.0 ** 3))) + ' GiB')
print ('Disk Percentage Used = ' + str("{:.2f}".format(obj_Disk.percent)) + '%')
print()


print('<b>CPU Info</b>')
cpu_temp = subprocess.run(['vcgencmd', 'measure_temp'], stdout=subprocess.PIPE)
dec_cpu_temp = cpu_temp.stdout.decode(encoding='UTF-8')
cpu_clock = subprocess.run(['vcgencmd', 'measure_clock arm'], stdout=subprocess.PIPE)
dec_cpu_clock = cpu_clock.stdout.decode(encoding='UTF-8')[:-7]
cpu_volt = subprocess.run(['vcgencmd', 'measure_volts core'], stdout=subprocess.PIPE)
dec_cpu_volt = cpu_volt.stdout.decode(encoding='UTF-8')
cpu_mem = subprocess.run(['vcgencmd', 'get_mem arm'], stdout=subprocess.PIPE)
dec_cpu_mem = cpu_mem.stdout.decode(encoding='UTF-8')
gpu_mem = subprocess.run(['vcgencmd', 'get_mem gpu'], stdout=subprocess.PIPE)
dec_gpu_mem = gpu_mem.stdout.decode(encoding='UTF-8')

print('Temperature: ' + dec_cpu_temp, end='')
print('Frequency: ' + dec_cpu_clock + 'Mhz\n', end='')
print('Core Voltage: ' + dec_cpu_volt, end='')
print('CPU Memory: ' + dec_cpu_mem, end='')
print('GPU Memory: ' + dec_gpu_mem)

print('<b>OS Info</b>')
with open("/etc/os-release") as f:
    for line in f:
        line = line.strip()
        print (line)

print()

print('<b>Raspberry Pi Information</b>')
with open("/proc/cpuinfo") as f:
    for line in f:
        line = line.strip()
        print (line)

print()

if str(loglevels[loglevel]) == '10':
    print('<b>Installed Python3 Libraries and Versions</b>')
    result = subprocess.run(['pip3', 'freeze'], stdout=subprocess.PIPE)
    dec_result = result.stdout.decode(encoding='UTF-8')
    print(dec_result)
else:
    dec_result = ''

print('</div>')

#Output to logfile.log
logger.info('LiveSectional System Information - ' + timestr)

logger.info('LiveSectional Version = ' + version)
logger.info('My IP Address is = ' + s.getsockname()[0])
with open("/proc/device-tree/model") as f:
    for line in f:
        line = line.strip()
        logger.info(line)
logger.info('Python Version = ' + sys.version)
logger.info('Flask Version = ' + flask.__version__)
logger.info('Flask Path = ' + flask.__file__)
logger.info('Current MOS Data ='+get_mos_date())

logger.info('WiFi SSID =' + dec_wifi)
logger.info('Wifi Frequency =' + dec_wifi_f)
logger.info('Wifi Channel =' + dec_wifi_c)

logger.info(dec_mem_info)

logger.info('Temperature: ' + dec_cpu_temp)
logger.info('Frequency: ' + dec_cpu_clock)
logger.info('Core Voltage: ' + dec_cpu_volt)
logger.info('CPU Memory: ' + dec_cpu_mem)
logger.info('GPU Memory: ' + dec_gpu_mem)

logger.info('OS Info')
with open("/etc/os-release") as f:
    for line in f:
        line = line.strip()
        logger.info(line)

logger.info('Raspberry Pi Information')
with open("/proc/cpuinfo") as f:
    for line in f:
        line = line.strip()
        logger.info(line)

logger.debug('Installed Python3 Libraries and Versions')
logger.debug(dec_result)


