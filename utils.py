#!/usr/bin/env python3
""" Collection of shared utility functions for all of the modules """

import os
import time
import socket
import json
import requests
import wget
import debugging

def is_connected():
    ''' Check to see if we can reach an endpoint on the Internet '''
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        sock = socket.create_connection(("www.google.com", 80))
        if sock is not None:
            print('Closing socket')
            sock.close()
        return True
    except OSError:
        pass
    return False


def wait_for_internet():
    ''' Delay until Internet is up (return True) - or (return False) '''
    wait_count = 0
    while True:
        if is_connected():
            return True
        wait_count += 1
        if wait_count == 6:
            return False
        time.sleep(30)


def get_local_ip():
    ''' Create Socket to the Internet, Query Local IP '''
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        sock = socket.create_connection(("ipv4.google.com", 80))
        if sock is not None:
            print('Closing socket')
            sock.close()
        ipaddr = sock.getsockname()[0]
        return ipaddr
    except OSError:
        pass
    return "0.0.0.0"


# May be used to display user location on map in user interface. - TESTING Not working consistently, not used
# This is not working for at least the following reasons
# 1. extreme-ip-lookup wants an API key
# 2. extreme-ip-lookup.com is on some pihole blocklists
#
# IP to Geo mapping is notoriously error prone
# Going to look at python-geoip as a data source
def get_loc():
    """ Try figure out approximate location from IP data """
    loc_data = {}
    loc = {}

    url_loc = 'https://extreme-ip-lookup.com/json/'
    geo_json_data = requests.get(url_loc)
    data = json.loads(geo_json_data.content.decode())

    ip_data = data['query']
    loc_data['city'] = data['city']
    loc_data['region'] = data['region']
    loc_data['lat'] = data['lat']
    loc_data['lon'] = data['lon']
    loc[ip_data] = loc_data


 # functions for updating software via web
def delete_file(target_path, filename):
    """Delete File""" # FIXME - Check to make sure filename is not relative
    try:
        os.remove(target_path + filename)
        debugging.info('Deleted ' + filename)
    except:
        debugging.error("Error while deleting file " + target_path + filename)


 # rgb and hex routines
def rgb2hex(rgb):
    """Convert RGB to HEX"""
    debugging.dprint(rgb)
    (r,g,b) = eval(rgb)
    hexval = '#%02x%02x%02x' % (r, g, b)
    return hexval


def hex2rgb(value):  # from; https://www.codespeedy.com/convert-rgb-to-hex-color -code-in-python/
    """Hex to RGB"""
    value = value.lstrip('#')
    length_v = len(value)
    return tuple(int(value[i:i+length_v//3], 16) for i in range(0, length_v, length_v//3))


def download_file(url, filename):
    """ Download a file """
    wget.download(url, filename)
    debugging.info('Downloaded ' + filename + ' from neoupdate')
