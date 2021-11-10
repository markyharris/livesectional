#!/usr/bin/env python3

# import os
# import time
import conf


def load_config_entries():
    print("Hello World")
    print("conf.get")
    print(conf.get("default","welcome"))
    print("conf.get_string")
    print(conf.get_string("default","welcome"))
    print("conf.get_bool : flask_debug")
    print(conf.get_bool("default","flask_debug"))
    print("conf.get_color_tuple")
    print(conf.get_color("colors","color_vfr"))



if __name__ == '__main__':
    conf = conf.Conf()
    print("Testing Configuration Parsing")
    load_config_entries()
    print("Testing complete")
