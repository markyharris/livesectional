#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Oct 28 - 2021

@author: chris.higgins@alternoc.net
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
    ''' Read Setting '''
    return configfile.get(section, key)


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
