#!/usr/bin/env python3

def isConnected():
    ''' Check to see if we can reach an endpoint on the Internet '''
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        sock = socket.create_connection(("www.google.com", 80))
        if sock is not None:
            print('Closing socket')
            sock.close
        return True
    except OSError:
        pass
    return False


def waitForInternet():
    ''' Delay until Internet is up (return True) - or (return False) '''
    waitCount = 0
    while True:
        if isConnected():
            return True
        waitCount += 1
        if waitCount == 6:
            return False
        sleep(30)

