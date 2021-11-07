#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Oct 28 - 2021

@author: chris.higgins@alternoc.net

Config Parser loads boolean data as case-insensitive 
Will accept any of 'yes'/'no', 'on'/'off', 'true'/'false' and '1'/'0'

"""

import configparser

config_filename = "config.ini"

def init():
    ''' Initialize and load configuration '''
    global configfile
    configfile = configparser.ConfigParser()
    configfile._interpolation = configparser.ExtendedInterpolation()
    configfile.read(config_filename)

def get(section, key):
    ''' Read [SECTION] key '''
    return configfile.get(section, key)


def get_string(section, key):
    ''' Read String Setting '''
    return configfile.get(section, key)


def get_bool(section, key):
    ''' Read Boolean Setting - Yes/Y/True/true/1'''
    return configfile.getboolean(section, key)


def get_integer(section, key):
    ''' Read Setting '''
    return configfile.getint(section, key)


def save_config():
    ''' Save configuration file '''
    cfgfile = open(config_filename,'w')
    configfile.write(cfgfile)
    cfgfile.close()
