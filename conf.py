#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Oct 28 - 2021

@author: chris.higgins@alternoc.net
"""

import re
import configparser

config_filename = "config.ini"

def init():
    ''' Initialize and load configuration '''
    global configfile
    configfile = configparser.ConfigParser()
    configfile._interpolation = configparser.ExtendedInterpolation()
    configfile.read(config_filename)

def get(section, key):
    ''' Read Setting '''
    return configfile.get(section, key)

def get_color_tuple(section, key):
    ''' Read three tuple string, Return as tuple of integers'''
    color_list = []
    tmp_string = configfile.get(section, key) 
    print("tmp_string:" + tmp_string + ":--")
    # color_list = tmp_string.split(',')
    match_pattern = '(), '
    color_list = re.split(r"[(),\s]\s*", tmp_string)
    print(type(color_list))
    print(len(color_list))
    print("-=-=-=-=-=-=-")
    print(color_list)
    print("-=-=-=-=-=-=-")
    rgb_r = int(color_list[0])
    rgb_g = int(color_list[1])
    rgb_b = int(color_list[2])
    print(rgb_r, rgb_g, rgb_b)
    print("-=-=-=-=-=-=-")

    return tuple([rgb_r, rgb_g, rgb_b])


def get_string(section, key):
    ''' Read Setting '''
    return configfile.get(section, key)


def get_bool(section, key):
    ''' Read Setting '''
    return configfile.getboolean(section, key)


def get_integer(section, key):
    ''' Read Setting '''
    return configfile.getint(section, key)


def save_config():
    ''' Save configuration file '''
    cfgfile = open(config_filename,'w')
    configfile.write(cfgfile)
    cfgfile.close()
