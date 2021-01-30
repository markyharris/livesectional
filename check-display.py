# check-display.py - v1.0 by Stuart, Thank you for your contribution to LiveSectional.
# Used to monitor if metar-v4.py is running and metar-display-v4.py is not, if so, restart the metar-display script
# or visa-versa. If one stops running, this script will start it back up.

import time
import os
import subprocess
import re
import logging
import logzero                                  #had to manually install logzero. https://logzero.readthedocs.io/en/latest/
from logzero import logger
import config                                   #config.py holds user settings used by the various scripts
import admin

# Setup rotating logfile with 3 rotations, each with a maximum filesize of 1MB:
version = admin.version                         #Software version
loglevel = config.loglevel
loglevels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR]
logzero.loglevel(loglevels[loglevel])           #Choices in order; DEBUG, INFO, WARNING, ERROR
logzero.logfile("/NeoSectional/logfile.log", maxBytes=1e6, backupCount=3)
logger.info("\n\nStartup of check-display.py Script, Version " + version)
logger.info("Log Level Set To: " + str(loglevels[loglevel]))

#misc settings
displayused = config.displayused                #0 = no, 1 = yes. If no, then only the metar.py script will be run. Otherwise both scripts will be threaded.
title1 = "metar-v4.py"                          #define the filename for the metar.py file
path1 = "/NeoSectional/metar-v4.py"
prog1 = "sudo python3 /NeoSectional/metar-v4.py"
title2 = "metar-display-v4.py"                  #define the filename for the display.py file
path2 = "/NeoSectional/metar-display-v4.py"
prog2 = "sudo python3 /NeoSectional/metar-display-v4.py"

waitsecs = 10

def findThisProcess( process_name ):
    ps     = subprocess.Popen("ps -eaf | grep "+process_name, shell=True, stdout=subprocess.PIPE)
    output = ps.stdout.read().decode('utf-8')
    ps.stdout.close()
    ps.wait()
    return output

# This is the function you can use
def isThisRunning( process_name, path_name ):
    output = findThisProcess( process_name )
    #print(output)
    #print(re.search(process_name, output))

    if re.search(path_name, output) is None:
        #print(title1 + " not in search")
        return False
    else:
        return True

# Check script status...  We'll do it every 10 seconds...
while True:
    #   first, the main LED script
    if isThisRunning(title1, path1) == False:
        ledrunning = False
        logger.debug(title1 + " Not running")

    else:
        ledrunning = True
        logger.debug(title1 + " Running!")

    if displayused == 0:
        # kill the LED process if it's not showing as running (should be a not found response, but that's ok)
        if ledrunning == False:
            logger.info(" -- killin " + title1)
            os.system("ps -ef | grep '" + path1 +"' | awk '{print $2}' | xargs sudo kill")
            time.sleep(2)
            logger.info(" -- Restarting " + title1)
            os.system(prog1)                        #execute filename


    if displayused == 1:
        #   now the display script
        if isThisRunning(title2, path2) == False:
            displayrunning = False
            logger.debug(title2 + " Not running")
        else:
            displayrunning = True
            logger.debug(title2 + " Running!")

        # kill the display process if it's not showing as running (should be a not found response, but that's ok)
        if displayrunning == False:
            logger.info(" -- killin " + title2)
            os.system("ps -ef | grep '" + path2 +"' | awk '{print $2}' | xargs sudo kill")
            time.sleep(2)

        # now restart OLEDs if the LEDs are running
        if ledrunning == True and displayrunning == False:
            logger.info(" -- Restart " + title2)
            os.system(prog2)                        #execute filename

        # now restart LEDs if the OLEDs are running
        elif ledrunning == False and displayrunning == True:
            logger.info(" -- Restart " + title1)
            os.system(prog1)                        #execute filename

        # if the LEDs and OLEDs are not running, exit the script
        elif ledrunning == False and displayrunning == False:
            logger.info('check-display.py is stopping')
            break # break out of while loop and quite script


    # now let's wait our interval seconds then start again...
    time.sleep(waitsecs)
