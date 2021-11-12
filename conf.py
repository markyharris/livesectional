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


    def set_string(self, section, key, value):
        """ Set String Value """
        self.configfile.set(section, key, value)


    def get_bool(self, section, key):
        ''' Read Setting '''
        return self.configfile.getboolean(section, key)


    def get_int(self, section, key):
        ''' Read Setting '''
        return self.configfile.getint(section, key)


    def save_config(self):
        ''' Save configuration file '''
        cfgfile = open(self.config_filename,'w')
        self.configfile.write(cfgfile)
        cfgfile.close()


    def gen_settings_dict(self):
        ''' Generate settings template to pass to flask '''
        settings = {}
        # FIXME - Change to boolean here and in HTML Templates
        settings['autorun'] = self.get_int("default", "autorun")
        settings['LED_COUNT'] = self.get_int("default", "led_count")
        # FIXME - Change to boolean here and in HTML Templates
        settings['legend'] = self.get_int("default", "legend")
        settings['max_wind_speed'] = self.get_int("metar", "max_wind_speed")
        settings['update_interval'] = self.get_int("metar", "update_interval")
        settings['metar_age'] = self.get_string("metar", "metar_age")
        settings['usetimer'] = self.get_int("schedule", "usetimer")
        settings['offhour'] = self.get_int("schedule", "offhour")
        settings['offminutes'] = self.get_int("schedule", "offminutes")
        settings['onhour'] = self.get_int("schedule", "onhour")
        settings['onminutes'] = self.get_int("schedule", "onminutes")
        settings['tempsleepon'] = self.get_int("schedule", "tempsleepon")
        settings['sleepmsg'] = self.get_int("schedule", "sleepmsg")
        settings['displayused'] = self.get_int("oled", "displayused")
        settings['oledused'] = self.get_int("oled", "oledused")
        settings['lcddisplay'] = self.get_int("oled", "lcddisplay")
        settings['numofdisplays'] = self.get_int("oled", "numofdisplays")
        settings['loglevel'] = self.get_int("default", "loglevel")
        settings['hiwindblink'] = self.get_int("lights", "hiwindblink")
        settings['lghtnflash'] = self.get_int("lights", "lghtnflash")
        settings['rainshow'] = self.get_int("lights", "rainshow")
        settings['frrainshow'] = self.get_int("lights", "frrainshow")
        settings['snowshow'] = self.get_int("lights", "snowshow")
        settings['dustsandashshow'] = self.get_int("lights", "dustsandashshow")
        settings['fogshow'] = self.get_int("lights", "fogshow")
        settings['homeport'] = self.get_int("lights", "homeport")
        settings['homeport_pin'] = self.get_int("lights", "homeport_pin")
        settings['homeport_display'] = self.get_int("lights", "homeport_display")
        settings['dim_value'] = self.get_int("lights", "dim_value")
        settings['rgb_grb'] = self.get_int("lights", "rgb_grb")
        settings['rev_rgb_grb'] = self.get_string("lights", "rev_rgb_grb")
        settings['dimmed_value'] = self.get_int("lights", "dimmed_value")
        settings['legend_hiwinds'] = self.get_int("lights", "legend_hiwinds")
        settings['legend_lghtn'] = self.get_int("lights", "legend_lghtn")
        settings['legend_snow'] = self.get_int("lights", "legend_snow")
        settings['legend_rain'] = self.get_int("lights", "legend_rain")
        settings['legend_frrain'] = self.get_int("lights", "legend_frrain")
        settings['legend_dustsandash'] = self.get_int("lights", "legend_dustsandash")
        settings['legend_fog'] = self.get_int("lights", "legend_fog")
        settings['leg_pin_vfr'] = self.get_int("lights", "leg_pin_vfr")
        settings['leg_pin_mvfr'] = self.get_int("lights", "leg_pin_mvfr")
        settings['leg_pin_ifr'] = self.get_int("lights", "leg_pin_ifr")
        settings['leg_pin_lifr'] = self.get_int("lights", "leg_pin_lifr")
        settings['leg_pin_nowx'] = self.get_int("lights", "leg_pin_nowx")
        settings['leg_pin_hiwinds'] = self.get_int("lights", "leg_pin_hiwinds")
        settings['leg_pin_lghtn'] = self.get_int("lights", "leg_pin_lghtn")
        settings['leg_pin_snow'] = self.get_int("lights", "leg_pin_snow")
        settings['leg_pin_rain'] = self.get_int("lights", "leg_pin_rain")
        settings['leg_pin_frrain'] = self.get_int("lights", "leg_pin_frrain")
        settings['leg_pin_dustsandash'] = self.get_int("lights", "leg_pin_dustsandash")
        settings['leg_pin_fog'] = self.get_int("lights", "leg_pin_fog")
        settings['num2display'] = self.get_int("lights", "num2display")
        settings['exclusive_flag'] = self.get_int("lights", "exclusive_flag")
        settings['exclusive_list'] = self.get_string("lights", "exclusive_list")
        settings['abovekts'] = self.get_int("lights", "abovekts")
        settings['lcdpause'] = self.get_string("lights", "lcdpause")
        settings['rotyesno'] = self.get_int("oled", "rotyesno")
        settings['oledposorder'] = self.get_int("oled", "oledposorder")
        settings['oledpause'] = self.get_string("oled", "oledpause")
        settings['fontsize'] = self.get_int("oled", "fontsize")
        settings['offset'] = self.get_int("oled", "offset")
        settings['wind_numorarrow'] = self.get_int("oled", "wind_numorarrow")
        settings['boldhiap'] = self.get_int("oled", "boldhiap")
        settings['blankscr'] = self.get_int("oled", "blankscr")
        settings['border'] = self.get_int("oled", "border")
        settings['dimswitch'] = self.get_int("oled", "dimswitch")
        settings['dimmin'] = self.get_int("oled", "dimmin")
        settings['dimmax'] = self.get_int("oled", "dimmax")
        settings['invert'] = self.get_int("oled", "invert")
        settings['toginv'] = self.get_int("oled", "toginv")
        settings['scrolldis'] = self.get_int("oled", "scrolldis")
        settings['usewelcome'] = self.get_int("default", "usewelcome")
        settings['welcome'] = self.get_string("default", "welcome")
        settings['displaytime'] = self.get_int("oled", "displaytime")
        settings['displayip'] = self.get_int("oled", "displayip")
        settings['data_sw0'] = self.get_int("rotaryswitch", "data_sw0")
        settings['time_sw0'] = self.get_int("rotaryswitch", "time_sw0")
        settings['data_sw1'] = self.get_int("rotaryswitch", "data_sw1")
        settings['time_sw1'] = self.get_int("rotaryswitch", "time_sw1")
        settings['data_sw2'] = self.get_int("rotaryswitch", "data_sw2")
        settings['time_sw2'] = self.get_int("rotaryswitch", "time_sw2")
        settings['data_sw3'] = self.get_int("rotaryswitch", "data_sw3")
        settings['time_sw3'] = self.get_int("rotaryswitch", "time_sw3")
        settings['data_sw4'] = self.get_int("rotaryswitch", "data_sw4")
        settings['time_sw4'] = self.get_int("rotaryswitch", "time_sw4")
        settings['data_sw5'] = self.get_int("rotaryswitch", "data_sw5")
        settings['time_sw5'] = self.get_int("rotaryswitch", "time_sw5")
        settings['data_sw6'] = self.get_int("rotaryswitch", "data_sw6")
        settings['time_sw6'] = self.get_int("rotaryswitch", "time_sw6")
        settings['data_sw7'] = self.get_int("rotaryswitch", "data_sw7")
        settings['time_sw7'] = self.get_int("rotaryswitch", "time_sw7")
        settings['data_sw8'] = self.get_int("rotaryswitch", "data_sw8")
        settings['time_sw8'] = self.get_int("rotaryswitch", "time_sw8")
        settings['data_sw9'] = self.get_int("rotaryswitch", "data_sw9")
        settings['time_sw9'] = self.get_int("rotaryswitch", "time_sw9")
        settings['data_sw10'] = self.get_int("rotaryswitch", "data_sw10")
        settings['time_sw10'] = self.get_int("rotaryswitch", "time_sw10")
        settings['data_sw11'] = self.get_int("rotaryswitch", "data_sw11")
        settings['time_sw11'] = self.get_int("rotaryswitch", "time_sw11")
        return settings

