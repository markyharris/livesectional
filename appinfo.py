from urllib.request import urlopen
import json
from time import sleep

import confsettings

class AppInfo:
    ''' Class to store information and data about the install environment.
    Gather information about the currently installed version, and check for new versions.
    As this gets smarter - we should be able to handle 
    - Hardware Info
    - Performance Data
    - Crash Data
    - Version Information
    - Update Information
    '''
    def __init__(self):
        self.curVersionInfo =  3.0
        self.availableVersion = 3.0
        self.refresh()

    def refresh(self):
        """ Update AppInfo data """
        checkForUpdate()

    def updateAvailable():
        """ Return True if update is available """
        if self.availableVersion > self.curVersionInfo:
            return True
        return False

    def checkForUpdate():
        """ Query for new versions """


 

