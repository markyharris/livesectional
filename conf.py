#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Oct 28 - 2021

@author: chris.higgins@alternoc.net
"""

import re
import configparser


class Conf:
    """ Configuration Class"""

    def __init__(self):
        ''' Initialize and load configuration '''
        self.config_filename = "config.ini"
        self.configfile = configparser.ConfigParser()
        self.configfile._interpolation = configparser.ExtendedInterpolation()
        self.configfile.read(self.config_filename)

    def get(self, section, key):
        ''' Read Setting '''
        return self.configfile.get(section, key)

    def get_color(self, section, key):
        ''' Read three tuple string, Return as tuple of integers'''
        color_list = []
        tmp_string = self.configfile.get(section, key)
        # print("tmp_string:" + tmp_string + ":--")
        # color_list = tmp_string.split(',')
        color_list = re.split(r"[(),\s]\s*", tmp_string)
        # print(type(color_list))
        # print(len(color_list))
        # print("-=-=-=-=-=-=-")
        # print(color_list)
        # print("-=-=-=-=-=-=-")
        rgb_r = int(color_list[0])
        rgb_g = int(color_list[1])
        rgb_b = int(color_list[2])
        # print(rgb_r, rgb_g, rgb_b)
        # print("-=-=-=-=-=-=-")

        return tuple([rgb_r, rgb_g, rgb_b])


    def get_string(self, section, key):
        ''' Read Setting '''
        return self.configfile.get(section, key)


    def get_bool(self, section, key):
        ''' Read Setting '''
        return self.configfile.getboolean(section, key)


    def get_integer(self, section, key):
        ''' Read Setting '''
        return self.configfile.getint(section, key)


    def save_config(self):
        ''' Save configuration file '''
        cfgfile = open(self.config_filename,'w')
        self.configfile.write(cfgfile)
        cfgfile.close()
