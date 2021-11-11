#!/usr/bin/env python3

# import os
# import time
import conf


def test_config_handling():
    confdata = conf.Conf()
    print("Hello World")
    print("confdata.get")
    print(confdata.get("default","welcome"))
    print("confdata.get_string")
    print(confdata.get_string("default","welcome"))
    print("confdata.get_bool : flask_debug")
    print(confdata.get_bool("default","flask_debug"))
    print("confdata.get_color_tuple")
    print(confdata.get_color("colors","color_vfr"))
    print("Generate Flask settings dict")
    print(confdata.gen_settings_dict())
    print("Testing complete")

