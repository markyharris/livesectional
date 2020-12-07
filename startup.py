# startup.py v4 - by Mark Harris with contribution from Stuart.
#    Thank you for your help.
#    Used to start 3 scripts, one to run the metar leds and one to update an
#    LCD display or OLED displays. A 3rd as watchdog.
#    Taken from https://raspberrypi.stackexchange.com/questions/39108/
#    how-do-i-start-two-different-python-scripts-with-rc-local

import time
import threading
import os
import sys
import logging
import logzero                                  # had to manually install logzero. https://logzero.readthedocs.io/en/latest/
from logzero import logger
import config                                   # Config.py holds user settings used by the various scripts
import admin

# Setup rotating logfile with 3 rotations, each with a maximum filesize of 1MB:
version = admin.version                         # Software version
loglevel = config.loglevel
loglevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
logzero.loglevel(loglevels[loglevel])           # Choices in order; DEBUG, INFO, WARNING, ERROR
logzero.logfile("/NeoSectional/logfile.log", maxBytes=1e6, backupCount=3)
logger.info("\n\nStartup of startup.py Script, Version " + version)
logger.info("Log Level Set To: " + str(loglevels[loglevel]))

# Misc settings
displayused = config.displayused                # 0 = no, 1 = yes. If no, then only the metar.py script will be run. Otherwise both scripts will be threaded.
autorun = config.autorun                        # 0 = no, 1 = yes. If yes, live sectional will run on boot up. No, must run from cmd line.
title1 = "metar-v4.py"                          # define the filename for the metar.py file
prog1 = "sudo python3 /NeoSectional/metar-v4.py 2>&1 | seashells -s metar-v4"
title2 = "metar-display-v4.py"                  # define the filename for the display.py file
prog2 = "sudo python3 /NeoSectional/metar-display-v4.py 2>&1 | seashells -s metar-display-v4"
title3 = "check-display.py"                     # define the filename for the check-display.py file
prog3 = "sudo python3 /NeoSectional/check-display.py"


def startprgm(i):
    logger.info("Running thread %d" % i)
    if (i == 0):                                # Run first program prog1
        time.sleep(1)
        logger.info(title1)                     # display filename being run
        os.system(prog1)                        # execute filename
    if (i == 1) and (displayused):              # Run second program prog2 if display is  being used.
        logger.info(title2)                     # display filename being run
        time.sleep(1)
        os.system(prog2)                        # execute filename
    if (i == 2) and (displayused):              # Run second program prog3 if display is  being used (watchdog for displays).
        logger.info(title3)                     # display filename being run
        time.sleep(1)
        os.system(prog3)                        # execute filename
    pass


if len(sys.argv) > 1 or autorun == 1:
#       print (sys.argv[1] + " from cmd line") #debug
    for i in range(3):
        t = threading.Thread(target=startprgm, args=(i,))
        t.start()
