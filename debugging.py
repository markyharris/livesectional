''' Support Debugging Printing '''

# -*- coding: utf-8 -*-


import datetime

DEBUG_MSGS = True
INFO_MSGS = True
WARN_MSGS = True
ERR_MSGS = True


def dprint(args):
    ''' Passthrough call to print() if DEBUG_MSGS is enabled '''
    if DEBUG_MSGS:
        appname = "LIVEMAP:"
        logtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(logtime, appname, "PRINT:", args, flush=True )

def info(args):
    ''' Passthrough call to print() if DEBUG_MSGS is enabled '''
    if INFO_MSGS:
        appname = "LIVEMAP:"
        logtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(logtime, appname, "INFO:", args, flush=True )

def warn(args):
    ''' Passthrough call to print() if WARN_MSGS is enabled '''
    if WARN_MSGS:
        appname = "LIVEMAP:"
        logtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(logtime, appname, "WARN:", args, flush=True )

def error(args):
    ''' Passthrough call to print() if ERR_MSGS is enabled '''
    if ERR_MSGS:
        appname = "LIVEMAP:"
        logtime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(logtime, appname, "ERROR:", args, flush=True )
