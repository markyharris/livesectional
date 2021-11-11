#!/usr/bin/env python3
import socket
import time
import urllib.request, urllib.error, urllib.parse
test = 1
delay_time = 1

import conf

def test_internet():

    settings = conf.Conf()

    if settings.get_bool('default', 'nightly_reboot'):
        print('Nightly Reboot Enabled')
    else:
        print('Nightly Reboot Disabled')



    #Display active IP address for builder to open up web browser to configure.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    apurl = 'https://www.aviationweather.gov/adds/dataserver_current/httpparam?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=1.5&stationString=KFLG,%20KSEZ'
    #apurl = 'http://www.livesectional.com'

    if test == 0:
        while True: #check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
            try:
                s.connect(("8.8.8.8", 80))
                print('Internet Available')
                break

            except:
                print('Internet NOT Available')
                time.sleep(delay_time)
                pass

    else:
        while True: #check internet availability and retry if necessary. If house power outage, map may boot quicker than router.
            content = urllib.request.urlopen(apurl).read()

            try:
                content = urllib.request.urlopen(apurl).read()
                print('Internet Available')
                break
            except:
                print('Internet NOT Available')
                time.sleep(delay_time)
                pass

